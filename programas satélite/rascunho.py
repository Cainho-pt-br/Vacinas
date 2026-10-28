import pyautogui
import time
import os
import pandas as pd
import subprocess
from glob import glob
import re 
import tkinter as tk
from threading import Timer

# Parâmetros de controle
tempo_maximo_espera = 60  # Tempo máximo de espera para o login (em segundos)
intervalo_verificacao = 3  # Intervalo de verificação (em segundos)
tentativas_maximas = 3  # Número máximo de tentativas de login

# Função para maximizar a janela ativa
def maximizar_janela():
    pyautogui.hotkey("win", "up")  # Atalho do Windows para maximizar a janela ativa
    time.sleep(1.5)  # Pausa adicional para garantir que a maximização seja concluída

# Função que verifica se o login foi concluído com base no retângulo verde
def verificar_login_concluido():
    caminho_imagem = r'C:\Users\Clineo\OneDrive\Documentos\Programa\retangulo.png'
    
    # Verifica se o arquivo existe no caminho especificado
    if not os.path.exists(caminho_imagem):
        print(f"Erro: o arquivo '{caminho_imagem}' não foi encontrado.")
        return False

    # Tenta localizar a imagem na tela com o OpenCV
    indicador = pyautogui.locateOnScreen(caminho_imagem, confidence=0.8)
    if indicador:
        print("Indicador de login detectado!")
        return True
    return False

# Função que tenta fazer login e aguarda até o sucesso ou timeout
def tentar_login():
    tentativas = 0
    while tentativas < tentativas_maximas:
        print(f"Tentativa de login {tentativas + 1} de {tentativas_maximas}")

        # Abre uma nova janela anônima no Chrome
        subprocess.Popen(['chrome', '--new-window', '--incognito', 'https://www.pimaco.com.br/apweb'])
        time.sleep(3)

        # Maximiza a janela após a abertura
        maximizar_janela()

        # Acessa o site e insere o login e a senha
        pyautogui.press("tab")
        pyautogui.write("clicneorosa@gmail.com")
        pyautogui.press("tab")
        pyautogui.write("010797#")
        pyautogui.press("enter")

        # Tempo decorrido para a tentativa atual
        tempo_decorrido = 0

        # Loop de verificação do login
        while tempo_decorrido < tempo_maximo_espera:
            if verificar_login_concluido():
                print("Login realizado com sucesso!")
                return True  # Sai da função se o login for bem-sucedido
            
            time.sleep(intervalo_verificacao)  # Aguarda antes de verificar novamente
            tempo_decorrido += intervalo_verificacao

        # Se o login não ocorreu, aumenta a tentativa e espera um pouco antes da próxima
        tentativas += 1
        print("Login não foi concluído. Tentando novamente em alguns segundos...")
        time.sleep(5)  # Espera antes de uma nova tentativa

    print("Erro: Não foi possível fazer login após várias tentativas.")
    return False  # Retorna False se todas as tentativas falharem

# Executa o login e só prossegue se bem-sucedido
if tentar_login():
    print("Iniciando o restante do programa com PyAutoGUI.")
else:
    print("Falha no login. O programa será encerrado.")

pyautogui.click(x=376, y=190)
pyautogui.write("6187")
pyautogui.click(x=1196, y=378)
pyautogui.click(x=406, y=413)
time.sleep(1.5)
pyautogui.click(x=1269, y=364)

# Passo 1: Especifica o caminho para o diretório dos arquivos .xlsx
diretorio_dos_arquivos = "C:/Users/Clineo/Downloads"  # Substitua pelo caminho correto

# Passo 2: Verifica se o diretório existe
if not os.path.exists(diretorio_dos_arquivos):
    raise FileNotFoundError(f"O diretório especificado não existe: {diretorio_dos_arquivos}")

# Passo 3: Encontra todos os arquivos .xlsx no diretório
arquivos_xlsx = glob(os.path.join(diretorio_dos_arquivos, "*.xlsx"))
print("Arquivos encontrados:", arquivos_xlsx)  # Exibe os arquivos .xlsx encontrados

# Passo 4: Verifica se há algum arquivo .xlsx encontrado
if not arquivos_xlsx:
    raise FileNotFoundError("Nenhum arquivo .xlsx encontrado no diretório especificado.")

# Passo 5: Seleciona o arquivo mais recente
arquivo_mais_recente = max(arquivos_xlsx, key=os.path.getmtime)
print("Arquivo mais recente encontrado:", arquivo_mais_recente)

# Passo 6: Carrega o arquivo mais recente
try:
    tabela = pd.read_excel(arquivo_mais_recente)
    print("Arquivo carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o arquivo: {e}")
    raise

# Passo 7: Normaliza os nomes das colunas (para o caso de nomes inconsistentes)
tabela.columns = tabela.columns.str.strip().str.lower()

# Verifica as colunas para garantir que estão como esperado
print("Colunas na tabela:", tabela.columns.tolist())

# Passo 8: Localiza as colunas específicas
padrao_coluna_vacina = re.compile(r'\bvacinas?\b', re.IGNORECASE)
padrao_coluna_obs = re.compile(r'\bobs\b|\bobservação\b', re.IGNORECASE)
padrao_coluna_nome = re.compile(r'\bnomes?\b', re.IGNORECASE)  # Adiciona verificação para "nome" ou "nomes"

coluna_vacina = None
coluna_obs = None
coluna_nome = None

# Identifica as colunas exatas
for coluna in tabela.columns:
    if padrao_coluna_vacina.search(coluna) and not coluna_vacina:
        coluna_vacina = coluna
    if padrao_coluna_obs.search(coluna) and not coluna_obs:
        coluna_obs = coluna
    if padrao_coluna_nome.search(coluna) and not coluna_nome:
        coluna_nome = coluna

# Passo 9: Verifica se a coluna de vacinas foi encontrada e processa os dados
if coluna_vacina:
    print(f"Coluna de vacinas encontrada: {coluna_vacina}")
    if coluna_obs:
        print(f"Coluna de observação encontrada: {coluna_obs}")
    if coluna_nome:
        print(f"Coluna de nome encontrada: {coluna_nome}")

    # Passo 10: Processa cada linha da tabela e insere informações com PyAutoGUI
    for index, row in tabela.iterrows():
        nome = row[coluna_nome] if coluna_nome else "N/A"  # Usa a coluna "nome" ou "nomes" localizada
        vacina = row[coluna_vacina]
        via = row['via'] if 'via' in tabela.columns else "N/A"
        
        # Verifica se há informação em obs e constrói o texto de saída para via
        if coluna_obs and pd.notna(row[coluna_obs]):  # Verifica se "obs" existe e não está vazio
            observacao = f"{via} - {row[coluna_obs]}"  # Adiciona a observação após "via"
        else:
            observacao = via  # Apenas "via" sem o "-"

        # Exibe ou insere as informações como desejado
        print(f"Nome: {nome}, Vacina: {vacina}, Via e Observação: {observacao}")

    pyautogui.click(x=119, y=350) #clique inicial de texto de ada etiqueta 

    pyautogui.click(x=783, y=360)
    pyautogui.hotkey("ctrl","a")
    pyautogui.write("9")
    pyautogui.click(x=943, y=354)
    pyautogui.click(x=508, y=351)
    pyautogui.click(x=445, y=323)

    pyautogui.click(x=676, y=459) #(digite seu texto)
    pyautogui.hotkey('ctrl', 'a') 

    pyautogui.write(f"{nome}")
    pyautogui.press("enter")

    pyautogui.write(f"{vacina}")
    pyautogui.press("enter")

    if observacao:  # Se houver uma observação
        pyautogui.write(f"{via} - {observacao}")
    else:  # Sem observação, escreve apenas via
        pyautogui.write(via)
    pyautogui.click(x=800, y=248)
    time.sleep(2)
    pyautogui.click(x=770, y=248)

pyautogui.click(x=1176, y=167)
pyautogui.click(x=1043, y=652)

# Caminho da pasta de downloads do usuário
downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

# Função para abrir o último arquivo PDF baixado
def abrir_ultimo_pdf():
    try:
        # Lista todos os arquivos na pasta de downloads e filtra por PDFs
        arquivos = [os.path.join(downloads_folder, f) for f in os.listdir(downloads_folder) if f.endswith('.pdf')]
        
        if not arquivos:
            print("Nenhum arquivo PDF encontrado na pasta de downloads.")
            return
        
        # Ordena os arquivos por data de modificação (do mais recente para o mais antigo)
        arquivos.sort(key=os.path.getmtime, reverse=True)
        
        ultimo_pdf = arquivos[0]  # Pega o arquivo PDF mais recente
        
        print(f"Abrindo o arquivo: {ultimo_pdf}")  # Debug: mostra o nome do arquivo sendo aberto
        
        # Abre o arquivo PDF
        subprocess.Popen([ultimo_pdf], shell=True)  
        
    except Exception as e:
        print(f"Erro ao abrir o arquivo PDF: {e}")

# Função para aguardar o download do novo PDF
def aguardar_novo_pdf():
    arquivos_iniciais = set(os.listdir(downloads_folder))
    
    while True:
        time.sleep(1)  # Verifica a cada segundo
        arquivos_atualizados = set(os.listdir(downloads_folder))
        novos_arquivos = arquivos_atualizados - arquivos_iniciais
        
        # Filtra apenas arquivos PDF
        novos_pdfs = [f for f in novos_arquivos if f.endswith('.pdf')]
        
        if novos_pdfs:
            print("Novo PDF detectado.")
            break

# Passo 1: Realiza o clique que inicia o download do PDF
pyautogui.click(x=1043, y=652)

# Passo 2: Aguardar o novo PDF ser baixado
aguardar_novo_pdf()

# Passo 3: Abrir o último arquivo PDF
abrir_ultimo_pdf()

time.sleep(5)
pyautogui.click(x=1298, y=110)
time.sleep(7)
pyautogui.click(x=1021, y=652) #clica para imprimir de verdade

from PIL import Image, ImageTk, ImageEnhance
import sys

def mostrar_janela_finalizada():
    root = tk.Tk()
    root.title("Processo Finalizado")

    # Dimensões e centralização da janela
    janela_largura = 800
    janela_altura = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    pos_x = (screen_width // 2) - (janela_largura // 2)
    pos_y = (screen_height // 2) - (janela_altura // 2)
    root.geometry(f"{janela_largura}x{janela_altura}+{pos_x}+{pos_y}")

    # Configurar a janela para estar sempre no topo
    root.attributes('-topmost', True)
    root.resizable(False, False)

    # Configuração do Canvas
    root.config(bg="#F0F0F0")
    canvas = tk.Canvas(root, width=janela_largura, height=janela_altura, bg="#F0F0F0", highlightthickness=0)
    canvas.pack()

    # Caminho da imagem (considerando o ambiente do executável)
    if getattr(sys, 'frozen', False):  # Se estiver rodando como executável
        caminho_imagem = os.path.join(sys._MEIPASS, "Doc.png")
    else:  # Se estiver rodando como script
        caminho_imagem = "Doc.png"

    # Carregar e escurecer a imagem
    try:
        img = Image.open(caminho_imagem)
        enhancer = ImageEnhance.Brightness(img)
        img_dark = enhancer.enhance(0.6)  # Escurece a imagem
        img_tk = ImageTk.PhotoImage(img_dark)
        canvas.create_image(janela_largura // 2, janela_altura // 2, image=img_tk)
    except Exception as e:
        print("Erro ao carregar a imagem:", e)
        return

    # Texto grifado sobre a imagem
    texto_x = janela_largura // 2
    texto_y = janela_altura // 2
    canvas.create_text(texto_x + 1, texto_y + 1, text="As etiquetas das vacinas foram impressas!",
                       font=("Arial", 24, "bold"), fill="black")
    canvas.create_text(texto_x, texto_y, text="As etiquetas das vacinas foram impressas!",
                       font=("Arial", 24, "bold"), fill="yellow")

    # Botão de fechamento
    button = tk.Button(root, text="Fechar", font=("Arial", 12), command=root.quit, bg="#4CAF50", fg="white")
    button.pack(pady=10)

    root.mainloop()

# Chama a função para exibir a janela
mostrar_janela_finalizada()


