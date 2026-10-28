"""
Launcher — Interface gráfica moderna para o sistema de etiquetas de vacinas.
Abre uma janela limpa e intuitiva para iniciar o processo e gerenciar configurações.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

# DPI Awareness no Windows para deixar textos e botões perfeitamente nítidos
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)


def centralizar_janela(janela, largura, altura):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")


# ── Janela de Configurações (.env) ──────────────────────────────────
def abrir_janela_configuracoes():
    """Abre modal elegante para editar credenciais do .env sem tocar em código."""
    janela_cfg = tk.Toplevel(root)
    janela_cfg.title("Configurações do Sistema")
    janela_cfg.geometry("460x520")
    janela_cfg.resizable(False, False)
    janela_cfg.config(bg="#F8FAFC")
    janela_cfg.attributes("-topmost", True)
    centralizar_janela(janela_cfg, 460, 520)

    try:
        janela_cfg.iconbitmap(get_resource_path("vacina.ico"))
    except Exception:
        pass

    # Carrega valores atuais
    import Vacinasnovo
    
    # Cabeçalho
    header = tk.Frame(janela_cfg, bg="#F8FAFC", padx=25, pady=15)
    header.pack(fill="x")
    tk.Label(
        header, text="Configurações & Credenciais",
        font=("Segoe UI", 14, "bold"), bg="#F8FAFC", fg="#0F172A"
    ).pack(anchor="w")
    tk.Label(
        header, text="Os dados são salvos localmente e protegidos de envio externo.",
        font=("Segoe UI", 9), bg="#F8FAFC", fg="#64748B"
    ).pack(anchor="w", pady=(2, 0))

    # Form Container
    form_frame = tk.Frame(janela_cfg, bg="#FFFFFF", bd=1, relief="solid", highlightthickness=0)
    form_frame.config(highlightbackground="#E2E8F0", highlightcolor="#E2E8F0")
    form_frame.pack(fill="both", expand=True, padx=25, pady=(0, 15))

    campos = {}

    def criar_campo(pai, label, chave, valor_padrao, secreto=False):
        row = tk.Frame(pai, bg="#FFFFFF", padx=15, pady=6)
        row.pack(fill="x")
        tk.Label(row, text=label, font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#334155").pack(anchor="w")
        
        entry_frame = tk.Frame(row, bg="#FFFFFF")
        entry_frame.pack(fill="x", pady=(2, 0))
        
        var = tk.StringVar(value=valor_padrao)
        entry = tk.Entry(
            entry_frame, textvariable=var, font=("Segoe UI", 10),
            bg="#F8FAFC", fg="#0F172A", relief="solid", bd=1,
            show="*" if secreto else ""
        )
        entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        if secreto:
            def toggle():
                if entry.cget("show") == "":
                    entry.config(show="*")
                    btn_eye.config(text="👁")
                else:
                    entry.config(show="")
                    btn_eye.config(text="🔒")
            btn_eye = tk.Button(
                entry_frame, text="👁", font=("Segoe UI", 9),
                command=toggle, relief="flat", bg="#F1F5F9", fg="#475569",
                cursor="hand2", padx=6
            )
            btn_eye.pack(side="right", padx=(4, 0))

        campos[chave] = var

    # Adiciona os campos
    criar_campo(form_frame, "E-mail Pimaco:", "PIMACO_EMAIL", os.getenv("PIMACO_EMAIL", ""))
    criar_campo(form_frame, "Senha Pimaco:", "PIMACO_SENHA", os.getenv("PIMACO_SENHA", ""), secreto=True)
    criar_campo(form_frame, "Código do Produto:", "PIMACO_PRODUTO", os.getenv("PIMACO_PRODUTO", "6187"))
    criar_campo(form_frame, "Token GitHub:", "GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""), secreto=True)
    criar_campo(form_frame, "E-mail Gmail (Backup):", "GMAIL_USER", os.getenv("GMAIL_USER", ""))
    criar_campo(form_frame, "Senha App Gmail:", "GMAIL_APP_PASS", os.getenv("GMAIL_APP_PASS", ""), secreto=True)

    # Botão Salvar
    def salvar():
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("# ─────────────────────────────────────────────\n")
                f.write("# CONFIGURAÇÕES SALVAS PELO APLICATIVO\n")
                f.write("# ─────────────────────────────────────────────\n\n")
                f.write(f"PIMACO_URL={os.getenv('PIMACO_URL', 'https://editor.pimaco.com.br/APWeb')}\n")
                f.write(f"PIMACO_EMAIL={campos['PIMACO_EMAIL'].get().strip()}\n")
                f.write(f"PIMACO_SENHA={campos['PIMACO_SENHA'].get().strip()}\n")
                f.write(f"PIMACO_PRODUTO={campos['PIMACO_PRODUTO'].get().strip()}\n")
                f.write(f"FONTE_ETIQUETA={os.getenv('FONTE_ETIQUETA', 'Arial')}\n")
                f.write(f"TAMANHO_FONTE={os.getenv('TAMANHO_FONTE', '10')}\n")
                f.write(f"GITHUB_TOKEN={campos['GITHUB_TOKEN'].get().strip()}\n")
                f.write(f"GITHUB_REPO={os.getenv('GITHUB_REPO', 'Cainho-pt-br/Vacinas')}\n")
                f.write(f"GITHUB_FILE={os.getenv('GITHUB_FILE', 'vacinas.json')}\n")
                f.write(f"GMAIL_USER={campos['GMAIL_USER'].get().strip()}\n")
                f.write(f"GMAIL_APP_PASS={campos['GMAIL_APP_PASS'].get().strip()}\n")
                f.write(f"EMAIL_DESTINO={campos['GMAIL_USER'].get().strip()}\n")

            # Atualiza variáveis na memória
            os.environ["PIMACO_EMAIL"] = campos['PIMACO_EMAIL'].get().strip()
            os.environ["PIMACO_SENHA"] = campos['PIMACO_SENHA'].get().strip()
            os.environ["PIMACO_PRODUTO"] = campos['PIMACO_PRODUTO'].get().strip()
            os.environ["GITHUB_TOKEN"] = campos['GITHUB_TOKEN'].get().strip()
            os.environ["GMAIL_USER"] = campos['GMAIL_USER'].get().strip()
            os.environ["GMAIL_APP_PASS"] = campos['GMAIL_APP_PASS'].get().strip()

            import importlib
            importlib.reload(Vacinasnovo)

            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!", parent=janela_cfg)
            janela_cfg.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar configurações:\n{e}", parent=janela_cfg)

    footer = tk.Frame(janela_cfg, bg="#F8FAFC", padx=25, pady=5)
    footer.pack(fill="x", side="bottom")

    tk.Button(
        footer, text="Salvar Alterações", font=("Segoe UI", 10, "bold"),
        bg="#0F9D76", fg="white", activebackground="#0D8A66", activeforeground="white",
        relief="flat", cursor="hand2", padx=20, pady=8, command=salvar
    ).pack(side="right")

    tk.Button(
        footer, text="Cancelar", font=("Segoe UI", 10),
        bg="#E2E8F0", fg="#334155", activebackground="#CBD5E1",
        relief="flat", cursor="hand2", padx=15, pady=8, command=janela_cfg.destroy
    ).pack(side="right", padx=(0, 10))


# ── Tela de Finalização ─────────────────────────────────────────────
def mostrar_tela_finalizada():
    """Abre janela moderna de confirmação com a imagem Doc.png."""
    janela = tk.Toplevel(root)
    janela.title("Impressão Concluída")
    janela.geometry("800x700")
    janela.attributes("-topmost", True)
    janela.resizable(False, False)
    janela.config(bg="#0F172A")
    centralizar_janela(janela, 800, 700)

    try:
        janela.iconbitmap(get_resource_path("vacina.ico"))
    except Exception:
        pass

    canvas = tk.Canvas(janela, width=800, height=700, bg="#0F172A", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    try:
        from PIL import Image, ImageTk, ImageEnhance
        img = Image.open(get_resource_path("Doc.png"))
        img_dark = ImageEnhance.Brightness(img).enhance(0.5)
        img_tk = ImageTk.PhotoImage(img_dark)
        canvas.create_image(400, 350, image=img_tk)
        canvas.image = img_tk
    except Exception:
        pass

    # Card translúcido central
    canvas.create_rectangle(140, 240, 660, 480, fill="#0F172A", outline="#1E293B", width=2)

    # Ícone de sucesso / check
    canvas.create_text(
        400, 280, text="✓",
        font=("Segoe UI", 32, "bold"), fill="#10B981"
    )

    # Título elegante
    canvas.create_text(
        400, 335, text="Etiquetas Processadas com Sucesso!",
        font=("Segoe UI", 18, "bold"), fill="#F8FAFC"
    )

    # Mensagem descritiva
    canvas.create_text(
        400, 380,
        text="As etiquetas foram digitadas, enviadas para impressão\ne o backup do PDF foi gerado.",
        font=("Segoe UI", 11), fill="#94A3B8", justify="center"
    )

    # Botão Fechar moderno
    btn_fechar = tk.Button(
        janela, text="Concluir e Fechar", font=("Segoe UI", 12, "bold"),
        command=janela.destroy, bg="#0F9D76", fg="white",
        activebackground="#0D8A66", activeforeground="white",
        relief="flat", padx=30, pady=8, cursor="hand2"
    )
    canvas.create_window(400, 440, window=btn_fechar)


# ── Execução do Processo ───────────────────────────────────────────
def atualizar_status(texto, cor_texto="#475569", icone="●", cor_icone="#10B981"):
    lbl_dot.config(text=icone, fg=cor_icone)
    lbl_status.config(text=texto, fg=cor_texto)


def iniciar_processo():
    """Roda o Vacinasnovo.py em uma thread separada para manter a UI fluida."""
    btn_iniciar.config(state="disabled", text="Processando etiquetas...", bg="#64748B", cursor="wait")
    atualizar_status("Buscando lista de vacinas no servidor...", "#0D9488", "⏳", "#0D9488")
    root.update()

    def executar():
        try:
            import Vacinasnovo
            Vacinasnovo.main()

            root.after(0, lambda: atualizar_status("Etiquetas impressas com sucesso!", "#059669", "✔", "#059669"))
            root.after(0, mostrar_tela_finalizada)

        except FileNotFoundError as e:
            root.after(0, lambda: atualizar_status("Nenhuma lista encontrada na fila.", "#DC2626", "✖", "#DC2626"))
            root.after(0, lambda: messagebox.showwarning("Sem Lista", str(e)))

        except ValueError as e:
            root.after(0, lambda: atualizar_status("Erro de configuração.", "#DC2626", "✖", "#DC2626"))
            root.after(0, lambda: messagebox.showwarning("Configuração Necessária", str(e)))

        except Exception as e:
            root.after(0, lambda: atualizar_status("Erro durante o processo.", "#DC2626", "✖", "#DC2626"))
            root.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro:\n\n{str(e)}"))

        finally:
            root.after(0, lambda: btn_iniciar.config(
                state="normal", text="Imprimir Etiquetas", bg="#0F9D76", cursor="hand2"
            ))

    thread = threading.Thread(target=executar, daemon=True)
    thread.start()


# ── Janela Principal ───────────────────────────────────────────────
root = tk.Tk()
root.title("Etiquetas de Vacinas — Pimaco")
root.geometry("520x470")
root.resizable(False, False)
root.config(bg="#F1F5F9")
centralizar_janela(root, 520, 470)

# Ícone do aplicativo
try:
    root.iconbitmap(get_resource_path("vacina.ico"))
except Exception:
    pass

# Botão superior discreto de Configurações
top_bar = tk.Frame(root, bg="#F1F5F9", padx=20, pady=10)
top_bar.pack(fill="x")

btn_config = tk.Button(
    top_bar, text="⚙️ Configurações", font=("Segoe UI", 9),
    bg="#E2E8F0", fg="#334155", activebackground="#CBD5E1",
    relief="flat", cursor="hand2", padx=10, pady=4,
    command=abrir_janela_configuracoes
)
btn_config.pack(side="right")

# Card Central Moderno
card = tk.Frame(root, bg="#FFFFFF", padx=36, pady=28, relief="flat")
card.place(relx=0.5, rely=0.52, anchor="center", width=460, height=380)

# Borda suave visual no card
card.config(highlightbackground="#E2E8F0", highlightthickness=1)

# Ícone/Imagem Principal
try:
    from PIL import Image, ImageTk
    resample_mode = getattr(Image, "Resampling", Image).LANCZOS
    img = Image.open(get_resource_path("vacina.png")).resize((72, 72), resample_mode)
    img_tk = ImageTk.PhotoImage(img)
    lbl_img = tk.Label(card, image=img_tk, bg="#FFFFFF")
    lbl_img.image = img_tk
    lbl_img.pack(pady=(0, 10))
except Exception:
    pass

# Título
tk.Label(
    card, text="Etiquetas de Vacinas",
    font=("Segoe UI", 18, "bold"), bg="#FFFFFF", fg="#0F172A"
).pack(pady=(0, 4))

# Subtítulo explicativo
tk.Label(
    card,
    text="Busca a fila de pacientes do formulário e preenche\nas etiquetas Pimaco no navegador automaticamente.",
    font=("Segoe UI", 10), bg="#FFFFFF", fg="#64748B", justify="center"
).pack(pady=(0, 22))

# Botão Principal com Efeito Hover
def on_enter(e):
    if btn_iniciar["state"] == "normal":
        btn_iniciar.config(bg="#0D8A66")

def on_leave(e):
    if btn_iniciar["state"] == "normal":
        btn_iniciar.config(bg="#0F9D76")

btn_iniciar = tk.Button(
    card, text="Imprimir Etiquetas",
    font=("Segoe UI", 13, "bold"),
    bg="#0F9D76", fg="white",
    activebackground="#097354", activeforeground="white",
    relief="flat", cursor="hand2",
    padx=34, pady=11,
    command=iniciar_processo
)
btn_iniciar.pack(pady=(0, 18))
btn_iniciar.bind("<Enter>", on_enter)
btn_iniciar.bind("<Leave>", on_leave)

# Pill Badge de Status
status_badge = tk.Frame(card, bg="#F8FAFC", padx=12, pady=6, relief="flat")
status_badge.config(highlightbackground="#E2E8F0", highlightthickness=1)
status_badge.pack()

lbl_dot = tk.Label(
    status_badge, text="●", font=("Segoe UI", 10, "bold"),
    bg="#F8FAFC", fg="#10B981"
)
lbl_dot.pack(side="left", padx=(0, 6))

lbl_status = tk.Label(
    status_badge, text="Pronto para iniciar",
    font=("Segoe UI", 9), bg="#F8FAFC", fg="#475569"
)
lbl_status.pack(side="left")

# Atalho de teclado (Enter para iniciar)
root.bind("<Return>", lambda event: iniciar_processo() if btn_iniciar["state"] == "normal" else None)

if __name__ == "__main__":
    root.mainloop()
