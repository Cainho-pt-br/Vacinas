"""
Vacinas.py — Automação de etiquetas Pimaco para vacinas
Usa Playwright (controle real do browser) em vez de PyAutoGUI (coordenadas de pixel).
Lê dados de vacinas.json no GitHub (preenchido pelo formulário da secretária).

Instalação (primeira vez):
    pip install playwright requests unidecode
    playwright install chromium
"""

import os
import sys
import time
import subprocess
import json
import base64
import smtplib
import zipfile
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import requests
from unidecode import unidecode
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ─────────────────────────────────────────────
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE
# ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    # Carrega .env da pasta do script ou do executável se empacotado
    if getattr(sys, "frozen", False):
        _base_dir = os.path.dirname(sys.executable)
    else:
        _base_dir = os.path.dirname(os.path.abspath(__file__))
    _env_path = os.path.join(_base_dir, ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Pimaco
URL_LOGIN      = os.getenv("PIMACO_URL", "https://editor.pimaco.com.br/APWeb")
EMAIL          = os.getenv("PIMACO_EMAIL", "")
SENHA          = os.getenv("PIMACO_SENHA", "")
CODIGO_PRODUTO = os.getenv("PIMACO_PRODUTO", "6187")
FONTE_ETIQUETA = os.getenv("FONTE_ETIQUETA", "Arial")
TAMANHO_FONTE  = os.getenv("TAMANHO_FONTE", "10")
DOWNLOADS      = os.path.join(os.path.expanduser("~"), "Downloads")

# GitHub — repositório onde o formulário salva vacinas.json
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO    = os.getenv("GITHUB_REPO", "Cainho-pt-br/Vacinas")
GITHUB_FILE    = os.getenv("GITHUB_FILE", "vacinas.json")
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# SumatraPDF — para impressão em tamanho real (sem escala)
SUMATRA_EXE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "SumatraPDF.exe")

# Email — backup do PDF por Gmail SMTP
GMAIL_USER     = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS", "")
EMAIL_DESTINO  = os.getenv("EMAIL_DESTINO", GMAIL_USER)

# Tempo máximo (ms) para aguardar elementos aparecerem
TIMEOUT = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))

# ─────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────

def abreviar_nome(nome_completo: str) -> str:
    """Abrevia nomes com mais de 3 palavras."""
    partes = str(nome_completo).strip().split()
    if len(partes) <= 3:
        return " ".join(partes).title()
    abrev = " ".join(partes[:3]).title()
    for parte in partes[3:]:
        abrev += f" {parte[0].upper()}."
    return abrev


def formatar_texto(texto: str) -> str:
    """Primeira letra maiúscula + correções de acentuação para termos de vacina."""
    correcoes = {
        "injetavel": "Injetável",
        "injetvel": "Injetável",
        "intramuscular": "Intramuscular",
        "subcutanea": "Subcutânea",
        "oral": "Oral",
        "intradermica": "Intradérmica",
    }
    texto_str = str(texto).strip()
    chave = unidecode(texto_str).lower()
    corrigido = correcoes.get(chave, texto_str)
    # Garante primeira letra maiúscula, restante minúscula (se não veio do dicionário)
    if chave not in correcoes:
        corrigido = corrigido.capitalize()
    return corrigido


def ler_dados_github() -> list[dict]:
    """Baixa vacinas.json do GitHub e retorna lista de dicts [{nome, vacina, via}, ...]."""
    print("Buscando vacinas.json no GitHub...")
    # Tenta com token; se falhar (401), tenta sem (repo público)
    resp = requests.get(GITHUB_API_URL, headers=GITHUB_HEADERS)
    if resp.status_code == 401:
        print("Token inválido, tentando acesso público...")
        resp = requests.get(GITHUB_API_URL)

    if resp.status_code == 404:
        raise FileNotFoundError("vacinas.json não encontrado no repositório. Nenhuma lista foi enviada ainda.")

    resp.raise_for_status()
    dados_json = resp.json()

    conteudo = base64.b64decode(dados_json["content"]).decode("utf-8")
    lista = json.loads(conteudo)

    # Filtra entradas vazias
    lista = [e for e in lista if e.get("nome") or e.get("vacina") or e.get("via")]

    if not lista:
        raise ValueError("vacinas.json está vazio. Nenhum paciente na fila.")

    print(f"{len(lista)} paciente(s) encontrado(s) na fila.")
    return lista


def apagar_json_github():
    """Apaga vacinas.json do GitHub para limpar a fila após impressão."""
    print("Limpando fila no GitHub (apagando vacinas.json)...")
    # Precisa do SHA atual para deletar
    resp = requests.get(GITHUB_API_URL, headers=GITHUB_HEADERS)
    if resp.status_code == 404:
        print("vacinas.json já não existe.")
        return

    resp.raise_for_status()
    sha = resp.json()["sha"]

    del_resp = requests.delete(
        GITHUB_API_URL,
        headers=GITHUB_HEADERS,
        json={
            "message": "Fila processada e impressa — limpando vacinas.json",
            "sha": sha,
        },
    )
    del_resp.raise_for_status()
    print("Fila limpa. Próximo envio começa do zero.")


def enviar_pdf_por_email(caminho_pdf, impressao_ok):
    """Envia o PDF das etiquetas por email como backup."""
    if impressao_ok:
        assunto = "Etiquetas de Vacinas - PDF (backup)"
        corpo = "As etiquetas foram enviadas para a impressora.\nSegue o PDF em anexo como backup."
    else:
        assunto = "Etiquetas de Vacinas - PDF para impressao"
        corpo = "Nao foi possivel imprimir automaticamente.\nImprima o PDF em anexo pelo celular ou computador."

    print(f"Enviando PDF por email para {EMAIL_DESTINO}...")
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = EMAIL_DESTINO
        msg["Subject"] = assunto

        # Comprime o PDF em ZIP (PDFs do Pimaco passam de 25MB, limite do Gmail)
        caminho_zip = caminho_pdf.replace(".pdf", ".zip")
        with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(caminho_pdf, os.path.basename(caminho_pdf))
        tamanho_zip = os.path.getsize(caminho_zip) / 1024 / 1024
        print(f"PDF comprimido: {tamanho_zip:.1f} MB")

        corpo += "\n\nO PDF foi comprimido em ZIP. Extraia o arquivo antes de imprimir."
        corpo += "\nImprima em TAMANHO REAL (100%) para as etiquetas ficarem alinhadas."
        msg.attach(MIMEText(corpo, "plain"))

        with open(caminho_zip, "rb") as f:
            anexo = MIMEBase("application", "zip")
            anexo.set_payload(f.read())
            encoders.encode_base64(anexo)
            anexo.add_header("Content-Disposition", 'attachment; filename="etiquetas_vacinas.zip"')
            msg.attach(anexo)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(GMAIL_USER, GMAIL_APP_PASS)
            servidor.send_message(msg)

        print("Email enviado com sucesso!")
        # Limpa o ZIP temporário
        os.remove(caminho_zip)
    except Exception as e:
        print(f"Falha ao enviar email: {e}")


# ─────────────────────────────────────────────
# IMPRESSÃO SILENCIOSA (SumatraPDF)
# ─────────────────────────────────────────────

def garantir_sumatra():
    """Verifica se SumatraPDF existe. Se não, baixa automaticamente (~15 MB)."""
    if os.path.exists(SUMATRA_EXE):
        return SUMATRA_EXE

    print("SumatraPDF não encontrado. Baixando (~15 MB)...")
    sumatra_url = "https://www.sumatrapdfreader.org/dl/rel/3.5.2/SumatraPDF-3.5.2-64.exe"

    try:
        resp = requests.get(sumatra_url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(SUMATRA_EXE, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"SumatraPDF salvo em: {SUMATRA_EXE}")
        return SUMATRA_EXE
    except Exception as e:
        print(f"ERRO ao baixar SumatraPDF: {e}")
        if os.path.exists(SUMATRA_EXE):
            os.remove(SUMATRA_EXE)
        return None


def imprimir_pdf(caminho_pdf):
    """Abre o PDF no leitor padrão para impressão manual em tamanho real."""
    print("Abrindo PDF para impressão...")
    try:
        os.startfile(caminho_pdf)
        print("PDF aberto. Imprima com: Ctrl+P → Tamanho real (100%).")
        return True
    except Exception as e:
        print(f"Falha ao abrir PDF: {e}")
        return False


# ─────────────────────────────────────────────
# AUTOMAÇÃO PLAYWRIGHT
# ─────────────────────────────────────────────

def fazer_login(page):
    if not EMAIL or not SENHA:
        raise ValueError("Credenciais da Pimaco não configuradas. Preencha PIMACO_EMAIL e PIMACO_SENHA no arquivo .env.")
    print("Abrindo site e fazendo login...")
    page.goto(URL_LOGIN)
    page.wait_for_load_state("networkidle")

    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="password"]', SENHA)
    page.click('button[type="submit"]:has-text("Entrar")')

    # Aguarda indicador de login: campo de busca de produto
    page.wait_for_selector('input[name="nomeCodigo"]', timeout=TIMEOUT)
    print("Login OK.")


def abrir_produto(page):
    print(f"Buscando produto {CODIGO_PRODUTO}...")
    campo = page.locator('input[name="nomeCodigo"]')
    campo.click()
    campo.fill(CODIGO_PRODUTO)
    campo.press("Enter")

    # Clica em "Personalizar"
    page.wait_for_selector('button:has-text("Personalizar")', timeout=TIMEOUT)
    page.click('button:has-text("Personalizar")')
    print("Produto aberto.")


def selecionar_etiqueta_em_branco(page):
    """Clica na primeira etiqueta em branco (canvas menor, de seleção)."""
    # Aguarda os canvas aparecerem
    page.wait_for_selector("canvas.upper-canvas", timeout=TIMEOUT)
    # O canvas de seleção de etiqueta tem width="2" — é o menor
    canvas_selecao = page.locator("canvas.upper-canvas").first
    canvas_selecao.click()
    time.sleep(0.5)

    # Escolhe "APENAS UMA"
    page.wait_for_selector('button:has-text("APENAS UMA")', timeout=TIMEOUT)
    page.click('button:has-text("APENAS UMA")')
    print("Etiqueta em branco selecionada.")


def minimizar_painel_etiquetas(page):
    """Minimiza o painel 'Qual etiqueta deseja editar?' para desobstruir."""
    try:
        page.locator('svg.bi-arrows-angle-contract').click(timeout=3_000)
        time.sleep(0.3)
        print("Painel de etiquetas minimizado.")
    except Exception:
        print("Painel de etiquetas já minimizado ou não encontrado.")


def clicar_fora(page):
    """Clica no canvas principal para fechar o flutuante de edição de texto."""
    page.locator('canvas.upper-canvas').last.click()
    time.sleep(0.5)


def abrir_accordion_texto(page):
    """Garante que o accordion TEXTO está aberto e o botão Texto está visível."""
    texto_btn = page.locator('label.MuiButton-root:has-text("Texto")')

    # Se o botão já está visível, não precisa abrir o accordion
    if texto_btn.first.is_visible():
        return

    # Clica no header do accordion para expandir
    page.locator('[data-accordion-component="AccordionItemButton"]:has-text("Texto")').click()
    time.sleep(0.5)

    # Espera o botão ficar visível
    texto_btn.first.wait_for(state="visible", timeout=5_000)


def escrever_etiqueta(page, nome: str, vacina: str, via: str, primeira: bool):
    """Fluxo: clicar Texto → digitar → fonte Arial → tamanho 10 → centralizar → clicar fora → próxima."""

    if not primeira:
        # Clica fora para fechar o flutuante de edição e liberar a seta de próxima
        clicar_fora(page)
        time.sleep(0.5)

        # Avança para a próxima etiqueta
        page.click('[data-testid="ArrowForwardIosOutlinedIcon"]')
        time.sleep(1)

    # Garante que o accordion TEXTO está aberto
    abrir_accordion_texto(page)

    # Clica no botão "Texto" — abre caixa com "Digite seu texto" PRÉ-SELECIONADO
    page.locator('label.MuiButton-root:has-text("Texto")').first.click()
    time.sleep(0.8)

    # Digita conteúdo — substitui o texto pré-selecionado automaticamente
    page.keyboard.type(nome, delay=30)
    page.keyboard.press("Enter")
    page.keyboard.type(vacina, delay=30)
    page.keyboard.press("Enter")
    page.keyboard.type(via, delay=30)
    time.sleep(0.5)

    # ── Formatar no flutuante PROPRIEDADES DO OBJETO ──

    # Fonte Arial — select de fonte dentro da property bar
    try:
        fonte_select = page.locator('.property-bar-container .MuiSelect-select').first
        fonte_select.click(force=True)
        time.sleep(0.3)
        page.click('li[data-value="Arial"], [role="option"]:has-text("Arial")')
        time.sleep(0.3)
    except Exception:
        print("  Aviso: fonte Arial não alterada (pode já estar selecionada)")

    # Tamanho 10 — busca o input com value > 0 (tamanho=18) e ignora espessura (value=0)
    # Usa JS para achar o ID, depois [id="..."] em vez de #id (colons no ID quebram CSS)
    try:
        font_id = page.evaluate('''
            () => {
                const bar = document.querySelector('.property-bar-container');
                if (!bar) return null;
                const inputs = bar.querySelectorAll('input[type="number"]');
                for (const inp of inputs) {
                    if (parseInt(inp.value) > 0) return inp.id;
                }
                return null;
            }
        ''')
        if font_id:
            campo = page.locator(f'[id="{font_id}"]')
            campo.click(click_count=3, force=True)
            campo.fill(TAMANHO_FONTE)
            campo.press("Enter")
            time.sleep(0.3)
            print("  Tamanho 10 aplicado.")
        else:
            print("  Aviso: input de tamanho não encontrado")
    except Exception as e:
        print(f"  Aviso: tamanho de fonte não alterado ({e})")

    # Centralizar — SVG do botão de alinhamento centralizado
    try:
        page.locator('path[d*="M4 12.5a.5.5 0 0 1 .5-.5h7"]').locator('..').click(force=True)
        time.sleep(0.3)
        print("  Centralizado.")
    except Exception:
        print("  Aviso: centralização não aplicada")

    print(f"  OK: {nome} | {vacina} | {via}")


def aguardar_download_estavel(pasta, arquivos_antes, timeout_seg=90):
    """Monitora a pasta até aparecer um arquivo novo e estável (tamanho para de mudar).
    Retorna o caminho completo do arquivo, ou None se timeout."""
    print("Aguardando download do arquivo...")
    inicio = time.time()
    while time.time() - inicio < timeout_seg:
        time.sleep(1)
        arquivos_agora = set(os.listdir(pasta))
        novos = arquivos_agora - arquivos_antes
        # Ignora temporários do Chrome
        novos_prontos = [
            f for f in novos
            if not f.endswith(".crdownload") and not f.endswith(".tmp")
        ]
        if novos_prontos:
            # Pega o mais recente
            caminho = os.path.join(pasta, novos_prontos[0])
            # Espera o tamanho estabilizar (download completo)
            tamanho_anterior = -1
            for _ in range(30):  # até 30 segundos extras
                try:
                    tamanho_atual = os.path.getsize(caminho)
                except OSError:
                    time.sleep(1)
                    continue
                if tamanho_atual == tamanho_anterior and tamanho_atual > 0:
                    print(f"Download completo: {novos_prontos[0]} ({tamanho_atual:,} bytes)")
                    return caminho
                tamanho_anterior = tamanho_atual
                time.sleep(1)
            # Se saiu do loop, retorna de qualquer forma
            return caminho
    return None


def imprimir_e_salvar(page, context):
    """Clica fora, clica Imprimir Atual, baixa o PDF e imprime automaticamente."""

    # Fecha flutuante de edição clicando fora
    clicar_fora(page)
    time.sleep(0.5)

    # Passo 1: clica no botão "Imprimir" da barra de ferramentas (abre prévia)
    print("Abrindo prévia de impressão...")
    page.click('button:has-text("Imprimir")', force=True)
    time.sleep(3)

    print("Clicando em Imprimir Atual (download do PDF)...")
    btn_imprimir_atual = page.get_by_role("button", name="Imprimir atual")
    btn_imprimir_atual.wait_for(state="visible", timeout=TIMEOUT)

    # Registra arquivos ANTES do clique para detectar novos
    arquivos_antes = set(os.listdir(DOWNLOADS))
    caminho_pdf = os.path.join(DOWNLOADS, "etiquetas_vacinas.pdf")
    download_ok = False

    # ── Estratégia 1: expect_download do Playwright ──
    try:
        with page.expect_download(timeout=60_000) as download_info:
            btn_imprimir_atual.click(force=True)
        download = download_info.value
        print(f"Download capturado via Playwright: {download.suggested_filename}")
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
        download.save_as(caminho_pdf)
        download_ok = True
        print(f"PDF salvo em: {caminho_pdf} ({os.path.getsize(caminho_pdf):,} bytes)")
    except Exception as e:
        print(f"expect_download falhou: {e}")

    # ── Estratégia 2 (fallback): monitorar pasta Downloads ──
    if not download_ok:
        print("Usando fallback: monitorando pasta Downloads...")
        caminho_baixado = aguardar_download_estavel(DOWNLOADS, arquivos_antes, timeout_seg=90)

        if not caminho_baixado:
            print("ERRO: Nenhum arquivo novo detectado na pasta Downloads!")
            return

        # Renomeia para .pdf se necessário (arquivo com nome UUID)
        if not caminho_baixado.lower().endswith(".pdf"):
            if os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)
            os.rename(caminho_baixado, caminho_pdf)
            print(f"Arquivo renomeado: {os.path.basename(caminho_baixado)} → etiquetas_vacinas.pdf")
        else:
            caminho_pdf = caminho_baixado
            print(f"PDF já com extensão correta: {caminho_pdf}")

    print(f"PDF final: {caminho_pdf} ({os.path.getsize(caminho_pdf):,} bytes)")

    # ── Abre PDF para impressão manual (tamanho real) ──
    impressao_ok = imprimir_pdf(caminho_pdf)

    # ── Envia PDF por email como backup ──
    enviar_pdf_por_email(caminho_pdf, impressao_ok)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    # Lê a fila de pacientes do GitHub
    lista = ler_dados_github()
    total = len(lista)
    print(f"{total} etiquetas para processar.")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
            channel="chrome",
            args=["--start-minimized"]
        )
        context = browser.new_context(accept_downloads=True)
        page    = context.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            fazer_login(page)
            abrir_produto(page)
            selecionar_etiqueta_em_branco(page)
            minimizar_painel_etiquetas(page)

            for i, entrada in enumerate(lista):
                nome   = abreviar_nome(entrada.get("nome", ""))
                vacina = formatar_texto(entrada.get("vacina", ""))
                via    = formatar_texto(entrada.get("via", ""))
                print(f"[{i+1}/{total}] Escrevendo etiqueta...")
                escrever_etiqueta(page, nome, vacina, via, primeira=(i == 0))

            imprimir_e_salvar(page, context)

        except PlaywrightTimeout as e:
            print(f"\nERRO: Elemento não encontrado a tempo.\nDetalhe: {e}")
            input("Browser mantido aberto para diagnóstico. ENTER para fechar...")
            return
        except Exception as e:
            print(f"\nERRO inesperado: {e}")
            input("Browser mantido aberto para diagnóstico. ENTER para fechar...")
            return
        finally:
            browser.close()

    apagar_json_github()
    print("Processo concluído! Fila limpa, pronto para próxima semana.")


if __name__ == "__main__":
    main()
