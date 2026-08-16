from core.sandbox import Sandbox


sandbox = Sandbox()


# ==========================================
# TESTE 1 — CÓDIGO CORRETO
# ==========================================

codigo_correto = (
    "```python\n"
    "def soma(a, b):\n"
    "    return a + b\n"
    "\n"
    "print(soma(10, 20))\n"
    "```"
)

resultado = sandbox.executar(codigo_correto)

print("=" * 60)
print("TESTE 1 — CÓDIGO CORRETO")
print("=" * 60)

print("Sucesso:", resultado["sucesso"])
print("Saída:", resultado["stdout"])
print("Erro:", resultado["erro"])


# ==========================================
# TESTE 2 — CÓDIGO COM ERRO
# ==========================================

codigo_errado = (
    "```python\n"
    "def soma(a, b):\n"
    "    return a + b\n"
    "\n"
    "print(soma(10))\n"
    "```"
)

resultado = sandbox.executar(codigo_errado)

print()
print("=" * 60)
print("TESTE 2 — CÓDIGO COM ERRO")
print("=" * 60)

print("Sucesso:", resultado["sucesso"])
print("Saída:", resultado["stdout"])
print("Erro:", resultado["erro"])