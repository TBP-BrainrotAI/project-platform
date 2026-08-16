import os
import subprocess
import shutil

from core.agent import Agent


# ============================================================
# CODEX CLI
# MÚLTIPLAS CONTAS + ISOLAMENTO TOTAL
# ============================================================

class CodexAgent(Agent):

    # ========================================================
    # CONFIGURAÇÃO
    # ========================================================

    def __init__(self, nome_conta="Padrao"):

        super().__init__(
            f"Codex CLI ({nome_conta})"
        )

        self.nome_conta = nome_conta

        # ----------------------------------------------------
        # DIRETÓRIO BASE DA CONTA
        # ----------------------------------------------------

        self.pasta_conta = os.path.join(
            os.getcwd(),
            "workspace",
            "contas",
            self.nome_conta
        )

        # ----------------------------------------------------
        # CODEX_HOME
        #
        # Cada conta possui seu próprio:
        #
        # workspace/
        #   contas/
        #       conta2/
        #           .codex/
        #               auth.json
        #
        #       contateste/
        #           .codex/
        #               auth.json
        # ----------------------------------------------------

        self.codex_home = os.path.join(
            self.pasta_conta,
            ".codex"
        )

        # ----------------------------------------------------
        # APPDATA ISOLADO
        # ----------------------------------------------------

        self.pasta_appdata = os.path.join(
            self.pasta_conta,
            "AppData",
            "Roaming"
        )

        self.pasta_localappdata = os.path.join(
            self.pasta_conta,
            "AppData",
            "Local"
        )

        # ----------------------------------------------------
        # CRIA DIRETÓRIOS
        # ----------------------------------------------------

        os.makedirs(
            self.pasta_conta,
            exist_ok=True
        )

        os.makedirs(
            self.codex_home,
            exist_ok=True
        )

        os.makedirs(
            self.pasta_appdata,
            exist_ok=True
        )

        os.makedirs(
            self.pasta_localappdata,
            exist_ok=True
        )

    # ========================================================
    # AMBIENTE ISOLADO
    # ========================================================

    def obter_ambiente_isolado(self):

        ambiente = os.environ.copy()

        # ----------------------------------------------------
        # ISOLAMENTO DO USUÁRIO
        # ----------------------------------------------------

        ambiente["USERPROFILE"] = self.pasta_conta
        ambiente["HOME"] = self.pasta_conta
        ambiente["HOMEPATH"] = self.pasta_conta

        # ----------------------------------------------------
        # ISOLAMENTO WINDOWS
        # ----------------------------------------------------

        ambiente["APPDATA"] = self.pasta_appdata
        ambiente["LOCALAPPDATA"] = self.pasta_localappdata

        # ----------------------------------------------------
        # ISOLAMENTO CODEX
        #
        # ESTE É O MAIS IMPORTANTE.
        # ----------------------------------------------------

        ambiente["CODEX_HOME"] = self.codex_home

        return ambiente

    # ========================================================
    # CAMINHO DO AUTH.JSON
    # ========================================================

    def caminho_auth(self):

        return os.path.join(
            self.codex_home,
            "auth.json"
        )

    # ========================================================
    # VERIFICAR AUTENTICAÇÃO
    # ========================================================

    def esta_autenticada(self):

        return os.path.isfile(
            self.caminho_auth()
        )

    # ========================================================
    # STATUS DA CONTA
    # ========================================================

    def obter_status(self):

        if self.esta_autenticada():

            return {
                "nome": self.nome_conta,
                "autenticada": True,
                "status": "🟢 Autenticada",
                "pasta": self.pasta_conta,
                "codex_home": self.codex_home
            }

        return {
            "nome": self.nome_conta,
            "autenticada": False,
            "status": "🔴 Não autenticada",
            "pasta": self.pasta_conta,
            "codex_home": self.codex_home
        }

    # ========================================================
    # EXECUTAR CODEX
    # ========================================================

    def ask(self, prompt):

        try:

            # ------------------------------------------------
            # GARANTE QUE A CONTA ESTÁ AUTENTICADA
            # ------------------------------------------------

            if not self.esta_autenticada():

                return (
                    f"[CODEX - {self.nome_conta}] "
                    f"Esta conta não está autenticada."
                )

            # ------------------------------------------------
            # COMANDO
            # ------------------------------------------------

            comando = [
                "cmd.exe",
                "/c",
                "codex.cmd",
                "exec",
                "--skip-git-repo-check",
                prompt
            ]

            # ------------------------------------------------
            # EXECUÇÃO ISOLADA
            # ------------------------------------------------

            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                cwd=os.getcwd(),
                env=self.obter_ambiente_isolado()
            )

            stdout = resultado.stdout.strip()
            stderr = resultado.stderr.strip()

            saida_completa = (
                f"{stdout}\n{stderr}"
            ).lower()

            # ------------------------------------------------
            # DETECÇÃO DE QUOTA
            # ------------------------------------------------

            indicadores_limite = [
                "quota",
                "429",
                "rate limit",
                "resource_exhausted",
                "insufficient_quota",
                "usage limit",
                "limit reached"
            ]

            if any(
                indicador in saida_completa
                for indicador in indicadores_limite
            ):

                return (
                    f"[CODEX INDISPONÍVEL - {self.nome_conta}] "
                    f"O limite de uso desta conta foi atingido."
                )

            # ------------------------------------------------
            # DETECÇÃO DE AUTENTICAÇÃO
            # ------------------------------------------------

            indicadores_auth = [
                "401 unauthorized",
                "unauthorized",
                "missing bearer",
                "authentication",
                "not authenticated"
            ]

            if any(
                indicador in saida_completa
                for indicador in indicadores_auth
            ):

                return (
                    f"[CODEX NÃO AUTENTICADO - "
                    f"{self.nome_conta}] "
                    f"A autenticação desta conta não está válida."
                )

            # ------------------------------------------------
            # RESPOSTA NORMAL
            # ------------------------------------------------

            if stdout:

                return stdout

            # ------------------------------------------------
            # ERRO
            # ------------------------------------------------

            if stderr:

                return (
                    f"[CODEX - {self.nome_conta}] "
                    f"O Codex não retornou resposta no stdout.\n"
                    f"{stderr}"
                )

            return (
                f"[CODEX - {self.nome_conta}] "
                f"Resposta vazia."
            )

        # ----------------------------------------------------
        # TIMEOUT
        # ----------------------------------------------------

        except subprocess.TimeoutExpired:

            return (
                f"[ERRO CODEX - {self.nome_conta}] "
                f"Tempo limite de execução excedido."
            )

        # ----------------------------------------------------
        # CODEX NÃO INSTALADO
        # ----------------------------------------------------

        except FileNotFoundError:

            return (
                f"[ERRO CODEX - {self.nome_conta}] "
                f"codex.cmd não encontrado. "
                f"Verifique se o Codex CLI está instalado."
            )

        # ----------------------------------------------------
        # ERRO GENÉRICO
        # ----------------------------------------------------

        except Exception as e:

            return (
                f"[ERRO CODEX - {self.nome_conta}] "
                f"{e}"
            )

    # ========================================================
    # DETECTAR CONTAS AUTENTICADAS
    # ========================================================

    @staticmethod
    def detectar_contas():

        pasta_base = os.path.join(
            os.getcwd(),
            "workspace",
            "contas"
        )

        os.makedirs(
            pasta_base,
            exist_ok=True
        )

        contas = []

        # ----------------------------------------------------
        # PERCORRE AS CONTAS
        # ----------------------------------------------------

        try:

            nomes = os.listdir(
                pasta_base
            )

        except OSError:

            return []

        for nome in nomes:

            pasta = os.path.join(
                pasta_base,
                nome
            )

            if not os.path.isdir(pasta):
                continue

            # ------------------------------------------------
            # NOVA ESTRUTURA:
            #
            # conta/.codex/auth.json
            # ------------------------------------------------

            auth_direto = os.path.join(
                pasta,
                ".codex",
                "auth.json"
            )

            if os.path.isfile(auth_direto):

                contas.append(nome)

                continue

            # ------------------------------------------------
            # COMPATIBILIDADE COM ESTRUTURA ANTIGA
            #
            # Procura auth.json dentro da conta.
            # ------------------------------------------------

            encontrou_auth = False

            for root, dirs, files in os.walk(pasta):

                # Não precisamos entrar em diretórios enormes
                # de AppData/npm etc. para procurar infinitamente.

                dirs[:] = [
                    d for d in dirs
                    if d not in {
                        "node_modules",
                        "__pycache__"
                    }
                ]

                if "auth.json" in files:

                    encontrou_auth = True
                    break

            if encontrou_auth:

                contas.append(nome)

        return sorted(
            set(contas),
            key=str.lower
        )

    # ========================================================
    # DETECTAR TODAS AS CONTAS
    #
    # Inclui contas ainda não autenticadas.
    # Útil para gerenciamento da interface.
    # ========================================================

    @staticmethod
    def detectar_todas_contas():

        pasta_base = os.path.join(
            os.getcwd(),
            "workspace",
            "contas"
        )

        os.makedirs(
            pasta_base,
            exist_ok=True
        )

        contas = []

        try:

            nomes = os.listdir(
                pasta_base
            )

        except OSError:

            return []

        for nome in nomes:

            pasta = os.path.join(
                pasta_base,
                nome
            )

            if os.path.isdir(pasta):

                contas.append(nome)

        return sorted(
            contas,
            key=str.lower
        )

    # ========================================================
    # OBTER STATUS DE TODAS AS CONTAS
    # ========================================================

    @staticmethod
    def status_todas_contas():

        contas = CodexAgent.detectar_todas_contas()

        resultado = []

        for nome in contas:

            agente = CodexAgent(
                nome
            )

            resultado.append(
                agente.obter_status()
            )

        return resultado

    # ========================================================
    # CRIAR NOVA CONTA
    # ========================================================

    @staticmethod
    def criar_nova_conta(nome):

        nome = nome.strip()

        if not nome:

            raise ValueError(
                "O nome da conta não pode estar vazio."
            )

        # ----------------------------------------------------
        # Impede caracteres problemáticos no nome da pasta
        # ----------------------------------------------------

        caracteres_invalidos = [
            "\\",
            "/",
            ":",
            "*",
            "?",
            '"',
            "<",
            ">",
            "|"
        ]

        if any(
            caractere in nome
            for caractere in caracteres_invalidos
        ):

            raise ValueError(
                "O nome da conta contém caracteres inválidos."
            )

        # ----------------------------------------------------
        # Não permitir nomes reservados
        # ----------------------------------------------------

        if nome in {
            ".",
            ".."
        }:

            raise ValueError(
                "Nome de conta inválido."
            )

        # ----------------------------------------------------
        # Verifica duplicidade
        # ----------------------------------------------------

        contas = CodexAgent.detectar_todas_contas()

        if nome in contas:

            raise ValueError(
                f"A conta '{nome}' já existe."
            )

        # ----------------------------------------------------
        # Cria o agente
        # ----------------------------------------------------

        agente = CodexAgent(
            nome
        )

        return agente

    # ========================================================
    # LOGIN
    # ========================================================

    def login(self):

        try:

            # ------------------------------------------------
            # Cria ambiente isolado
            # ------------------------------------------------

            ambiente = self.obter_ambiente_isolado()

            # ------------------------------------------------
            # IMPORTANTE:
            #
            # O login será executado dentro do CODEX_HOME
            # desta conta.
            # ------------------------------------------------

            comando = [
                "cmd.exe",
                "/c",
                "codex.cmd",
                "login"
            ]

            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
                cwd=os.getcwd(),
                env=ambiente
            )

            stdout = resultado.stdout.strip()
            stderr = resultado.stderr.strip()

            saida = (
                f"{stdout}\n{stderr}"
            ).strip()

            # ------------------------------------------------
            # Verifica se auth.json apareceu
            # ------------------------------------------------

            if self.esta_autenticada():

                return {
                    "sucesso": True,
                    "mensagem": (
                        f"Conta '{self.nome_conta}' "
                        f"autenticada com sucesso."
                    ),
                    "saida": saida
                }

            # ------------------------------------------------
            # Falha
            # ------------------------------------------------

            return {
                "sucesso": False,
                "mensagem": (
                    "O processo de login terminou, "
                    "mas o auth.json não foi encontrado "
                    "no CODEX_HOME da conta."
                ),
                "saida": saida
            }

        except subprocess.TimeoutExpired:

            return {
                "sucesso": False,
                "mensagem": (
                    "Tempo limite do login excedido."
                ),
                "saida": ""
            }

        except FileNotFoundError:

            return {
                "sucesso": False,
                "mensagem": (
                    "codex.cmd não foi encontrado."
                ),
                "saida": ""
            }

        except Exception as e:

            return {
                "sucesso": False,
                "mensagem": str(e),
                "saida": ""
            }

    # ========================================================
    # REMOVER CONTA
    # ========================================================

    def remover_conta(self):

        if not os.path.exists(
            self.pasta_conta
        ):

            return False

        try:

            shutil.rmtree(
                self.pasta_conta
            )

            return True

        except Exception:

            return False

    # ========================================================
    # REMOVER CONTA PELO NOME
    # ========================================================

    @staticmethod
    def remover_conta_por_nome(nome):

        agente = CodexAgent(
            nome
        )

        return agente.remover_conta()

    # ========================================================
    # VERIFICAR SE A CONTA EXISTE
    # ========================================================

    @staticmethod
    def conta_existe(nome):

        return nome in (
            CodexAgent.detectar_todas_contas()
        )