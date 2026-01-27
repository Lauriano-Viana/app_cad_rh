#!/usr/bin/env python3
"""
Script auxiliar para configurar as credenciais do Google Cloud
Execute este script para ajudar a configurar o secrets.toml
"""

import os
import json
from pathlib import Path

def create_secrets_template():
    """Cria template do secrets.toml"""
    
    secrets_dir = Path(".streamlit")
    secrets_file = secrets_dir / "secrets.toml"
    
    print("\n" + "="*60)
    print("⚙️  CONFIGURADOR DE CREDENCIAIS - GOOGLE CLOUD")
    print("="*60 + "\n")
    
    # Verificar se arquivo já existe
    if secrets_file.exists():
        resp = input("❓ O arquivo secrets.toml já existe. Deseja sobrescrever? (s/n): ").strip().lower()
        if resp != 's':
            print("❌ Operação cancelada.")
            return
    
    print("\n📌 INSTRUÇÕES:")
    print("1. Acesse https://console.cloud.google.com/")
    print("2. Crie um novo projeto")
    print("3. Ative as APIs: Google Sheets API e Google Drive API")
    print("4. Crie uma Conta de Serviço")
    print("5. Gere uma chave privada (JSON)")
    print("6. Baixe o arquivo JSON\n")
    
    # Coletar informações
    json_path = input("📁 Caminho para o arquivo JSON das credenciais: ").strip()
    
    if not os.path.exists(json_path):
        print(f"❌ Arquivo não encontrado: {json_path}")
        return
    
    try:
        with open(json_path, 'r') as f:
            credentials = json.load(f)
    except json.JSONDecodeError:
        print("❌ Arquivo JSON inválido")
        return
    
    sheet_id = input("\n📊 ID da Planilha Google Sheets (está na URL): ").strip()
    drive_folder_id = input("📁 ID da Pasta Google Drive (está na URL): ").strip()
    
    # Criar conteúdo do secrets.toml
    secrets_content = f'''# Configuração do Google Cloud para Cadastro de Funcionários
# Gerado automaticamente - NÃO COMMITAR ESTE ARQUIVO

google_sheet_id = "{sheet_id}"
google_drive_folder_id = "{drive_folder_id}"

[google_service_account]
type = "{credentials.get('type', 'service_account')}"
project_id = "{credentials.get('project_id', '')}"
private_key_id = "{credentials.get('private_key_id', '')}"
private_key = """{credentials.get('private_key', '')}"""
client_email = "{credentials.get('client_email', '')}"
client_id = "{credentials.get('client_id', '')}"
auth_uri = "{credentials.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth')}"
token_uri = "{credentials.get('token_uri', 'https://oauth2.googleapis.com/token')}"
auth_provider_x509_cert_url = "{credentials.get('auth_provider_x509_cert_url', 'https://www.googleapis.com/oauth2/v1/certs')}"
client_x509_cert_url = "{credentials.get('client_x509_cert_url', '')}"
'''
    
    # Garantir que diretório existe
    secrets_dir.mkdir(exist_ok=True)
    
    # Salvar arquivo
    with open(secrets_file, 'w', encoding='utf-8') as f:
        f.write(secrets_content)
    
    print("\n✅ Arquivo secrets.toml criado com sucesso!")
    print(f"📍 Localização: {secrets_file.absolute()}")
    
    print("\n⚠️  PRÓXIMOS PASSOS:")
    print("1. Abra a planilha Google Sheets")
    print("2. Clique em 'Compartilhar'")
    print(f"3. Adicione o email: {credentials.get('client_email')}")
    print("4. Dê permissão de Editor")
    print("5. Repita o processo com a pasta do Google Drive")
    print("\n✨ Depois execute: streamlit run app.py")
    print("="*60 + "\n")

def verify_installation():
    """Verifica se todas as dependências estão instaladas"""
    print("\n🔍 Verificando dependências...\n")
    
    required_packages = [
        'streamlit',
        'pandas',
        'gspread',
        'google',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Instale os pacotes faltantes:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("\n✅ Todas as dependências estão instaladas!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_installation()
    else:
        verify_installation()
        print("\n")
        create_secrets_template()
