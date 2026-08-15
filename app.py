import customtkinter as ctk
from PIL import Image
import requests
import threading

# ==========================================
# PALETA DE CORES (3 TEMAS)
# ==========================================
PALETAS = {
    "Dark": {"fundo": "#1A1B26", "painel": "#24283B", "chat": "#16161E", "texto": "#C0CAF5", "destaque": "#7AA2F7"},
    "Light": {"fundo": "#F0F0F0", "painel": "#E0E0E0", "chat": "#FFFFFF", "texto": "#333333", "destaque": "#3B82F6"}
}

class BrainRotDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BrainRotAI - Central de Comando Pro")
        self.geometry("1200x800")
        self.tema_atual = "Dark"

        # Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- SIDEBAR ---
        self.menu_lateral = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.menu_lateral.grid(row=0, column=0, sticky="nsew")
        
        # Logo
        try:
            img = Image.open("logo.jpg")
            img_tk = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
            ctk.CTkLabel(self.menu_lateral, image=img_tk, text="").pack(pady=(30, 10))
        except: pass
        
        ctk.CTkLabel(self.menu_lateral, text="BrainRotAI", font=("Segoe UI", 22, "bold")).pack(pady=(0, 20))

        # Hub de IAs
        ctk.CTkLabel(self.menu_lateral, text="🧠 HUB DE IA PAI", font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
        lista_ias = ["Qwen 2 (Local)", "GPT-4o (OpenAI)", "Claude 3.5 Sonnet (Anthropic)", "Claude 3 Opus (Anthropic)", "Gemini 1.5 Pro (Google)"]
        self.seletor_ia = ctk.CTkOptionMenu(self.menu_lateral, values=lista_ias, command=self.detectar_api)
        self.seletor_ia.pack(padx=20, pady=5)
        self.seletor_ia.set("Qwen 2 (Local)")

        # Entrada API (Dinâmica)
        self.entrada_api = ctk.CTkEntry(self.menu_lateral, placeholder_text="Chave API (Necessário para Nuvem)", show="*")
        
        # Tema
        ctk.CTkLabel(self.menu_lateral, text="🎨 TEMA", font=("Segoe UI", 12, "bold")).pack(pady=(30, 5))
        self.seletor_tema = ctk.CTkOptionMenu(self.menu_lateral, values=["Dark", "Light"], command=self.mudar_tema)
        self.seletor_tema.pack(padx=20, pady=5)

        # --- ÁREA PRINCIPAL ---
        self.area_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.area_principal.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.area_principal.grid_rowconfigure(1, weight=1)
        self.area_principal.grid_columnconfigure(0, weight=1)

        # Top Bar (Modos)
        self.top_bar = ctk.CTkFrame(self.area_principal, height=50)
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.modo_op = ctk.CTkSegmentedButton(self.top_bar, values=["Manual", "Semi-Auto", "Auto"])
        self.modo_op.pack(side="left", padx=15, pady=10)
        self.modo_op.set("Manual")

        # Chat
        self.chat_area = ctk.CTkTextbox(self.area_principal, font=("Segoe UI", 14), wrap="word")
        self.chat_area.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        self.chat_area.configure(state="disabled")

        # Input
        self.entrada = ctk.CTkEntry(self.area_principal, placeholder_text="Comando para o Agente...", height=50)
        self.entrada.grid(row=2, column=0, sticky="ew", padx=(0, 10))
        self.entrada.bind("<Return>", self.enviar)

        self.btn_enviar = ctk.CTkButton(self.area_principal, text="ENVIAR 🚀", width=120, height=50, command=self.enviar)
        self.btn_enviar.grid(row=2, column=1)

        self.mudar_tema("Dark")

    # --- LÓGICA ---
    def mudar_tema(self, tema):
        self.tema_atual = tema
        ctk.set_appearance_mode(tema)
        cor = PALETAS[tema]
        self.configure(fg_color=cor["fundo"])
        self.menu_lateral.configure(fg_color=cor["painel"])
        self.chat_area.configure(fg_color=cor["chat"], text_color=cor["texto"])
        self.entrada.configure(fg_color=cor["chat"], text_color=cor["texto"])
        self.btn_enviar.configure(fg_color=cor["destaque"])

    def detectar_api(self, escolha):
        if "Local" not in escolha: self.entrada_api.pack(padx=20, pady=10, fill="x")
        else: self.entrada_api.pack_forget()

    def enviar(self, event=None):
        msg = self.entrada.get()
        if not msg.strip(): return
        
        self.chat_historico_update(f"👤 VOCÊ: {msg}\n🤖 BRAINROT ({self.seletor_ia.get()}): ...Processando...\n\n", is_processing=True)
        self.entrada.delete(0, "end")
        threading.Thread(target=self.processar_ia, args=(msg, self.seletor_ia.get(), self.entrada_api.get())).start()

    def chat_historico_update(self, texto, is_processing=False):
        self.chat_area.configure(state="normal")
        if is_processing: self.chat_area.insert("end", texto)
        else:
            self.chat_area.delete("end-3c", "end")
            self.chat_area.insert("end", f"{texto}\n\n")
        self.chat_area.configure(state="disabled")

    def processar_ia(self, msg, ia, api_key):
        resp = "Erro na conexão."
        if "Local" in ia:
            try:
                # O servidor Ollama (localhost:11434)
                res = requests.post("http://localhost:11434/api/generate", json={"model": "qwen2", "prompt": msg, "stream": False})
                resp = res.json().get("response", "Erro no Ollama.")
            except: resp = "Verifique se o Ollama está rodando no terminal."
        else:
            if not api_key: resp = "⚠️ Erro: Você precisa de uma Chave de API para usar modelos de nuvem."
            else: resp = "Conexão com API estabelecida (Simulação: Integração em andamento)."
        
        self.after(0, lambda: self.chat_historico_update(resp))

if __name__ == "__main__":
    BrainRotDashboard().mainloop()