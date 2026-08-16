import json
import re
import concurrent.futures

from core.sandbox import Sandbox


class Orchestrator:

    def __init__(self, chefe, agentes, on_event=None):
        self.chefe = chefe
        self.agentes = agentes
        self.sandbox = Sandbox()
        self.on_event = on_event or (lambda tipo, dados: None)

    # ==========================================
    # EVENTOS (para a interface gráfica acompanhar
    # o processamento em tempo real, sem afetar
    # quem usa o orquestrador só pelo terminal)
    # ==========================================

    def _emit(self, tipo, dados):

        try:
            self.on_event(tipo, dados)
        except Exception:
            pass

    # ==========================================
    # PLANEJAMENTO
    # ==========================================

    def criar_plano(self, pergunta):

        prompt = f"""
Você é o ORQUESTRADOR PRINCIPAL do BrainRotAI.

Você NÃO deve resolver o problema.
Sua função é decidir quais agentes devem trabalhar
na solicitação, aplicando regras OBJETIVAS abaixo.

PEDIDO DO USUÁRIO:
{pergunta}

AGENTES DISPONÍVEIS:

qwen:
IA local através do Ollama.
Analista, programador e raciocinador geral.

gemini:
Gemini CLI.
Revisão técnica, análise e programação.

codex:
OpenAI Codex CLI.
Especialista em código, debugging e implementação.

CRITÉRIOS OBJETIVOS (marque mentalmente cada um que se aplica
ao pedido do usuário):

[ ] Pede apenas 1 função simples, sem validação de regras externas
    (ex: soma, média, conversão de unidade, string simples)
[ ] Envolve validação de dados com regras específicas
    (ex: CPF, CNPJ, e-mail, senha, cartão de crédito)
[ ] Envolve cálculo com múltiplas etapas ou algoritmo com mais
    de uma verificação encadeada (ex: dígitos verificadores,
    checksum, criptografia, parsing, recursão)
[ ] Pede para encontrar ou corrigir um bug em código existente
[ ] Pede comparação entre abordagens, arquiteturas ou tecnologias
[ ] É uma pergunta conceitual, sem pedir código

REGRAS DE SELEÇÃO (aplique a PRIMEIRA regra que combinar,
na ordem abaixo):

1. Se marcou "pergunta conceitual, sem código":
   use ["qwen"]

2. Se marcou "1 função simples" E NENHUM outro item:
   use ["codex", "qwen"]

3. Se marcou "validação de dados com regras específicas",
   OU "múltiplas etapas/algoritmo encadeado",
   OU "encontrar/corrigir bug":
   use ["codex", "qwen", "gemini"]

4. Se marcou "comparação entre abordagens":
   use ["qwen", "gemini"]

5. Se nenhuma regra acima combinar claramente:
   use ["codex", "qwen"]

REGRAS GERAIS:

- Nunca escolha mais de 3 agentes.
- Codex é sempre prioritário quando há geração de código.
- Gemini deve ser incluído sempre que a regra 3 ou 4 se aplicar.
- A IA chefe é responsável pela síntese final.

RESPONDA SOMENTE COM JSON VÁLIDO, sem explicações fora do JSON.

Formato obrigatório:

{{
    "agentes": ["qwen", "codex"],
    "motivo": "A solicitação envolve programação e precisa de implementação e análise."
}}
"""

        resposta = self.chefe.ask(prompt)

        try:

            match = re.search(
                r'\{.*\}',
                resposta,
                re.DOTALL
            )

            if not match:
                raise ValueError(
                    "Nenhum JSON encontrado na resposta da IA chefe."
                )

            plano = json.loads(match.group(0))

            agentes = plano.get("agentes", [])
            motivo = plano.get("motivo", "")

            agentes_validos = [
                nome
                for nome in agentes
                if nome in self.agentes
            ]

            agentes_validos = agentes_validos[:3]

            if not agentes_validos:

                agentes_validos = ["qwen"]

                motivo = (
                    "Não foi possível identificar os agentes "
                    "necessários. Usando Qwen como fallback."
                )

            return {
                "agentes": agentes_validos,
                "motivo": motivo
            }

        except Exception as e:

            print(
                f"[ORQUESTRADOR] Falha ao interpretar plano: {e}"
            )

            return {
                "agentes": ["qwen"],
                "motivo": "Fallback automático."
            }

    # ==========================================
    # EXECUÇÃO PARALELA DOS AGENTES
    # ==========================================

    def executar_agentes(self, pergunta, nomes):

        resultados = {}

        selecionados = [
            self.agentes[nome]
            for nome in nomes
            if nome in self.agentes
        ]

        if not selecionados:
            return resultados

        print(
            f"\n⚡ Executando "
            f"{len(selecionados)} agente(s) em paralelo..."
        )

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(selecionados)
        ) as executor:

            futuros = {}

            for agente in selecionados:

                print(
                    f"   → Iniciando: {agente.name}"
                )

                self._emit(
                    "agente_iniciado",
                    {"nome": agente.name}
                )

                futuro = executor.submit(
                    agente.ask,
                    pergunta
                )

                futuros[futuro] = agente.name

            for futuro in concurrent.futures.as_completed(futuros):

                nome = futuros[futuro]

                try:

                    resultados[nome] = futuro.result()

                    print(
                        f"   ✓ Finalizado: {nome}"
                    )

                    self._emit(
                        "agente_finalizado",
                        {"nome": nome, "sucesso": True}
                    )

                except Exception as e:

                    resultados[nome] = (
                        f"[ERRO {nome}] {e}"
                    )

                    print(
                        f"   ✗ Erro: {nome}"
                    )

                    self._emit(
                        "agente_finalizado",
                        {"nome": nome, "sucesso": False}
                    )

        return resultados

    # ==========================================
    # EXTRAÇÃO DE CÓDIGO
    # ==========================================

    def extrair_codigos(self, resultados):

        codigos = []

        for nome, resposta in resultados.items():

            if not resposta:
                continue

            blocos = re.findall(
                r"```(?:python|py)?\s*\n(.*?)```",
                resposta,
                re.DOTALL | re.IGNORECASE
            )

            for indice, codigo in enumerate(blocos, start=1):

                codigo = codigo.strip()

                if codigo:

                    codigos.append({
                        "agente": nome,
                        "indice": indice,
                        "codigo": codigo
                    })

        return codigos

    # ==========================================
    # TESTE DOS CÓDIGOS NO SANDBOX
    # ==========================================

    def testar_codigos(self, resultados):

        codigos = self.extrair_codigos(resultados)

        if not codigos:

            print(
                "\n🧪 SANDBOX: Nenhum código encontrado."
            )

            return []

        print(
            f"\n🧪 SANDBOX: "
            f"{len(codigos)} bloco(s) de código encontrado(s)."
        )

        resultados_sandbox = []

        for item in codigos:

            print(
                f"   → Testando código de "
                f"{item['agente']} "
                f"(bloco {item['indice']})..."
            )

            try:

                resultado = self.sandbox.executar(
                    item["codigo"]
                )

                sucesso = resultado.get(
                    "sucesso",
                    False
                )

                stdout = resultado.get(
                    "stdout",
                    ""
                )

                erro = resultado.get(
                    "erro",
                    ""
                )

                if sucesso:

                    print(
                        f"   ✓ Código de "
                        f"{item['agente']} funcionou."
                    )

                else:

                    print(
                        f"   ✗ Código de "
                        f"{item['agente']} apresentou erro."
                    )

                resultados_sandbox.append({
                    "agente": item["agente"],
                    "indice": item["indice"],
                    "sucesso": sucesso,
                    "stdout": stdout,
                    "erro": erro
                })

                self._emit(
                    "sandbox_resultado",
                    {
                        "item": {
                            "agente": item["agente"],
                            "indice": item["indice"],
                            "sucesso": sucesso
                        }
                    }
                )

            except Exception as e:

                print(
                    f"   ✗ Falha ao executar Sandbox: {e}"
                )

                resultados_sandbox.append({
                    "agente": item["agente"],
                    "indice": item["indice"],
                    "sucesso": False,
                    "stdout": "",
                    "erro": str(e)
                })

                self._emit(
                    "sandbox_resultado",
                    {
                        "item": {
                            "agente": item["agente"],
                            "indice": item["indice"],
                            "sucesso": False
                        }
                    }
                )

        return resultados_sandbox

    # ==========================================
    # FORMATAR RESULTADOS DO SANDBOX
    # ==========================================

    def formatar_sandbox(self, resultados_sandbox):

        if not resultados_sandbox:

            return "Nenhum código foi executado no Sandbox."

        partes = []

        for resultado in resultados_sandbox:

            status = (
                "SUCESSO"
                if resultado["sucesso"]
                else "ERRO"
            )

            texto = (
                f"Agente: {resultado['agente']}\n"
                f"Bloco: {resultado['indice']}\n"
                f"Status: {status}\n"
                f"Saída:\n{resultado['stdout']}\n"
                f"Erro:\n{resultado['erro']}"
            )

            partes.append(texto)

        return "\n\n".join(partes)

    # ==========================================
    # SÍNTESE FINAL
    # ==========================================

    def sintetizar(
        self,
        pergunta,
        resultados,
        resultados_sandbox
    ):

        relatorios = "\n\n".join(
            f"### RELATÓRIO DO AGENTE: {nome}\n"
            f"{resposta}"
            for nome, resposta in resultados.items()
        )

        sandbox_texto = self.formatar_sandbox(
            resultados_sandbox
        )

        prompt = f"""
Você é a IA CHEFE do BrainRotAI.

Você recebeu uma solicitação do usuário,
relatórios de outros agentes e resultados
de execução no Sandbox.

PEDIDO ORIGINAL:

{pergunta}

========================================
RELATÓRIOS DOS AGENTES
========================================

{relatorios}

========================================
RESULTADOS DO SANDBOX
========================================

{sandbox_texto}

========================================
SUA FUNÇÃO
========================================

Analise criticamente todas as informações
e produza uma única resposta final de alta qualidade.

REGRAS:

- Não copie cegamente os relatórios.
- Verifique inconsistências.
- Considere os resultados do Sandbox.
- Se um código apresentar erro no Sandbox,
  corrija-o antes de entregá-lo.
- Não entregue código que você sabe que falhou.
- Se necessário, explique o erro encontrado.
- Não mencione os agentes desnecessariamente.
- Não diga que você "consultou outras IAs".
- Não invente informações.
- Preserve código correto.
- Se houver código, entregue código funcional.
- Responda diretamente ao usuário.

IMPORTANTE:

O resultado do Sandbox tem prioridade sobre
uma afirmação de que determinado código funciona.
"""

        return self.chefe.ask(prompt)

    # ==========================================
    # EXECUÇÃO COMPLETA
    # ==========================================

    def executar(self, pergunta):

        print()
        print("=" * 60)
        print("🧠 BRAINROTAI — ORQUESTRAÇÃO")
        print("=" * 60)

        # ==========================================
        # IA CHEFE
        # ==========================================

        print(
            f"\n👑 IA CHEFE: "
            f"{self.chefe.name}"
        )

        # ==========================================
        # PLANEJAMENTO
        # ==========================================

        print(
            "\n🧠 IA CHEFE ANALISANDO A TAREFA..."
        )

        plano = self.criar_plano(
            pergunta
        )

        print(
            "\n📋 PLANO:"
        )

        print(
            f"Agentes: "
            f"{', '.join(plano['agentes'])}"
        )

        print(
            f"Motivo: "
            f"{plano['motivo']}"
        )

        self._emit(
            "plano_pronto",
            {
                "agentes": plano["agentes"],
                "motivo": plano["motivo"]
            }
        )

        # ==========================================
        # EXECUÇÃO DOS AGENTES
        # ==========================================

        print(
            "\n⚡ EXECUTANDO AGENTES..."
        )

        resultados = self.executar_agentes(
            pergunta,
            plano["agentes"]
        )

        # ==========================================
        # RELATÓRIOS
        # ==========================================

        print()

        for nome, resultado in resultados.items():

            print("=" * 60)

            print(
                f"🔹 RELATÓRIO: {nome}"
            )

            print("=" * 60)

            print(
                resultado
            )

        # ==========================================
        # SANDBOX
        # ==========================================

        resultados_sandbox = self.testar_codigos(
            resultados
        )

        # ==========================================
        # RESULTADOS DO SANDBOX
        # ==========================================

        if resultados_sandbox:

            print()
            print("=" * 60)
            print("🧪 RESULTADOS DO SANDBOX")
            print("=" * 60)

            for resultado in resultados_sandbox:

                status = (
                    "✅ SUCESSO"
                    if resultado["sucesso"]
                    else "❌ ERRO"
                )

                print(
                    f"\n{status} | "
                    f"{resultado['agente']} | "
                    f"Bloco {resultado['indice']}"
                )

                if resultado["stdout"]:

                    print(
                        f"Saída:\n"
                        f"{resultado['stdout']}"
                    )

                if resultado["erro"]:

                    print(
                        f"Erro:\n"
                        f"{resultado['erro']}"
                    )

        # ==========================================
        # SÍNTESE
        # ==========================================

        print(
            "\n🧠 IA CHEFE SINTETIZANDO "
            "OS RELATÓRIOS E TESTES..."
        )

        self._emit("sintese_iniciada", {})

        resposta_final = self.sintetizar(
            pergunta,
            resultados,
            resultados_sandbox
        )

        # ==========================================
        # RESPOSTA FINAL
        # ==========================================

        print()
        print("=" * 60)
        print("🤖 RESPOSTA FINAL")
        print("=" * 60)

        print(
            resposta_final
        )

        print()

        self._emit(
            "resposta_final",
            {"resposta": resposta_final}
        )

        return resposta_final