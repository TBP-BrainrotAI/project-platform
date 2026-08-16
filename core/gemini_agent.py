import subprocess
from .agent import Agent


class GeminiAgent(Agent):

    def __init__(self):
        super().__init__("Gemini CLI")

    def ask(self, prompt):
        try:
            resultado = subprocess.run(
                [
                    "gemini.cmd",
                    "-p",
                    prompt
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120
            )

            stdout = resultado.stdout.strip()
            stderr = resultado.stderr.strip()

            saida_completa = f"{stdout}\n{stderr}".lower()

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
                    "[GEMINI INDISPONÍVEL] Limite diário de "
                    "requisições do Gemini CLI foi atingido. "
                    "Tente novamente mais tarde ou configure "
                    "billing para aumentar a quota."
                )

            if resultado.returncode != 0:
                return (
                    "[ERRO GEMINI CLI]\n"
                    + stderr
                )

            return stdout

        except subprocess.TimeoutExpired:
            return "[ERRO GEMINI CLI] Timeout."

        except Exception as e:
            self.available = False
            return f"[ERRO GEMINI CLI] {e}"