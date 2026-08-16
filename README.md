# 🧠 BrainRotAI

> Orquestrador de Inteligências Artificiais com múltiplos agentes, execução paralela, integração com CLIs, múltiplas contas do Codex e validação automática de código.

---

## 📌 Sobre o projeto

O **BrainRotAI** é uma aplicação experimental de orquestração de Inteligências Artificiais.

A proposta é utilizar uma IA local como **IA chefe**, responsável por analisar uma solicitação, definir quais agentes devem participar da tarefa e, posteriormente, sintetizar os resultados obtidos.

Dependendo da tarefa, o sistema pode utilizar diferentes agentes:

- 🧠 Qwen
- 🦙 Llama
- 💎 Gemini CLI
- 🤖 OpenAI Codex CLI

Os agentes podem trabalhar simultaneamente, permitindo que diferentes modelos analisem a mesma solicitação.

Após a execução, a **IA chefe** analisa os resultados e produz uma única resposta final.

O projeto também possui um **Sandbox** para testar códigos gerados pelos agentes quando a validação for considerada necessária.

---

# 🏗️ Arquitetura

A arquitetura atual do BrainRotAI funciona da seguinte forma:

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
              │                    │             ┌──────┴──────┐
              │                    │             │             │
              │                    │          Conta 1      Conta 2
              │                    │
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
