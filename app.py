import customtkinter as ctk
import threading
import requests
import subprocess
import os

from core.orchestrator import Orchestrator
from core.codex_agent import CodexAgent


# ============================================================
# CONFIGURAÇÃO
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/chat"


PALETAS = {

    "Dark": {

        "fundo": "#1A1B26",
        "painel": "#24283B",
        "chat": "#16161E",
        "texto": "#C0CAF5",
        "destaque": "#7AA2F7",
        "pensamento": "#565F89",
        "sucesso": "#9ECE6A",
        "alerta": "#E0AF68",
        "erro": "#FF5555"
    },

    "Light": {

        "fundo": "#F0F0F0",
        "painel": "#E0E0E0",
        "chat": "#FFFFFF",
        "texto": "#333333",
        "destaque": "#3B82F6",
        "pensamento": "#8C8C8C",
        "sucesso": "#10B981",
        "alerta": "#F59E0B",
        "erro": "#EF4444"
    }
}


# ============================================================
# AGENTE BASE
# ============================================================

class Agente:

    def __init__(self, name):

        self.name = name

    def ask(self, prompt):

        raise NotImplementedError


# ============================================================
# AGENTE OLLAMA
# ============================================================

class OllamaAgent(Agente):

    def __init__(self, model):

        super().__init__(model)

        self.model = model

    def ask(self, prompt):

        sistema = (
            "Você é um agente do BrainRotAI. "
            "Responda em português do Brasil. "
            "Se houver código, entregue código funcional. "
            "Se estiver analisando código, procure erros cuidadosamente."
        )

        try:

            resposta = requests.post(

                OLLAMA_URL,

                json={

                    "model": self.model,

                    "messages": [

                        {
                            "role": "system",
                            "content": sistema
                        },

                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    "stream": False,

                    "options": {

                        "temperature": 0.1,
                        "num_predict": 2000
                    }
                },

                timeout=180
            )

            resposta.raise_for_status()

            dados = resposta.json()

            return (
                dados
                .get("message", {})
                .get("content", "")
                .strip()
            )

        except requests.exceptions.ConnectionError:

            return (
                "ERRO_CONEXAO_OLLAMA: "
                "Não foi possível conectar ao Ollama. "
                "Verifique se o Ollama está executando."
            )

        except Exception as e:

            return f"ERRO_OLLAMA: {e}"


# ============================================================
# GEMINI CLI
# ============================================================

class GeminiAgent(Agente):

    def __init__(self):

        super().__init__("Gemini CLI")

    def ask(self, prompt):

        try:

            comando = [

                "cmd.exe",
                "/c",
                "gemini.cmd",
                "-p",
                prompt
            ]

            ambiente = os.environ.copy()

            resultado = subprocess.run(

                comando,

                capture_output=True,

                text=True,

                encoding="utf-8",

                errors="replace",

                timeout=300,

                cwd=os.getcwd(),

                env=ambiente
            )

            stdout = resultado.stdout.strip()

            stderr = resultado.stderr.strip()

            saida_completa = (
                f"{stdout}\n{stderr}"
            ).lower()

            indicadores_quota = [

                "quota",
                "429",
                "resource_exhausted",
                "terminalquotaerror",
                "rate limit"
            ]

            if any(
                indicador in saida_completa
                for indicador in indicadores_quota
            ):

                return (
                    "[GEMINI INDISPONÍVEL] "
                    "Limite diário de requisições "
                    "do Gemini CLI foi atingido."
                )

            if stdout:

                return stdout

            if stderr:

                return (
                    "[Gemini CLI não retornou "
                    "resposta no stdout]\n"
                    f"{stderr}"
                )

            return (
                "[Gemini CLI retornou "
                "resposta vazia.]"
            )

        except subprocess.TimeoutExpired:

            return (
                "[ERRO GEMINI] "
                "Tempo limite excedido."
            )

        except FileNotFoundError:

            return (
                "[ERRO GEMINI] gemini.cmd "
                "não encontrado. "
                "Verifique se o Gemini CLI "
                "está instalado."
            )

        except Exception as e:

            return f"[ERRO GEMINI] {e}"


# ============================================================
# INTERFACE
# ============================================================

class BrainRotApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            "BrainRotAI - Orquestrador com CLI Integration"
        )

        self.geometry(
            "1250x900"
        )

        self.tema_atual = "Dark"

        self.cards_agentes = {}

        # ====================================================
        # GRID PRINCIPAL
        # ====================================================

        self.grid_rowconfigure(
            0,
            weight=1
        )

        self.grid_columnconfigure(
            1,
            weight=1
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.menu_lateral = ctk.CTkFrame(

            self,

            width=310,

            corner_radius=0
        )

        self.menu_lateral.grid(

            row=0,

            column=0,

            sticky="nsew"
        )

        # ====================================================
        # LOGO
        # ====================================================

        try:

            from PIL import Image

            imagem = Image.open(
                "logo.jpg"
            )

            imagem_ctk = ctk.CTkImage(

                light_image=imagem,

                dark_image=imagem,

                size=(70, 70)
            )

            ctk.CTkLabel(

                self.menu_lateral,

                image=imagem_ctk,

                text=""
            ).pack(

                pady=(20, 5)
            )

        except Exception:

            pass

        # ====================================================
        # TITULO
        # ====================================================

        ctk.CTkLabel(

            self.menu_lateral,

            text="BrainRotAI",

            font=(
                "Segoe UI",
                20,
                "bold"
            )

        ).pack(
            pady=(0, 10)
        )

        # ====================================================
        # IA CHEFE
        # ====================================================

        ctk.CTkLabel(

            self.menu_lateral,

            text="👑 ESCOLHER IA CHEFE (LOCAL)",

            font=(
                "Segoe UI",
                11,
                "bold"
            )

        ).pack(
            pady=(5, 2)
        )

        self.seletor_chefe = ctk.CTkOptionMenu(

            self.menu_lateral,

            values=[
                "Qwen 2.5",
                "Llama 3"
            ]
        )

        self.seletor_chefe.pack(

            padx=15,

            pady=5
        )

        self.seletor_chefe.set(
            "Qwen 2.5"
        )

        # ====================================================
        # TEMA
        # ====================================================

        ctk.CTkLabel(

            self.menu_lateral,

            text="🎨 TEMA DA INTERFACE",

            font=(
                "Segoe UI",
                11,
                "bold"
            )

        ).pack(
            pady=(20, 2)
        )

        self.seletor_tema = ctk.CTkOptionMenu(

            self.menu_lateral,

            values=[
                "Dark",
                "Light"
            ],

            command=self.mudar_tema
        )

        self.seletor_tema.pack(

            padx=15,

            pady=5
        )

        self.seletor_tema.set(
            "Dark"
        )

        # ====================================================
        # CONTAS CODEX
        # ====================================================

        ctk.CTkLabel(

            self.menu_lateral,

            text="🧑‍💻 CONTA CODEX",

            font=(
                "Segoe UI",
                11,
                "bold"
            )

        ).pack(
            pady=(20, 2)
        )

        contas_iniciais = (
            self.obter_contas_validas()
        )

        self.seletor_conta = ctk.CTkOptionMenu(

            self.menu_lateral,

            values=contas_iniciais
        )

        self.seletor_conta.pack(

            padx=15,

            pady=5
        )

        self.seletor_conta.set(
            contas_iniciais[0]
        )

        # ====================================================
        # NOVA CONTA
        # ====================================================

        self.btn_nova_conta = ctk.CTkButton(

            self.menu_lateral,

            text="➕ Nova Conta / Login",

            command=self.nova_conta_login
        )

        self.btn_nova_conta.pack(

            padx=15,

            pady=(5, 20)
        )

        # ====================================================
        # ÁREA PRINCIPAL
        # ====================================================

        self.area_principal = ctk.CTkFrame(

            self,

            fg_color="transparent"
        )

        self.area_principal.grid(

            row=0,

            column=1,

            sticky="nsew",

            padx=20,

            pady=20
        )

        self.area_principal.grid_rowconfigure(

            2,

            weight=1
        )

        self.area_principal.grid_columnconfigure(

            0,

            weight=1
        )

        # ====================================================
        # TOP BAR
        # ====================================================

        self.top_bar = ctk.CTkFrame(

            self.area_principal,

            height=50
        )

        self.top_bar.grid(

            row=0,

            column=0,

            sticky="ew",

            pady=(0, 10)
        )

        self.modo_op = ctk.CTkSegmentedButton(

            self.top_bar,

            values=[

                "Manual",
                "Semi-Auto",
                "Auto (Sandbox Híbrido)"
            ],

            command=self.ao_mudar_modo
        )

        self.modo_op.pack(

            side="left",

            padx=15,

            pady=10
        )

        self.modo_op.set(
            "Manual"
        )

        # ====================================================
        # PAINEL PROCESSAMENTO
        # ====================================================

        self.painel_processamento = ctk.CTkFrame(

            self.area_principal,

            corner_radius=10
        )

        self.painel_processamento.grid(

            row=1,

            column=0,

            sticky="ew",

            pady=(0, 10)
        )

        self.frame_conteudo_painel = ctk.CTkFrame(

            self.painel_processamento,

            fg_color="transparent"
        )

        self.frame_conteudo_painel.pack(

            fill="x",

            expand=True
        )

        self.mostrar_placeholder_painel(

            "Modo Manual: resposta direta "
            "da IA chefe, sem orquestração."
        )

        # ====================================================
        # CHAT
        # ====================================================

        self.chat_area = ctk.CTkTextbox(

            self.area_principal,

            font=(
                "Segoe UI",
                14
            ),

            wrap="word"
        )

        self.chat_area.grid(

            row=2,

            column=0,

            sticky="nsew",

            pady=(0, 15)
        )

        self.chat_area.configure(
            state="disabled"
        )

        # ====================================================
        # ENTRADA
        # ====================================================

        self.entrada = ctk.CTkEntry(

            self.area_principal,

            placeholder_text=(
                "Envie seu comando, código "
                "ou dúvida..."
            ),

            height=50
        )

        self.entrada.grid(

            row=3,

            column=0,

            sticky="ew",

            padx=(0, 10)
        )

        self.entrada.bind(
            "<Return>",
            self.enviar
        )

        # ====================================================
        # BOTÃO
        # ====================================================

        self.btn_enviar = ctk.CTkButton(

            self.area_principal,

            text="EXECUTAR 🚀",

            width=130,

            height=50,

            command=self.enviar
        )

        self.btn_enviar.grid(

            row=3,

            column=1
        )

        # ====================================================
        # TEMA
        # ====================================================

        self.mudar_tema(
            "Dark"
        )

    # ========================================================
    # CONTAS CODEX
    # ========================================================

    def obter_contas_validas(self):

        try:

            contas = (
                CodexAgent.detectar_contas()
            )

            if not contas:

                return [
                    "Nenhuma conta"
                ]

            return contas

        except Exception as e:

            print(
                "[BrainRotAI] "
                f"Erro detectando contas Codex: {e}"
            )

            return [
                "Nenhuma conta"
            ]

    # ========================================================

    def atualizar_dropdown(
        self,
        nome_novo=None
    ):

        contas = (
            self.obter_contas_validas()
        )

        self.seletor_conta.configure(
            values=contas
        )

        if (
            nome_novo
            and nome_novo in contas
        ):

            self.seletor_conta.set(
                nome_novo
            )

        elif contas:

            self.seletor_conta.set(
                contas[0]
            )

    # ========================================================

    def nova_conta_login(self):

        dialog = ctk.CTkInputDialog(

            text=(
                "Digite o nome da nova conta:"
            ),

            title="Gerenciador de Login"
        )

        nome = dialog.get_input()

        if not nome:
            return

        nome = nome.strip()

        if not nome:
            return

        contas_existentes = (
            CodexAgent.detectar_contas()
        )

        if nome in contas_existentes:

            self.escrever_chat(

                f"⚠️ A conta '{nome}' "
                f"já está conectada.\n\n",

                "alerta"
            )

            self.seletor_conta.set(
                nome
            )

            return

        self.escrever_chat(

            f"🔄 Iniciando login para "
            f"a conta '{nome}'...\n"
            f"🌐 Complete a autenticação "
            f"no navegador.\n\n",

            "alerta"
        )

        self.btn_nova_conta.configure(
            state="disabled"
        )

        def realizar_login():

            agente = None

            try:

                agente = (
                    CodexAgent.criar_nova_conta(
                        nome
                    )
                )

                resultado = agente.login()

                if resultado.get(
                    "sucesso"
                ):

                    self.escrever_chat(

                        f"✅ Conta '{nome}' "
                        f"conectada com sucesso!\n\n",

                        "sucesso"
                    )

                    self.after(

                        0,

                        lambda:
                        self.atualizar_dropdown(
                            nome
                        )
                    )

                else:

                    mensagem = (
                        resultado.get(
                            "mensagem",
                            "O login não foi concluído."
                        )
                    )

                    self.escrever_chat(

                        f"❌ Não foi possível "
                        f"conectar a conta '{nome}'.\n\n"
                        f"{mensagem}\n\n",

                        "erro"
                    )

                    if agente:

                        agente.remover_conta()

                    self.after(
                        0,
                        self.atualizar_dropdown
                    )

            except Exception as e:

                self.escrever_chat(

                    f"❌ Erro ao criar/login "
                    f"da conta '{nome}':\n"
                    f"{e}\n\n",

                    "erro"
                )

                if agente:

                    try:

                        agente.remover_conta()

                    except Exception:

                        pass

                self.after(
                    0,
                    self.atualizar_dropdown
                )

            finally:

                self.after(

                    0,

                    lambda:
                    self.btn_nova_conta.configure(
                        state="normal"
                    )
                )

        threading.Thread(

            target=realizar_login,

            daemon=True

        ).start()

    # ========================================================
    # TEMA
    # ========================================================

    def mudar_tema(
        self,
        tema
    ):

        self.tema_atual = tema

        ctk.set_appearance_mode(
            tema
        )

        cor = PALETAS[
            tema
        ]

        self.configure(
            fg_color=cor["fundo"]
        )

        self.menu_lateral.configure(
            fg_color=cor["painel"]
        )

        self.painel_processamento.configure(
            fg_color=cor["painel"]
        )

        self.chat_area.configure(

            fg_color=cor["chat"],

            text_color=cor["texto"]
        )

        self.entrada.configure(

            fg_color=cor["chat"],

            text_color=cor["texto"]
        )

        self.btn_enviar.configure(

            fg_color=cor["destaque"]
        )

        self.chat_area.tag_config(

            "usuario",

            foreground=cor["destaque"]
        )

        self.chat_area.tag_config(

            "pensamento",

            foreground=cor["pensamento"]
        )

        self.chat_area.tag_config(

            "sucesso",

            foreground=cor["sucesso"]
        )

        self.chat_area.tag_config(

            "alerta",

            foreground=cor["alerta"]
        )

        self.chat_area.tag_config(

            "erro",

            foreground=cor["erro"]
        )

    # ========================================================
    # PAINEL
    # ========================================================

    def limpar_painel_processamento(self):

        for widget in (
            self.frame_conteudo_painel
            .winfo_children()
        ):

            widget.destroy()

        self.cards_agentes = {}

    # ========================================================

    def mostrar_placeholder_painel(
        self,
        texto
    ):

        self.limpar_painel_processamento()

        ctk.CTkLabel(

            self.frame_conteudo_painel,

            text=texto,

            font=(
                "Segoe UI",
                12
            ),

            text_color=(
                PALETAS[
                    self.tema_atual
                ]["pensamento"]
            ),

            justify="left",

            anchor="w"

        ).pack(

            fill="x",

            padx=12,

            pady=12
        )

    # ========================================================

    def preparar_painel_execucao(self):

        self.limpar_painel_processamento()

        self.lbl_plano = ctk.CTkLabel(

            self.frame_conteudo_painel,

            text="📋 Planejando...",

            font=(
                "Segoe UI",
                12
            ),

            justify="left",

            anchor="w"
        )

        self.lbl_plano.pack(

            fill="x",

            padx=12,

            pady=(10, 6)
        )

        self.frame_agentes_row = ctk.CTkFrame(

            self.frame_conteudo_painel,

            fg_color="transparent"
        )

        self.frame_agentes_row.pack(

            fill="x",

            padx=8,

            pady=4
        )

        self.frame_sandbox_row = ctk.CTkFrame(

            self.frame_conteudo_painel,

            fg_color="transparent"
        )

        self.frame_sandbox_row.pack(

            fill="x",

            padx=8,

            pady=(4, 10)
        )

    # ========================================================

    def criar_ou_atualizar_card_agente(

        self,
        nome,
        status_texto,
        cor
    ):

        if nome not in self.cards_agentes:

            card = ctk.CTkFrame(

                self.frame_agentes_row,

                corner_radius=8
            )

            card.pack(

                side="left",

                padx=6,

                pady=4
            )

            ctk.CTkLabel(

                card,

                text=nome,

                font=(
                    "Segoe UI",
                    12,
                    "bold"
                )

            ).pack(

                padx=12,

                pady=(8, 2)
            )

            lbl_status = ctk.CTkLabel(

                card,

                text=status_texto,

                font=(
                    "Segoe UI",
                    11
                ),

                text_color=cor
            )

            lbl_status.pack(

                padx=12,

                pady=(0, 8)
            )

            self.cards_agentes[
                nome
            ] = {

                "card": card,

                "lbl_status":
                    lbl_status
            }

        else:

            self.cards_agentes[
                nome
            ][
                "lbl_status"
            ].configure(

                text=status_texto,

                text_color=cor
            )

    # ========================================================

    def adicionar_item_sandbox(

        self,
        agente,
        indice,
        sucesso
    ):

        cor = (

            PALETAS[
                self.tema_atual
            ]["sucesso"]

            if sucesso

            else

            PALETAS[
                self.tema_atual
            ]["erro"]
        )

        simbolo = (
            "✓"
            if sucesso
            else
            "✗"
        )

        ctk.CTkLabel(

            self.frame_sandbox_row,

            text=(
                f"{simbolo} "
                f"{agente} · "
                f"bloco {indice}"
            ),

            font=(
                "Segoe UI",
                11
            ),

            text_color=cor

        ).pack(

            side="left",

            padx=6,

            pady=2
        )

    # ========================================================
    # EVENTOS ORQUESTRADOR
    # ========================================================

    def processar_evento_ui(

        self,
        tipo,
        dados
    ):

        if tipo == "plano_pronto":

            self.preparar_painel_execucao()

            agentes_txt = ", ".join(
                dados.get(
                    "agentes",
                    []
                )
            )

            sandbox = dados.get(
                "sandbox",
                False
            )

            self.lbl_plano.configure(

                text=(

                    f"📋 Agentes selecionados: "
                    f"{agentes_txt}\n"

                    f"{dados.get('motivo', '')}\n"

                    f"🧪 Sandbox: "
                    f"{'ATIVADO' if sandbox else 'DESATIVADO'}"
                )
            )

            return

        if tipo == "agente_iniciado":

            self.criar_ou_atualizar_card_agente(

                dados.get(
                    "nome",
                    ""
                ),

                "⏳ Processando...",

                PALETAS[
                    self.tema_atual
                ]["destaque"]
            )

            return

        if tipo == "agente_finalizado":

            sucesso = dados.get(
                "sucesso",
                True
            )

            self.criar_ou_atualizar_card_agente(

                dados.get(
                    "nome",
                    ""
                ),

                (
                    "✅ Concluído"
                    if sucesso
                    else
                    "❌ Erro"
                ),

                (
                    PALETAS[
                        self.tema_atual
                    ]["sucesso"]

                    if sucesso

                    else

                    PALETAS[
                        self.tema_atual
                    ]["erro"]
                )
            )

            return

        if tipo == "sandbox_resultado":

            item = dados.get(
                "item",
                {}
            )

            self.adicionar_item_sandbox(

                item.get(
                    "agente",
                    ""
                ),

                item.get(
                    "indice",
                    0
                ),

                item.get(
                    "sucesso",
                    False
                )
            )

            return

        if tipo == "sintese_iniciada":

            if hasattr(
                self,
                "lbl_plano"
            ):

                texto_atual = (
                    self.lbl_plano.cget(
                        "text"
                    )
                )

                if (
                    "Sintetizando"
                    not in texto_atual
                ):

                    self.lbl_plano.configure(

                        text=(

                            texto_atual
                            + "\n🧠 "
                            "Sintetizando "
                            "resposta final..."
                        )
                    )

            return

    # ========================================================

    def ao_evento_orquestrador(

        self,
        tipo,
        dados
    ):

        self.after(

            0,

            lambda t=tipo, d=dados:
            self.processar_evento_ui(
                t,
                d
            )
        )

    # ========================================================
    # CHAT
    # ========================================================

    def escrever_chat(

        self,
        texto,
        tag=None
    ):

        def inserir():

            self.chat_area.configure(
                state="normal"
            )

            if tag:

                self.chat_area.insert(

                    "end",

                    texto,

                    tag
                )

            else:

                self.chat_area.insert(

                    "end",

                    texto
                )

            self.chat_area.yview(
                "end"
            )

            self.chat_area.configure(
                state="disabled"
            )

        self.after(
            0,
            inserir
        )

    # ========================================================
    # MODO
    # ========================================================

    def ao_mudar_modo(

        self,
        novo_modo
    ):

        self.chat_area.configure(
            state="normal"
        )

        self.chat_area.delete(
            "1.0",
            "end"
        )

        self.chat_area.insert(

            "end",

            f"🔄 MODO ALTERADO PARA: "
            f"{novo_modo.upper()}\n\n",

            "alerta"
        )

        descricoes = {

            "Manual":

                "Chat direto com a IA chefe local.",

            "Semi-Auto":

                "A IA chefe seleciona somente "
                "os agentes necessários. "
                "Não utiliza Sandbox.",

            "Auto (Sandbox Híbrido)":

                "Orquestração completa. "
                "Os agentes trabalham em paralelo "
                "e o Sandbox só é utilizado quando "
                "a IA chefe determinar que a validação "
                "realmente é necessária."
        }

        self.chat_area.insert(

            "end",

            descricoes.get(
                novo_modo,
                ""
            ),

            "pensamento"
        )

        self.chat_area.insert(
            "end",
            "\n\n"
        )

        self.chat_area.configure(
            state="disabled"
        )

        if novo_modo == "Manual":

            self.mostrar_placeholder_painel(

                "Modo Manual: resposta direta "
                "da IA chefe, sem orquestração."
            )

        else:

            self.mostrar_placeholder_painel(

                "Envie uma mensagem para iniciar "
                "a orquestração."
            )

    # ========================================================
    # CRIAÇÃO DOS AGENTES
    # ========================================================

    def criar_agentes(self):

        chefe_nome = (
            self.seletor_chefe.get()
        )

        if "Qwen" in chefe_nome:

            chefe = OllamaAgent(
                "qwen2.5"
            )

        else:

            chefe = OllamaAgent(
                "llama3"
            )

        qwen = OllamaAgent(
            "qwen2.5"
        )

        llama = OllamaAgent(
            "llama3"
        )

        gemini = GeminiAgent()

        nome_conta = (
            self.seletor_conta.get()
        )

        if (
            nome_conta
            == "Nenhuma conta"
        ):

            raise RuntimeError(

                "Nenhuma conta Codex "
                "está conectada. "
                "Faça login em uma conta "
                "antes de utilizar o Codex."
            )

        codex = CodexAgent(

            nome_conta=nome_conta
        )

        agentes = {

            "qwen": qwen,

            "llama": llama,

            "gemini": gemini,

            "codex": codex
        }

        return chefe, agentes

    # ========================================================
    # ORQUESTRADOR
    # ========================================================

    def executar_orquestrador(

        self,
        pergunta
    ):

        try:

            chefe, agentes = (
                self.criar_agentes()
            )

            modo_atual = (
                self.modo_op.get()
            )

            orchestrator = Orchestrator(

                chefe,

                agentes,

                on_event=(
                    self.ao_evento_orquestrador
                ),

                modo=modo_atual
            )

            resposta = (
                orchestrator.executar(
                    pergunta
                )
            )

            self.escrever_chat(

                "\n🤖 RESPOSTA FINAL:\n",

                "sucesso"
            )

            self.escrever_chat(
                resposta
            )

            self.escrever_chat(
                "\n\n"
            )

        except Exception as e:

            self.escrever_chat(

                "\n❌ ERRO NO ORQUESTRADOR:\n",

                "erro"
            )

            self.escrever_chat(
                str(e)
            )

            self.escrever_chat(
                "\n\n"
            )

        finally:

            self.after(

                0,

                lambda:
                self.btn_enviar.configure(
                    state="normal"
                )
            )

    # ========================================================
    # ENVIAR
    # ========================================================

    def enviar(

        self,
        event=None
    ):

        mensagem = (
            self.entrada.get()
        )

        if not mensagem.strip():

            return

        self.escrever_chat(

            "━" * 60 + "\n\n",

            "pensamento"
        )

        self.escrever_chat(

            f"👤 VOCÊ:\n"
            f"{mensagem}\n\n",

            "usuario"
        )

        self.entrada.delete(
            0,
            "end"
        )

        self.btn_enviar.configure(
            state="disabled"
        )

        modo = (
            self.modo_op.get()
        )

        # ====================================================
        # MANUAL
        # ====================================================

        if modo == "Manual":

            self.mostrar_placeholder_painel(

                "Modo Manual: resposta direta "
                "da IA chefe, sem orquestração."
            )

            def manual():

                try:

                    chefe, _ = (
                        self.criar_agentes()
                    )

                    self.escrever_chat(

                        f"🤖 RESPOSTA DIRETA "
                        f"({chefe.name}):\n",

                        "sucesso"
                    )

                    resposta = chefe.ask(
                        mensagem
                    )

                    self.escrever_chat(
                        resposta
                    )

                    self.escrever_chat(
                        "\n\n"
                    )

                except Exception as e:

                    self.escrever_chat(

                        f"❌ ERRO: {e}\n",

                        "erro"
                    )

                finally:

                    self.after(

                        0,

                        lambda:
                        self.btn_enviar.configure(
                            state="normal"
                        )
                    )

            threading.Thread(

                target=manual,

                daemon=True

            ).start()

            return

        # ====================================================
        # ORQUESTRAÇÃO
        # ====================================================

        self.mostrar_placeholder_painel(

            "🧠 IA chefe analisando a tarefa..."
        )

        threading.Thread(

            target=self.executar_orquestrador,

            args=(
                mensagem,
            ),

            daemon=True

        ).start()


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app = BrainRotApp()

    app.mainloop()