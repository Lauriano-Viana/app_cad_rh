import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo

FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")
import gspread
from google.oauth2.service_account import Credentials
import json
import re

# Configuração da página
st.set_page_config(
    page_title="Cadastro de Funcionários",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONFIGURAÇÃO DO GOOGLE DRIVE E SHEETS ====================

def init_google_credentials():
    """Inicializa as credenciais do Google"""
    try:
        # Tenta carregar do secrets do Streamlit
        credentials_dict = st.secrets["google_service_account"]
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        return credentials
    except (KeyError, FileNotFoundError):
        st.warning("⚠️ Credenciais do Google não configuradas. Configure em .streamlit/secrets.toml")
        return None

def get_google_sheet_client(credentials):
    """Obtém cliente do Google Sheets"""
    if credentials is None:
        return None
    return gspread.authorize(credentials)

# ==================== FUNÇÕES AUXILIARES ====================

def validar_cpf(cpf):
    """Valida CPF com cálculo dos dígitos verificadores"""
    cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    # Rejeita sequências com todos os dígitos iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False
    # Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    if int(cpf[9]) != digito1:
        return False
    # Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    if int(cpf[10]) != digito2:
        return False
    return True

def validar_email(email):
    """Valida formato de e-mail com regex"""
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))

def validar_telefone(telefone):
    """Valida telefone no formato brasileiro (DDD + 8 ou 9 dígitos)"""
    telefone = re.sub(r'[\s()\-\.+]', '', telefone)
    # Aceita formato com ou sem código do país (55)
    if telefone.startswith('55') and len(telefone) > 11:
        telefone = telefone[2:]
    # DDD (2 dígitos) + número (8 ou 9 dígitos) = 10 ou 11 dígitos
    if not telefone.isdigit() or len(telefone) not in (10, 11):
        return False
    ddd = int(telefone[:2])
    if ddd < 11 or ddd > 99:
        return False
    # Celular (9 dígitos) deve começar com 9
    if len(telefone) == 11 and telefone[2] != '9':
        return False
    return True

def formatar_cpf(cpf):
    """Formata CPF como XXX.XXX.XXX-XX"""
    cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')
    if len(cpf) == 11 and cpf.isdigit():
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

def formatar_telefone(telefone):
    """Formata telefone como (XX) XXXXX-XXXX ou (XX) XXXX-XXXX"""
    tel = re.sub(r'[\s()\-\.+]', '', telefone)
    if tel.startswith('55') and len(tel) > 11:
        tel = tel[2:]
    if tel.isdigit():
        if len(tel) == 11:
            return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
        elif len(tel) == 10:
            return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"
    return telefone

def criar_dicionario_formulario(form_data):
    """Cria dicionário com dados do formulário"""
    return {
        'Data/Hora Cadastro': form_data['data_hora'],
        'Nome Completo': form_data['nome'],
        'CPF': form_data['cpf'],
        'Endereço': form_data['endereco'],
        'E-mail': form_data['email'],
        'Telefone': form_data['telefone'],
        'Idade': form_data['idade'],
        'Data de Nascimento': form_data['data_nascimento'],
        'Diretoria': form_data['diretoria'],
        'Possui Comorbidade': form_data['comorbidade'],
        'Descrição Comorbidade': form_data['desc_comorbidade'],
        'Tipo Sanguíneo': form_data['tipo_sanguineo'],
        'Possui Plano de Saúde': form_data['plano_saude'],
        'Nome do Plano': form_data['nome_plano'],
        'Estado Civil': form_data['estado_civil'],
        'Nome Cônjuge/Companheiro(a)': form_data['nome_conjuge'],
        'Idade Cônjuge/Companheiro(a)': form_data['idade_conjuge'],
        'Possui Filhos': form_data['possui_filhos'],
        'Quantidade de Filhos': form_data['qtd_filhos'],
        'Contato Emergência 1 - Nome': form_data['emerg1_nome'],
        'Contato Emergência 1 - Telefone': form_data['emerg1_telefone'],
        'Contato Emergência 1 - Parentesco': form_data['emerg1_parentesco'],
        'Contato Emergência 2 - Nome': form_data['emerg2_nome'],
        'Contato Emergência 2 - Telefone': form_data['emerg2_telefone'],
        'Contato Emergência 2 - Parentesco': form_data['emerg2_parentesco']
    }

# ==================== INTERFACE PRINCIPAL ====================

def main():
    st.markdown("<h1 class='main-header'>📋 Sistema de Cadastro de Funcionários</h1>", unsafe_allow_html=True)
    
    # Tabs para organizar a interface
    tab1, tab2 = st.tabs(["➕ Novo Cadastro", "📊 Consultar Dados"])
    
    with tab1:
        st.subheader("Formulário de Cadastro")
        
        # Inicializa credenciais
        credentials = init_google_credentials()
        
        with st.form("formulario_cadastro", clear_on_submit=False):
            
            # ===== SEÇÃO 1: DADOS PESSOAIS =====
            st.markdown("### 👤 Dados Pessoais")
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome Completo *", key="nome")
                cpf = st.text_input("CPF *", key="cpf", max_chars=14, placeholder="000.000.000-00")
                email = st.text_input("E-mail *", key="email")
                telefone = st.text_input("Telefone *", key="telefone", max_chars=15, placeholder="(00) 00000-0000")
            
            with col2:
                idade = st.number_input("Idade *", min_value=18, max_value=100, key="idade")
                data_nascimento = st.date_input("Data de Nascimento *", key="data_nascimento", format="DD/MM/YYYY")
                endereco = st.text_area("Endereço *", key="endereco", height=80)
            
            # ===== SEÇÃO 2: INFORMAÇÕES PROFISSIONAIS =====
            st.markdown("### 🏢 Informações Profissionais")
            diretoria = st.selectbox(
                "Diretoria *",
                ["Selecione uma opção", "Diretoria Financeira", "Diretoria de Recursos Humanos", 
                 "Diretoria Operacional", "Diretoria de Tecnologia", "Diretoria Administrativa"],
                key="diretoria"
            )
            
            # ===== SEÇÃO 3: INFORMAÇÕES DE SAÚDE =====
            st.markdown("### 🏥 Informações de Saúde")
            col1, col2 = st.columns(2)
            
            with col1:
                comorbidade = st.radio("Possui Comorbidade? *", ["Não", "Sim"], key="comorbidade")
                if comorbidade == "Sim":
                    desc_comorbidade = st.text_area("Descreva a(s) Comorbidade(s)", height=100, key="desc_comorbidade")
                else:
                    desc_comorbidade = ""
                
                tipo_sanguineo = st.selectbox(
                    "Tipo Sanguíneo *",
                    ["Selecione", "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
                    key="tipo_sanguineo"
                )
            
            with col2:
                plano_saude = st.radio("Possui Plano de Saúde? *", ["Não", "Sim"], key="plano_saude")
                if plano_saude == "Sim":
                    nome_plano = st.text_input("Nome do Plano", key="nome_plano")
                else:
                    nome_plano = ""
            
            # ===== SEÇÃO 4: ESTADO CIVIL E FAMÍLIA =====
            st.markdown("### 👨‍👩‍👧‍👦 Estado Civil e Família")
            col1, col2 = st.columns(2)
            
            with col1:
                estado_civil = st.selectbox(
                    "Estado Civil *",
                    ["Selecione", "Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"],
                    key="estado_civil"
                )
                
                if estado_civil in ["Casado(a)", "União Estável"]:
                    nome_conjuge = st.text_input("Nome Cônjuge/Companheiro(a)", key="nome_conjuge")
                    idade_conjuge = st.number_input("Idade Cônjuge/Companheiro(a)", min_value=0, key="idade_conjuge")
                else:
                    nome_conjuge = ""
                    idade_conjuge = 0
            
            with col2:
                possui_filhos = st.radio("Possui Filhos? *", ["Não", "Sim"], key="possui_filhos")
                if possui_filhos == "Sim":
                    qtd_filhos = st.number_input("Quantidade de Filhos", min_value=1, key="qtd_filhos")
                else:
                    qtd_filhos = 0
            
            # ===== SEÇÃO 5: CONTATOS DE EMERGÊNCIA =====
            st.markdown("### 📞 Contatos de Emergência")
            
            st.write("**Contato de Emergência 1 ***")
            col1, col2, col3 = st.columns(3)
            with col1:
                emerg1_nome = st.text_input("Nome", key="emerg1_nome", placeholder="Nome")
            with col2:
                emerg1_telefone = st.text_input("Telefone", key="emerg1_telefone", max_chars=15, placeholder="(00) 00000-0000")
            with col3:
                emerg1_parentesco = st.text_input("Parentesco", key="emerg1_parentesco", placeholder="Parentesco")

            st.write("**Contato de Emergência 2**")
            col1, col2, col3 = st.columns(3)
            with col1:
                emerg2_nome = st.text_input("Nome ", key="emerg2_nome", placeholder="Nome")
            with col2:
                emerg2_telefone = st.text_input("Telefone ", key="emerg2_telefone", max_chars=15, placeholder="(00) 00000-0000")
            with col3:
                emerg2_parentesco = st.text_input("Parentesco ", key="emerg2_parentesco", placeholder="Parentesco")
            
            # ===== BOTÃO SUBMIT =====
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submitted = st.form_submit_button("✅ Cadastrar Funcionário", use_container_width=True)
            
            with col2:
                st.form_submit_button("🔄 Limpar Formulário", use_container_width=True)
            
            # ===== PROCESSAMENTO DO FORMULÁRIO =====
            if submitted:
                # Validações
                erros = []
                
                if not nome or nome.strip() == "":
                    erros.append("Nome completo é obrigatório")
                if not cpf or not validar_cpf(cpf):
                    erros.append("CPF inválido. Verifique se digitou os 11 dígitos corretamente (formato: XXX.XXX.XXX-XX)")
                if not email or not validar_email(email):
                    erros.append("E-mail inválido. Use o formato: exemplo@dominio.com")
                if not telefone or not validar_telefone(telefone):
                    erros.append("Telefone inválido. Use o formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX")
                if not endereco or endereco.strip() == "":
                    erros.append("Endereço é obrigatório")
                if diretoria == "Selecione uma opção":
                    erros.append("Diretoria é obrigatória")
                if tipo_sanguineo == "Selecione":
                    erros.append("Tipo sanguíneo é obrigatório")
                if estado_civil == "Selecione":
                    erros.append("Estado civil é obrigatório")
                if comorbidade == "Sim" and not desc_comorbidade:
                    erros.append("Descreva a comorbidade se respondeu sim")
                if plano_saude == "Sim" and not nome_plano:
                    erros.append("Nome do plano é obrigatório se respondeu sim")
                if not emerg1_nome or not emerg1_telefone:
                    erros.append("Contato de emergência 1 incompleto")
                
                if erros:
                    st.error("❌ Erros encontrados:")
                    for erro in erros:
                        st.write(f"• {erro}")
                else:
                    with st.spinner("Processando cadastro..."):
                        try:
                            # Preparar dados para enviar ao Google Sheets
                            form_data = {
                                'data_hora': datetime.now(FUSO_BRASIL).strftime("%d/%m/%Y %H:%M:%S"),
                                'nome': nome,
                                'cpf': formatar_cpf(cpf),
                                'endereco': endereco,
                                'email': email,
                                'telefone': formatar_telefone(telefone),
                                'idade': idade,
                                'data_nascimento': data_nascimento.strftime("%d/%m/%Y"),
                                'diretoria': diretoria,
                                'comorbidade': comorbidade,
                                'desc_comorbidade': desc_comorbidade,
                                'tipo_sanguineo': tipo_sanguineo,
                                'plano_saude': plano_saude,
                                'nome_plano': nome_plano,
                                'estado_civil': estado_civil,
                                'nome_conjuge': nome_conjuge,
                                'idade_conjuge': idade_conjuge,
                                'possui_filhos': possui_filhos,
                                'qtd_filhos': qtd_filhos,
                                'emerg1_nome': emerg1_nome,
                                'emerg1_telefone': formatar_telefone(emerg1_telefone),
                                'emerg1_parentesco': emerg1_parentesco,
                                'emerg2_nome': emerg2_nome,
                                'emerg2_telefone': formatar_telefone(emerg2_telefone),
                                'emerg2_parentesco': emerg2_parentesco
                            }
                            
                            # Enviar para Google Sheets
                            if credentials:
                                gc = get_google_sheet_client(credentials)
                                SHEET_ID = st.secrets.get("google_sheet_id", "")
                                
                                if SHEET_ID and gc:
                                    try:
                                        sheet = gc.open_by_key(SHEET_ID).sheet1
                                        
                                        # Adiciona nova linha com os dados
                                        nova_linha = [
                                            form_data['data_hora'],
                                            form_data['nome'],
                                            form_data['cpf'],
                                            form_data['endereco'],
                                            form_data['email'],
                                            form_data['telefone'],
                                            form_data['idade'],
                                            form_data['data_nascimento'],
                                            form_data['diretoria'],
                                            form_data['comorbidade'],
                                            form_data['desc_comorbidade'],
                                            form_data['tipo_sanguineo'],
                                            form_data['plano_saude'],
                                            form_data['nome_plano'],
                                            form_data['estado_civil'],
                                            form_data['nome_conjuge'],
                                            form_data['idade_conjuge'],
                                            form_data['possui_filhos'],
                                            form_data['qtd_filhos'],
                                            form_data['emerg1_nome'],
                                            form_data['emerg1_telefone'],
                                            form_data['emerg1_parentesco'],
                                            form_data['emerg2_nome'],
                                            form_data['emerg2_telefone'],
                                            form_data['emerg2_parentesco']
                                        ]
                                        
                                        sheet.append_row(nova_linha)
                                        
                                        st.success("✅ Cadastro realizado com sucesso!")
                                        st.balloons()
                                    except Exception as e:
                                        st.error(f"Erro ao salvar no Google Sheets: {str(e)}")
                                else:
                                    st.warning("Google Sheets não configurado. Configure SHEET_ID em .streamlit/secrets.toml")
                            else:
                                st.info("📌 Dados do formulário (modo sem credenciais Google):")
                                st.json(form_data)
                        
                        except Exception as e:
                            st.error(f"❌ Erro ao processar cadastro: {str(e)}")
    
    with tab2:
        st.subheader("Consultar Dados Cadastrados")

        # Login de administrador
        if "admin_autenticado" not in st.session_state:
            st.session_state.admin_autenticado = False

        if not st.session_state.admin_autenticado:
            st.warning("🔒 Área restrita. Faça login para acessar os dados.")

            with st.form("login_admin"):
                usuario = st.text_input("Usuário")
                senha = st.text_input("Senha", type="password")
                login_btn = st.form_submit_button("🔑 Entrar")

                if login_btn:
                    admin_user = st.secrets["admin_user"]
                    admin_password = st.secrets["admin_password"]

                    if usuario == admin_user and senha == admin_password:
                        st.session_state.admin_autenticado = True
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")
        else:
            col_header, col_logout = st.columns([4, 1])
            with col_header:
                st.success("🔓 Acesso autorizado")
            with col_logout:
                if st.button("🚪 Sair"):
                    st.session_state.admin_autenticado = False
                    st.rerun()

            credentials = init_google_credentials()

            if credentials:
                try:
                    gc = get_google_sheet_client(credentials)
                    SHEET_ID = st.secrets.get("google_sheet_id", "")

                    if SHEET_ID and gc:
                        sheet = gc.open_by_key(SHEET_ID).sheet1
                        dados = sheet.get_all_values()

                        if len(dados) > 1:
                            df = pd.DataFrame(dados[1:], columns=dados[0])
                            st.dataframe(df, use_container_width=True, height=400)

                            # Download CSV
                            csv = df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 Baixar como CSV",
                                data=csv,
                                file_name=f"funcionarios_{datetime.now(FUSO_BRASIL).strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("Nenhum funcionário cadastrado ainda.")
                    else:
                        st.warning("Google Sheets não configurado.")
                except Exception as e:
                    st.error(f"Erro ao consultar dados: {str(e)}")
            else:
                st.warning("Credenciais não configuradas.")

if __name__ == "__main__":
    main()
