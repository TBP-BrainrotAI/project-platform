from core.ollama_agent import OllamaAgent
from core.gemini_agent import GeminiAgent
from core.codex_agent import CodexAgent
from core.orchestrator import Orchestrator


# ==========================================
# IA CHEFE
# ==========================================

chefe = OllamaAgent("qwen2.5")


# ==========================================
# AGENTES DISPONÍVEIS
# ==========================================

agentes = {

    "qwen": OllamaAgent("qwen2.5"),

    "llama": OllamaAgent("llama3"),

    "gemini": GeminiAgent(),

    "codex": CodexAgent()
}


# ==========================================
# ORQUESTRADOR
# ==========================================

orquestrador = Orchestrator(
    chefe=chefe,
    agentes=agentes
)


# ==========================================
# TESTE
# ==========================================

pergunta = """
Crie um programa Python que leia uma lista de números,
encontre todos os números pares, calcule a média dos
números pares e trate possíveis erros de entrada.

O programa não deve usar input() porque será executado
automaticamente em um ambiente de testes.
"""


orquestrador.executar(
    pergunta
)