import os
import sys
import re
import time
import subprocess
import pandas as pd
from glob import glob
from unidecode import unidecode
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ── Configurações ────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

URL            = os.getenv("PIMACO_URL", "https://editor.pimaco.com.br/APWeb")
EMAIL          = os.getenv("PIMACO_EMAIL", "")
SENHA          = os.getenv("PIMACO_SENHA", "")
TENTATIVAS_MAX = 3
DOWNLOADS      = os.path.join(os.path.expanduser("~"), "Downloads")
# ─────────────────────────────────────────────────────────────────────────────


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# ── Helpers de nome / texto ──────────────────────────────────────────────────
def abreviar_nome(nome_completo):
    partes = str(nome_completo).split()
    if len(partes) <= 3:
        return " ".join(partes).title()
    abrev = " ".join(partes[:3]).title()
    for p in partes[3:]:
        abrev += f" {p[0].upper()}."
    return abrev


def formatar_texto(texto, correcoes=None):
    if correcoes is None:
        correcoes = {"injetavel": "Injetavel"}
    normalizado = unidecode(str(texto)).lower()
    return correcoes.get(normalizado, str(texto))


# ── Leitura do Excel mais recente ────────────────────────────────────────────
arquivos_xlsx = glob(os.path.join(DOWNLOADS, "*.xlsx"))
if not arquivos_xlsx:
    raise FileNotFoundError("Nenhum arquivo .xlsx encontrado na pasta Downloads.")

arquivo_mais_recente = max(arquivos_xlsx, key=os.path.getmtime)
tabela = pd.read_excel(arquivo_mais_recente)
tabela.columns = tabela.columns.str.strip().str.lower()
print("Colunas detectadas:", tabela.columns.tolist())

coluna_vacina = next((c for c in tabela.columns if re.search(r'^vacinas?\b', c, re.I)), None)
coluna_nome   = next((c for c in tabela.columns if re.search(r'\bnomes?\b',  c, re.I)), None)
coluna_via    = next((c for c in tabela.columns if re.search(r'\bvia\b',     c, re.I)), None)

print(f"Colunas: Nome={coluna_nome}, Vacina={coluna_vacina}, Via={coluna_via}")

if not all([coluna_nome, coluna_vacina, coluna_via]):
    raise ValueError("Não foi possível encontrar todas as colunas necessárias no arquivo Excel.")


# ── Utilitários de PDF ───────────────────────────────────────────────────────
def aguardar_novo_pdf(arquivos_iniciais):
    print("Aguardando novo PDF...")
    while True:
        time.sleep(1)
        novos = [f for f in set(os.listdir(DOWNLOADS)) - arquivos_iniciais if f.endswith(".pdf")]
        if novos:
            print("Novo PDF detectado.")
            return


def abrir_ultimo_pdf():
    pdfs = sorted(
        [os.path.join(DOWNLOADS, f) for f in os.listdir(DOWNLOADS) if f.endswith(".pdf")],
        key=os.path.getmtime, reverse=True
    )
    if not pdfs:
        print("Nenhum PDF encontrado.")
        return
    print(f"Abrindo: {pdfs[0]}")
    subprocess.Popen([pdfs[0]], shell=True)


# ── Janela de finalização ────────────────────────────────────────────────────
def mostrar_janela_finalizada():
    root = tk.Tk()
    root.title("Processo Finalizado")
    root.geometry("800x700")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.config(bg="#F0F0F0")

    canvas = tk.Canvas(root, width=800, height=700, bg="#F0F0F0", highlightthickness=0)
    canvas.pack()

    try:
        img = Image.open(get_resource_path("Doc.png"))
        img_dark = ImageEnhance.Brightness(img).enhance(0.6)
        img_tk = ImageTk.PhotoImage(img_dark)
        canvas.create_image(400, 350, image=img_tk)
    except Exception as e:
        print("Erro ao carregar imagem:", e)

    canvas.create_text(401, 351, text="As etiquetas das vacinas foram impressas!",
                       font=("Arial", 24, "bold"), fill="black")
    canvas.create_text(400, 350, text="As etiquetas das vacinas foram impressas!",
                       font=("Arial", 24, "bold"), fill="yellow")

    tk.Button(root, text="Fechar", font=("Arial", 12),
              command=root.quit, bg="#4CAF50", fg="white").pack(pady=10)
    root.mainloop()


# ── Automação com Playwright ─────────────────────────────────────────────────
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    # ── Login ────────────────────────────────────────────────────────────────
    logado = False
    for tentativa in range(1, TENTATIVAS_MAX + 1):
        print(f"Tentativa de login {tentativa}/{TENTATIVAS_MAX}")
        page.goto(URL)
        page.wait_for_load_state("networkidle")

        try:
            # Tenta preencher pelos seletores mais comuns de e-mail e senha
            page.locator(
                'input[type="email"], input[name*="email"], input[name*="user"], input[id*="email"], input[id*="user"]'
            ).first.fill(EMAIL)
            page.locator('input[type="password"]').first.fill(SENHA)
            page.keyboard.press("Enter")
        except Exception:
            # Fallback: navega por Tab como o script original fazia
            page.keyboard.press("Tab")
            page.keyboard.press("Tab")
            page.keyboard.type(EMAIL)
            page.keyboard.press("Tab")
            page.keyboard.type(SENHA)
            page.keyboard.press("Enter")

        # Aguarda até a URL mudar (indica redirecionamento pós-login)
        try:
            page.wait_for_url(lambda url: url.rstrip("/") != URL.rstrip("/"), timeout=60_000)
            logado = True
            print("Login realizado com sucesso!")
            break
        except PlaywrightTimeoutError:
            # Fallback: verifica se apareceu algum elemento típico de área logada
            try:
                page.wait_for_selector(
                    "[class*='dashboard'], [class*='editor'], [class*='logged'], [class*='workspace']",
                    timeout=5_000
                )
                logado = True
                print("Login realizado com sucesso!")
                break
            except PlaywrightTimeoutError:
                print("Login não concluído. Tentando novamente...")
                time.sleep(5)

    if not logado:
        print("Falha no login. Encerrando.")
        browser.close()
        sys.exit(1)

    # ── Fluxo pós-login ──────────────────────────────────────────────────────
    # Sequência de cliques/digitação original convertida de coordenadas PyAutoGUI
    page.mouse.click(376, 190)
    page.wait_for_timeout(600)
    page.keyboard.type("6187")
    page.wait_for_timeout(600)
    page.mouse.click(1196, 378)
    page.wait_for_timeout(600)
    page.mouse.click(406, 413)
    page.wait_for_timeout(1500)
    page.mouse.click(143, 512)
    page.wait_for_timeout(600)
    page.mouse.click(1244, 360)
    page.wait_for_timeout(1000)

    # ── Preenchimento de etiquetas ───────────────────────────────────────────
    for index, row in tabela.iterrows():
        if pd.isna(row[coluna_nome]) and pd.isna(row[coluna_vacina]) and pd.isna(row[coluna_via]):
            continue

        nome   = abreviar_nome(row[coluna_nome])   if coluna_nome   else "N/A"
        vacina = formatar_texto(row[coluna_vacina]) if coluna_vacina else "N/A"
        via    = formatar_texto(row[coluna_via])    if coluna_via    else "N/A"

        page.mouse.click(119, 350)
        page.wait_for_timeout(400)

        # Campo tamanho da fonte → seleciona tudo e digita "10"
        page.mouse.click(783, 360)
        page.wait_for_timeout(300)
        page.keyboard.press("Control+A")
        page.keyboard.type("10")
        page.wait_for_timeout(300)

        page.mouse.click(943, 354)
        page.wait_for_timeout(300)
        page.mouse.click(508, 351)
        page.wait_for_timeout(300)
        page.mouse.click(445, 323)
        page.wait_for_timeout(300)

        # Campo de texto da etiqueta
        page.mouse.click(676, 459)
        page.wait_for_timeout(300)
        page.keyboard.press("Control+A")
        page.keyboard.type(nome)
        page.keyboard.press("Enter")
        page.keyboard.type(vacina)
        page.keyboard.press("Enter")
        page.keyboard.type(via)
        page.wait_for_timeout(300)

        page.mouse.click(800, 248)
        page.wait_for_timeout(2000)
        page.mouse.click(770, 248)
        page.wait_for_timeout(500)

    print("Formatação e digitação completas!")

    # ── Exportar PDF e imprimir ──────────────────────────────────────────────
    arquivos_iniciais = set(os.listdir(DOWNLOADS))

    page.mouse.click(1169, 164)
    page.wait_for_timeout(600)
    page.mouse.click(1045, 652)

    aguardar_novo_pdf(arquivos_iniciais)
    abrir_ultimo_pdf()
    time.sleep(2)
    page.keyboard.press("Control+P")
    time.sleep(1.5)
    page.keyboard.press("Enter")

    browser.close()

mostrar_janela_finalizada()
