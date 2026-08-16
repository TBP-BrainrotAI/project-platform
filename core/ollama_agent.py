import requests
from .agent import Agent


class OllamaAgent(Agent):

    def __init__(self, model):
        super().__init__(model)
        self.model = model

    def ask(self, prompt, num_tokens=1024):

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Você é um agente técnico do BrainRotAI. "
                                "Responda em português do Brasil."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "options": {
                        "temperature": 0.1,
                        "num_predict": num_tokens
                    },
                    "stream": False
                },
                timeout=120
            )

            response.raise_for_status()

            return response.json()["message"]["content"]

        except Exception as e:
            self.available = False
            return f"[ERRO OLLAMA {self.model}] {e}"