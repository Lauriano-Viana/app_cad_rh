# 📋 Sistema de Cadastro de Funcionários - Streamlit

Aplicação completa para cadastro de funcionários com integração automática com Google Sheets e Google Drive.

## 🎯 Funcionalidades

✅ **Formulário Completo** com todos os 27 campos solicitados
✅ **Integração Google Sheets** - Dados salvos automaticamente em planilha
✅ **Upload Google Drive** - Comprovante de residência salvo em pasta do Drive
✅ **Validações** - CPF, E-mail, Telefone
✅ **Consulta de Dados** - Visualização e download dos cadastros
✅ **Interface Responsiva** - Design moderno com Streamlit

## 📦 Campos de Cadastro

- Data/Hora Cadastro
- Nome Completo
- CPF
- Endereço
- E-mail
- Telefone
- Idade
- Data de Nascimento
- Diretoria
- Possui Comorbidade
- Descrição Comorbidade
- Tipo Sanguíneo
- Possui Plano de Saúde
- Nome do Plano
- Estado Civil
- Nome Cônjuge/Companheiro(a)
- Idade Cônjuge/Companheiro(a)
- Possui Filhos
- Quantidade de Filhos
- Contato Emergência 1 (Nome, Telefone, Parentesco)
- Contato Emergência 2 (Nome, Telefone, Parentesco)
- Comprovante de Residência (PDF)

## 🚀 Instalação

### 1. Clonar/Baixar o Repositório
```bash
cd c:\Users\Lauriano\Documents\documentos-seres\TI\app_cad_rh
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar Google Cloud
#### Passo A: Criar Projeto no Google Cloud
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative as APIs:
   - Google Sheets API
   - Google Drive API

#### Passo B: Criar Conta de Serviço
1. Vá para "Contas de Serviço"
2. Crie uma nova conta de serviço
3. Gere uma chave privada (JSON)
4. Baixe o arquivo JSON

#### Passo C: Criar Planilha Google
1. Acesse [Google Sheets](https://sheets.google.com)
2. Crie uma nova planilha
3. Adicione os nomes das colunas na primeira linha (ou deixe em branco que a app cria)
4. Copie o ID da planilha (está na URL)

#### Passo D: Criar Pasta no Google Drive
1. Acesse [Google Drive](https://drive.google.com)
2. Crie uma pasta para guardar os comprovantes
3. Copie o ID da pasta (está na URL quando entra na pasta)

### 4. Configurar Credenciais
Edite `.streamlit/secrets.toml` e preencha:

```toml
google_sheet_id = "SEU_SHEET_ID"
google_drive_folder_id = "SEU_FOLDER_ID"

[google_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "sua-chave-id"
private_key = "sua-chave-privada"
client_email = "seu-email@seu-projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/seu-email%40seu-projeto.iam.gserviceaccount.com"
```

### 5. Compartilhar Recursos com Conta de Serviço
1. Abra a planilha Google Sheets
2. Clique em "Compartilhar"
3. Adicione o email da conta de serviço com permissão de editor
4. Faça o mesmo com a pasta do Google Drive

## ▶️ Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

## 📝 Modo de Uso

### 1. Novo Cadastro (Aba 1)
- Preencha todos os campos obrigatórios (marcados com *)
- Faça upload do comprovante de residência (PDF)
- Clique em "Cadastrar Funcionário"
- Os dados são salvos automaticamente no Google Sheets
- O comprovante é enviado para o Google Drive

### 2. Consultar Dados (Aba 2)
- Visualize todos os cadastros realizados
- Exporte como CSV clicando em "Baixar como CSV"

## 🔒 Segurança

- Credenciais nunca são commitadas no repositório
- Use `.streamlit/secrets.toml` (já ignorado no .gitignore)
- Adicione `.streamlit/secrets.toml` ao `.gitignore`

## 🐛 Troubleshooting

### Erro: "Credenciais não configuradas"
- Verifique se `.streamlit/secrets.toml` está preenchido corretamente
- Certifique-se que o JSON das credenciais está válido

### Erro: "Google Sheets não configurado"
- Verifique se `google_sheet_id` está em `secrets.toml`
- Compartilhe a planilha com o email da conta de serviço

### Erro: "Erro ao fazer upload"
- Verifique se `google_drive_folder_id` está em `secrets.toml`
- Compartilhe a pasta do Drive com o email da conta de serviço

## 📚 Estrutura de Arquivos

```
app_cad_rh/
├── app.py                    # Aplicação principal
├── requirements.txt          # Dependências Python
├── README.md                 # Este arquivo
├── .streamlit/
│   ├── config.toml          # Configuração do Streamlit
│   └── secrets.toml         # Credenciais (NÃO COMMITAR)
└── .gitignore               # Ignore arquivos sensíveis
```

## 🤝 Contribuições

Para melhorias ou correções, faça um pull request.

## 📞 Suporte

Para dúvidas ou problemas, entre em contato.

---

**Desenvolvido com ❤️ usando Streamlit**
