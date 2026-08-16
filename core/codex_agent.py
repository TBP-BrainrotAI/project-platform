import subprocess
from .agent import Agent


class CodexAgent(Agent):

    def __init__(self):
        super().__init__("Codex CLI")

    def ask(self, prompt):

        try:
            resultado = subprocess.run(
                [
                    "codex.cmd",
                    "exec",
                    "--skip-git-repo-check",
                    prompt
                ],
                cwd=r"C:\Users\muril\PROJETOBRAINROT",
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180
            )

            if resultado.returncode != 0:
                return (
                    "[ERRO CODEX CLI]\n"
                    + resultado.stderr.strip()
                )

            return resultado.stdout.strip()

        except subprocess.TimeoutExpired:
            return "[ERRO CODEX CLI] Timeout."

        except Exception as e:
            return f"[ERRO CODEX CLI] {e}"