# 🧠 BrainRotAI

BrainRotAI é um orquestrador local de inteligência artificial que planeja, divide tarefas e executa múltiplos agentes em paralelo para resolver problemas complexos e gerar código.

O sistema conta com um **Sandbox Híbrido** que extrai blocos de código gerados pelos agentes e os testa automaticamente antes que a IA chefe sintetize a resposta final.

## ⚙️ Arquitetura
* **👑 IA Chefe:** Qwen 2.5 (rodando localmente via Ollama). Responsável pelo planejamento e síntese.
* **🤖 Agentes de Execução:**
  * **Qwen:** Raciocínio geral e programação.
  * **Codex CLI:** Especialista na geração de scripts e debugging.
  * **Gemini CLI:** Revisão técnica e algoritmos complexos.

## 🚀 Pré-requisitos
Para rodar este projeto na sua máquina, você vai precisar de:
1. **Python 3** instalado.
2. **Ollama** instalado e rodando com o modelo Qwen (`ollama run qwen2.5`).
3. **Gemini CLI** e **Codex CLI** configurados nas variáveis de ambiente do Windows (comandos `gemini.cmd` e `codex.cmd` devem estar acessíveis no terminal).

## 🛠️ Instalação e Execução

1. Clone este repositório:
   ```bash
   git clone [https://github.com/TBP-BrainrotAI/project-platform.git](https://github.com/TBP-BrainrotAI/project-platform.git)
