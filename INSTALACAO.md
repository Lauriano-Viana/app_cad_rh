# 🚀 GUIA RÁPIDO - INSTALAÇÃO E EXECUÇÃO

## ⚡ Pré-requisitos
- Python 3.8+
- Conta Google (Gmail)
- Google Cloud Console

## 📦 Passo 1: Instalar Dependências

```bash
pip install -r requirements.txt
```

## 🔐 Passo 2: Configurar Google Cloud

### 2.1 Criar Projeto e Credenciais

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em "Selecionar um projeto" → "NOVO PROJETO"
3. Dê um nome: "RH-Funcionarios" (ou similar)
4. Ative as APIs:
   - Acesse "APIs e Serviços" → "Biblioteca"
   - Busque por "Google Sheets API" → Clique → "Ativar"
   - Busque por "Google Drive API" → Clique → "Ativar"

### 2.2 Criar Conta de Serviço

1. Em "APIs e Serviços" → "Credenciais"
2. Clique em "Criar Credenciais" → "Conta de Serviço"
3. Preencha o nome: "rh-app"
4. Clique em "Criar"
5. Clique em "Continuar" (sem adicionar funções por enquanto)
6. Clique em "Continuar" e depois "Concluído"

### 2.3 Gerar Chave Privada

1. Em "Contas de Serviço", clique na conta criada
2. Acesse a aba "Chaves"
3. Clique em "Adicionar chave" → "Criar nova chave"
4. Escolha "JSON"
5. Clique em "Criar" - um arquivo JSON será baixado
6. **Guarde este arquivo com segurança!**

## 📊 Passo 3: Criar Planilha Google Sheets

1. Acesse [Google Sheets](https://sheets.google.com)
2. Clique em "Criar" → "Planilha em branco"
3. Dê um nome: "Cadastro de Funcionários"
4. Copie o ID da planilha na URL:
   ```
   https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
   ```

## 📁 Passo 4: Criar Pasta no Google Drive

1. Acesse [Google Drive](https://drive.google.com)
2. Clique em "Novo" → "Pasta"
3. Nomeie: "Comprovantes RH"
4. Copie o ID da pasta na URL:
   ```
   https://drive.google.com/drive/folders/[FOLDER_ID]
   ```

## 🔧 Passo 5: Configurar Credenciais

### Opção A: Usando o script auxiliar (RECOMENDADO)

```bash
python setup_credentials.py
```

Siga as instruções do script. Ele pedirá:
- Caminho do arquivo JSON das credenciais
- ID da Planilha Google
- ID da Pasta do Drive

### Opção B: Manual

Edite `.streamlit/secrets.toml` e preencha com seus dados:

```toml
google_sheet_id = "COLE_O_SHEET_ID_AQUI"
google_drive_folder_id = "COLE_O_FOLDER_ID_AQUI"

[google_service_account]
type = "service_account"
project_id = "seu-projeto-id"
private_key_id = "sua-chave-id"
private_key = "sua-chave-privada-aqui"
client_email = "seu-email@seu-projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/seu-email%40seu-projeto.iam.gserviceaccount.com"
```

## 🤝 Passo 6: Compartilhar com Conta de Serviço

1. Abra a **Planilha Google Sheets**
2. Clique em "Compartilhar"
3. Cole o email da conta de serviço (de `secrets.toml` - `client_email`)
4. Dê permissão de "Editor"

5. Acesse a **Pasta no Google Drive**
6. Clique em "Compartilhar"
7. Cole o mesmo email
8. Dê permissão de "Editor"

## ▶️ Passo 7: Executar a Aplicação

```bash
streamlit run app.py
```

A app abrirá automaticamente em `http://localhost:8501`

## ✅ Verificação

Para verificar se tudo está configurado:

```bash
python setup_credentials.py --verify
```

## 🎉 Pronto!

Agora você pode:
- ✅ Cadastrar novos funcionários
- ✅ Os dados são salvos na Planilha Google automaticamente
- ✅ Os comprovantes são salvos no Google Drive
- ✅ Consultar todos os cadastros na aba "Consultar Dados"

## ❓ Problemas Comuns?

### "Credenciais não configuradas"
- Verifique se `.streamlit/secrets.toml` existe e está preenchido

### "Erro ao salvar no Google Sheets"
- A conta de serviço não tem permissão na planilha
- Compartilhe a planilha com o email da conta de serviço

### "Erro ao fazer upload"
- A conta de serviço não tem permissão na pasta
- Compartilhe a pasta com o email da conta de serviço

---

📞 **Precisa de ajuda?** Verifique o README.md para mais detalhes.
