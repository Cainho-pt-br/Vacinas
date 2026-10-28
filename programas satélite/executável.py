import os
import winshell

# Nome do script Python principal e ícone
nome_script = "Vacinas.py"  # Nome do script principal
nome_icone = "vacina.ico"   # Ícone para o executável

# Caminho da área de trabalho para salvar o executável
caminho_area_trabalho = winshell.desktop()

# Comando do PyInstaller
comando = (
    f'python -m PyInstaller --onefile --windowed --icon={nome_icone} '
    f'--add-data="retangulo.png;." '  # Adiciona a imagem de login ao executável
    f'--add-data="Doc.png;." '        # Adiciona a imagem Doc.png ao executável
    f'--distpath="{caminho_area_trabalho}" {nome_script}'
)

# Executa o comando para criar o executável
os.system(comando)

print("Novo executável gerado com sucesso na área de trabalho!")




