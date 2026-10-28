# Sistema de Automação de Etiquetas de Vacinas (Pimaco)

Sistema desktop para automação de preenchimento e impressão de etiquetas de vacinas no editor online da Pimaco.

---

## 🚀 Como Funciona

1. **Leitura da Fila**: O sistema baixa a lista de pacientes e vacinas (`vacinas.json`) a partir do repositório no GitHub preenchido pelo formulário da secretaria.
2. **Automação no Navegador**: Utiliza o **Playwright** para fazer login no editor Pimaco, selecionar o modelo da etiqueta (`6187`), formatar os textos (nome abreviado, via normalizada, fonte Arial 10) e preencher as etiquetas.
3. **Impressão e Backup**:
   - Baixa o PDF gerado pelo editor.
   - Abre o PDF para impressão em tamanho real (100%).
   - Compacta o PDF em ZIP e envia um backup para o e-mail cadastrado via Gmail SMTP.
4. **Limpeza da Fila**: Remove o `vacinas.json` no GitHub para deixar a fila limpa para o próximo lote.

---

## 🔒 Segurança e Configuração (.env)

As senhas e tokens **NÃO** ficam mais no código-fonte. Elas são lidas do arquivo `.env` (que é protegido pelo `.gitignore` e nunca deve ser enviado ao GitHub).

### Configuração Inicial:

1. Se ainda não existir, crie o arquivo `.env` copiando o modelo `.env.example`:
   ```bash
   copy .env.example .env
   ```
2. Abra o `.env` e preencha suas informações:
   ```ini
   PIMACO_URL=https://editor.pimaco.com.br/APWeb
   PIMACO_EMAIL=seu_email@exemplo.com
   PIMACO_SENHA=sua_senha
   PIMACO_PRODUTO=6187

   FONTE_ETIQUETA=Arial
   TAMANHO_FONTE=10

   GITHUB_TOKEN=seu_token_github
   GITHUB_REPO=Cainho-pt-br/Vacinas
   GITHUB_FILE=vacinas.json

   GMAIL_USER=seu_email@gmail.com
   GMAIL_APP_PASS=sua_senha_de_app_gmail
   EMAIL_DESTINO=seu_email@gmail.com
   ```

---

## 📦 Instalação e Execução

### 1. Instalar dependências:
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Executar o programa:
```bash
python launcher.py
```

### 3. Gerar Executável (.exe):
```bash
pyinstaller "Etiquetas Vacinas.spec"
```
O executável será gerado na pasta `dist/`. Certifique-se de que o arquivo `.env` esteja na mesma pasta do executável ao usá-lo em outra máquina.
