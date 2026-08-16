from core.ollama_agent import OllamaAgent
from core.gemini_agent import GeminiAgent
from core.codex_agent import CodexAgent


def testar(nome, agente):
    print("=" * 60)
    print(f"TESTANDO: {nome}")
    print("=" * 60)

    resposta = agente.ask(
        "Responda apenas com o seu nome."
    )

    print(resposta)
    print()


# ==========================
# AGENTES LOCAIS
# ==========================

qwen = OllamaAgent("qwen2.5")
llama = OllamaAgent("llama3")


# ==========================
# AGENTES CLI
# ==========================

gemini = GeminiAgent()
codex = CodexAgent()


# ==========================
# TESTES
# ==========================

testar("Qwen 2.5", qwen)
testar("Llama 3", llama)
testar("Gemini CLI", gemini)
testar("Codex CLI", codex)