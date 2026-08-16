import json
import re
import concurrent.futures

from core.sandbox import Sandbox


class Orchestrator:

    def __init__(
        self,
        chefe,
        agentes,
        on_event=None,
        modo="Auto (Sandbox Híbrido)"
    ):
        self.chefe = chefe
        self.agentes = agentes
        self.modo = modo
        self.sandbox = Sandbox()

        self.on_event = (
            on_event
            or (lambda tipo, dados: None)
        )

    # ==========================================
    # EVENTOS
    # ==========================================

    def _emit(self, tipo, dados):

        try:
            self.on_event(
                tipo,
                dados
            )

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
na solicitação.

PEDIDO DO USUÁRIO:

{pergunta}

========================================
AGENTES DISPONÍVEIS
========================================

qwen:
IA local através do Ollama.
Analista, programador e raciocinador geral.

gemini:
Gemini CLI.
Revisão técnica, análise e programação.

codex:
OpenAI Codex CLI.
Especialista em código, debugging e implementação.

========================================
CRITÉRIOS
========================================

Analise mentalmente se o pedido:

1. É uma pergunta conceitual sem código.

2. Pede apenas uma função simples.

3. Envolve validação de dados com regras específicas.

4. Envolve cálculo com múltiplas etapas ou algoritmo
   com várias verificações.

5. Pede para encontrar ou corrigir um bug.

6. Pede comparação entre abordagens,
   arquiteturas ou tecnologias.

7. Pede implementação de código.

8. Pede código que pode ser executado/testado.

========================================
REGRAS DE SELEÇÃO
========================================

REGRA 1:

Se for uma pergunta conceitual sem código:

use:

["qwen"]

REGRA 2:

Se for uma função simples:

use preferencialmente:

["codex"]

Não adicione outros agentes sem necessidade.

REGRA 3:

Se envolver implementação de código relevante:

use:

["codex", "qwen"]

REGRA 4:

Se envolver debugging, validação complexa,
algoritmo complexo ou necessidade de revisão técnica:

use:

["codex", "qwen", "gemini"]

REGRA 5:

Se for comparação entre abordagens:

use:

["qwen", "gemini"]

REGRA 6:

Se nenhuma regra se aplicar claramente:

use:

["qwen"]

========================================
REGRAS DO SANDBOX
========================================

Também decida se o Sandbox é realmente necessário.

"sandbox": true SOMENTE quando:

- houver código executável;
- houver implementação que realmente precise ser testada;
- houver debugging;
- houver algoritmo cuja execução ajude a validar a solução;
- houver uma razão concreta para executar o código.

"sandbox": false quando:

- for pergunta conceitual;
- for explicação;
- for comparação;
- não houver código executável;
- o código for trivial e não houver benefício relevante
  em executá-lo;
- executar o código não acrescentar informação útil.

IMPORTANTE:

Não use Sandbox apenas porque existe código.

O objetivo é ECONOMIZAR processamento.

========================================
REGRAS GERAIS
========================================

- Nunca escolha mais de 3 agentes.
- Codex é prioritário para implementação de código.
- Gemini só deve ser usado quando realmente agregar valor.
- Qwen pode funcionar como analista e sintetizador.
- Não escolha agentes desnecessariamente.
- O Sandbox deve ser usado somente quando necessário.
- A IA chefe será responsável pela síntese final.

========================================
FORMATO DA RESPOSTA
========================================

Responda SOMENTE com JSON válido.

Não escreva explicações fora do JSON.

Formato:

{{
    "agentes": ["codex", "qwen"],
    "motivo": "A solicitação envolve implementação e análise.",
    "sandbox": true
}}
"""

        resposta = self.chefe.ask(
            prompt
        )

        try:

            match = re.search(
                r'\{.*\}',
                resposta,
                re.DOTALL
            )

            if not match:

                raise ValueError(
                    "Nenhum JSON encontrado "
                    "na resposta da IA chefe."
                )

            plano = json.loads(
                match.group(0)
            )

            agentes = plano.get(
                "agentes",
                []
            )

            motivo = plano.get(
                "motivo",
                ""
            )

            usar_sandbox = plano.get(
                "sandbox",
                False
            )

            # --------------------------------------
            # VALIDAR AGENTES
            # --------------------------------------

            agentes_validos = [
                nome
                for nome in agentes
                if nome in self.agentes
            ]

            agentes_validos = agentes_validos[:3]

            # --------------------------------------
            # FALLBACK
            # --------------------------------------

            if not agentes_validos:

                agentes_validos = ["qwen"]

                motivo = (
                    "Não foi possível identificar "
                    "os agentes necessários. "
                    "Usando Qwen como fallback."
                )

                usar_sandbox = False

            # --------------------------------------
            # SANDBOX SÓ PODE SER USADO NO AUTO
            # --------------------------------------

            if self.modo != "Auto (Sandbox Híbrido)":

                usar_sandbox = False

            return {
                "agentes": agentes_validos,
                "motivo": motivo,
                "sandbox": usar_sandbox
            }

        except Exception as e:

            print(
                "[ORQUESTRADOR] "
                f"Falha ao interpretar plano: {e}"
            )

            return {
                "agentes": ["qwen"],
                "motivo": "Fallback automático.",
                "sandbox": False
            }

    # ==========================================
    # EXECUÇÃO PARALELA DOS AGENTES
    # ==========================================

    def executar_agentes(
        self,
        pergunta,
        nomes
    ):

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
                    f"   → Iniciando: "
                    f"{agente.name}"
                )

                self._emit(
                    "agente_iniciado",
                    {
                        "nome": agente.name
                    }
                )

                futuro = executor.submit(
                    agente.ask,
                    pergunta
                )

                futuros[futuro] = agente.name

            for futuro in concurrent.futures.as_completed(
                futuros
            ):

                nome = futuros[futuro]

                try:

                    resultados[nome] = (
                        futuro.result()
                    )

                    print(
                        f"   ✓ Finalizado: "
                        f"{nome}"
                    )

                    self._emit(
                        "agente_finalizado",
                        {
                            "nome": nome,
                            "sucesso": True
                        }
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
                        {
                            "nome": nome,
                            "sucesso": False
                        }
                    )

        return resultados

    # ==========================================
    # EXTRAÇÃO DE CÓDIGO
    # ==========================================

    def extrair_codigos(
        self,
        resultados
    ):

        codigos = []

        for nome, resposta in resultados.items():

            if not resposta:
                continue

            blocos = re.findall(
                r"```(?:python|py)?\s*\n(.*?)```",
                resposta,
                re.DOTALL | re.IGNORECASE
            )

            for indice, codigo in enumerate(
                blocos,
                start=1
            ):

                codigo = codigo.strip()

                if codigo:

                    codigos.append(
                        {
                            "agente": nome,
                            "indice": indice,
                            "codigo": codigo
                        }
                    )

        return codigos

    # ==========================================
    # TESTE DOS CÓDIGOS NO SANDBOX
    # ==========================================

    def testar_codigos(
        self,
        resultados
    ):

        codigos = self.extrair_codigos(
            resultados
        )

        if not codigos:

            print(
                "\n🧪 SANDBOX: "
                "Nenhum código encontrado."
            )

            return []

        print(
            f"\n🧪 SANDBOX: "
            f"{len(codigos)} bloco(s) "
            f"de código encontrado(s)."
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

                resultados_sandbox.append(
                    {
                        "agente": item["agente"],
                        "indice": item["indice"],
                        "sucesso": sucesso,
                        "stdout": stdout,
                        "erro": erro
                    }
                )

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
                    f"   ✗ Falha ao executar Sandbox: "
                    f"{e}"
                )

                resultados_sandbox.append(
                    {
                        "agente": item["agente"],
                        "indice": item["indice"],
                        "sucesso": False,
                        "stdout": "",
                        "erro": str(e)
                    }
                )

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
    # FORMATAR SANDBOX
    # ==========================================

    def formatar_sandbox(
        self,
        resultados_sandbox
    ):

        if not resultados_sandbox:

            return (
                "Nenhum código foi "
                "executado no Sandbox."
            )

        partes = []

        for resultado in resultados_sandbox:

            status = (
                "SUCESSO"
                if resultado["sucesso"]
                else "ERRO"
            )

            texto = (
                f"Agente: "
                f"{resultado['agente']}\n"
                f"Bloco: "
                f"{resultado['indice']}\n"
                f"Status: "
                f"{status}\n"
                f"Saída:\n"
                f"{resultado['stdout']}\n"
                f"Erro:\n"
                f"{resultado['erro']}"
            )

            partes.append(
                texto
            )

        return "\n\n".join(
            partes
        )

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
            for nome, resposta
            in resultados.items()
        )

        sandbox_texto = (
            self.formatar_sandbox(
                resultados_sandbox
            )
        )

        prompt = f"""
Você é a IA CHEFE do BrainRotAI.

Você recebeu:

1. A solicitação original do usuário.
2. Relatórios dos agentes selecionados.
3. Resultados do Sandbox, quando houver.

========================================
PEDIDO ORIGINAL
========================================

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
e produza uma única resposta final de
alta qualidade.

REGRAS:

- Não copie cegamente os relatórios.
- Verifique inconsistências.
- Considere os resultados do Sandbox.
- Se um código apresentar erro no Sandbox,
  corrija-o antes de entregá-lo.
- Não entregue código que você sabe que falhou.
- Se necessário, explique o erro encontrado.
- Não mencione os agentes desnecessariamente.
- Não diga que você consultou outras IAs.
- Não invente informações.
- Preserve código correto.
- Se houver código, entregue código funcional.
- Responda diretamente ao usuário.

IMPORTANTE:

Quando houver resultado do Sandbox,
ele tem prioridade sobre uma afirmação
de que determinado código funciona.
"""

        return self.chefe.ask(
            prompt
        )

    # ==========================================
    # EXECUÇÃO COMPLETA
    # ==========================================

    def executar(
        self,
        pergunta
    ):

        print()

        print(
            "=" * 60
        )

        print(
            "🧠 BRAINROTAI — ORQUESTRAÇÃO"
        )

        print(
            "=" * 60
        )

        # ==========================================
        # IA CHEFE
        # ==========================================

        print(
            f"\n👑 IA CHEFE: "
            f"{self.chefe.name}"
        )

        print(
            f"⚙️ MODO: "
            f"{self.modo}"
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

        print(
            "Sandbox: "
            f"{'SIM' if plano['sandbox'] else 'NÃO'}"
        )

        self._emit(
            "plano_pronto",
            {
                "agentes": plano["agentes"],
                "motivo": plano["motivo"],
                "sandbox": plano["sandbox"]
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

            print(
                "=" * 60
            )

            print(
                f"🔹 RELATÓRIO: "
                f"{nome}"
            )

            print(
                "=" * 60
            )

            print(
                resultado
            )

        # ==========================================
        # SANDBOX
        # ==========================================

        resultados_sandbox = []

        usar_sandbox = (
            self.modo
            == "Auto (Sandbox Híbrido)"
            and plano.get(
                "sandbox",
                False
            )
        )

        if usar_sandbox:

            print(
                "\n🧪 SANDBOX: "
                "Validação necessária."
            )

            resultados_sandbox = (
                self.testar_codigos(
                    resultados
                )
            )

        else:

            print(
                "\n🧪 SANDBOX: "
                "Não necessário para esta tarefa."
            )

        # ==========================================
        # RESULTADOS DO SANDBOX
        # ==========================================

        if resultados_sandbox:

            print()

            print(
                "=" * 60
            )

            print(
                "🧪 RESULTADOS DO SANDBOX"
            )

            print(
                "=" * 60
            )

            for resultado in resultados_sandbox:

                status = (
                    "✅ SUCESSO"
                    if resultado["sucesso"]
                    else "❌ ERRO"
                )

                print(
                    f"\n{status} | "
                    f"{resultado['agente']} | "
                    f"Bloco "
                    f"{resultado['indice']}"
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
            "OS RELATÓRIOS"
            + (
                " E TESTES..."
                if resultados_sandbox
                else "..."
            )
        )

        self._emit(
            "sintese_iniciada",
            {}
        )

        resposta_final = self.sintetizar(
            pergunta,
            resultados,
            resultados_sandbox
        )

        # ==========================================
        # RESPOSTA FINAL
        # ==========================================

        print()

        print(
            "=" * 60
        )

        print(
            "🤖 RESPOSTA FINAL"
        )

        print(
            "=" * 60
        )

        print(
            resposta_final
        )

        print()

        self._emit(
            "resposta_final",
            {
                "resposta": resposta_final
            }
        )

        return resposta_final