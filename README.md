# 🧠 BrainRotAI

> Orquestrador de Inteligências Artificiais com múltiplos agentes, execução paralela, integração com CLIs e validação de código.

---

## 📌 Sobre o projeto

O **BrainRotAI** é uma aplicação experimental de orquestração de Inteligências Artificiais.

A proposta é utilizar uma IA local como **IA chefe**, responsável por analisar uma solicitação e decidir quais agentes especializados devem participar da resolução.

Dependendo da tarefa, o sistema pode utilizar diferentes agentes, como:

- 🧠 Qwen
- 🦙 Llama
- 💎 Gemini CLI
- 🤖 OpenAI Codex CLI

Os agentes podem trabalhar simultaneamente e seus resultados são posteriormente analisados pela IA chefe.

O projeto também possui um **Sandbox** para validação de códigos gerados pelos agentes.

---

# 🏗️ Arquitetura

A arquitetura atual do BrainRotAI pode ser representada da seguinte forma:

```text
                         ┌──────────────────────┐
                         │       USUÁRIO        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     BrainRotAI       │
                         │      Interface       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      IA CHEFE        │
                         │   Qwen / Llama       │
                         └──────────┬───────────┘
                                    │
                            cria o plano
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        ┌───────────┐        ┌───────────┐        ┌───────────┐
        │   Qwen    │        │  Gemini   │        │   Codex   │
        │   Local   │        │    CLI    │        │    CLI    │
        └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
              │                    │                    │
              └────────────────────┼────────────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │       SANDBOX        │
                         │ Validação de código  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      IA CHEFE        │
                         │      Síntese          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    RESPOSTA FINAL    │
                         └──────────────────────┘