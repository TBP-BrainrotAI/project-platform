import re
import subprocess
import sys
import tempfile
import os


class Sandbox:

    def __init__(self, timeout=10):
        self.timeout = timeout

    # ==========================================
    # EXTRAIR CÓDIGOS PYTHON
    # ==========================================

    def extrair_codigos(self, texto):

        if not texto:
            return []

        codigos = []

        # ==========================================
        # BLOCO ```python ... ```
        # ==========================================

        padrao_python = re.compile(
            r"```(?:python|py)\s*\n?(.*?)```",
            re.IGNORECASE | re.DOTALL
        )

        encontrados = padrao_python.findall(texto)

        for codigo in encontrados:

            codigo = codigo.strip()

            if codigo:
                codigos.append(codigo)

        # ==========================================
        # BLOCO ``` ... ```
        # ==========================================

        if not codigos:

            padrao_generico = re.compile(
                r"```\s*\n?(.*?)```",
                re.DOTALL
            )

            encontrados = padrao_generico.findall(texto)

            for codigo in encontrados:

                codigo = codigo.strip()

                if codigo:
                    codigos.append(codigo)

        # ==========================================
        # NOVO FALLBACK
        # ==========================================
        #
        # Se o texto já for código puro, significa
        # que o app.py provavelmente já removeu
        # os ```python ... ```.
        #
        # Nesse caso NÃO procuramos outro bloco.
        # Usamos o próprio texto como código.
        #

        if not codigos:

            texto_limpo = texto.strip()

            if texto_limpo:

                indicadores_python = [
                    "def ",
                    "import ",
                    "from ",
                    "class ",
                    "print(",
                    "if ",
                    "for ",
                    "while ",
                    "return ",
                    "="
                ]

                parece_codigo = any(
                    indicador in texto_limpo
                    for indicador in indicadores_python
                )

                if parece_codigo:
                    codigos.append(texto_limpo)

        return codigos

    # ==========================================
    # EXECUTAR CÓDIGO
    # ==========================================

    def executar_codigo(self, codigo):

        arquivo = None

        try:

            # ==========================================
            # CRIAR ARQUIVO TEMPORÁRIO
            # ==========================================

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8"
            ) as f:

                f.write(codigo)

                arquivo = f.name

            # ==========================================
            # EXECUTAR PYTHON
            # ==========================================

            processo = subprocess.run(
                [
                    sys.executable,
                    arquivo
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace"
            )

            sucesso = processo.returncode == 0

            return {
                "sucesso": sucesso,
                "saida": processo.stdout.strip(),
                "erro": processo.stderr.strip()
            }

        except subprocess.TimeoutExpired:

            return {
                "sucesso": False,
                "saida": "",
                "erro": (
                    f"Execução excedeu o limite "
                    f"de {self.timeout} segundos."
                )
            }

        except Exception as e:

            return {
                "sucesso": False,
                "saida": "",
                "erro": str(e)
            }

        finally:

            if arquivo and os.path.exists(arquivo):

                try:
                    os.remove(arquivo)

                except Exception:
                    pass

    # ==========================================
    # EXECUTAR TEXTO
    # ==========================================

    def executar(self, texto):

        codigos = self.extrair_codigos(texto)

        # ==========================================
        # NENHUM CÓDIGO
        # ==========================================

        if not codigos:

            return {
                "sucesso": False,
                "saida": "",
                "erro": "Nenhum bloco de código Python encontrado.",
                "codigos": []
            }

        # ==========================================
        # EXECUTAR PRIMEIRO BLOCO
        # ==========================================

        resultado = self.executar_codigo(
            codigos[0]
        )

        resultado["codigos"] = codigos

        return resultado
