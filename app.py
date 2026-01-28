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
                ["Selecione uma opção", "GABINETE", "DAFIN", "DAPP", "DIPAS", "DIRES", "DIRSIN"],
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
                            # Cabeçalhos reais da planilha
                            df = pd.DataFrame(dados[1:], columns=dados[0])

                            # Nomes amigáveis para exibição
                            NOMES_EXIBICAO = {
                                'data_hora': 'Data/Hora Cadastro',
                                'nome': 'Nome Completo',
                                'cpf': 'CPF',
                                'endereco': 'Endereço',
                                'email': 'E-mail',
                                'telefone': 'Telefone',
                                'idade': 'Idade',
                                'data_nascimento': 'Data de Nascimento',
                                'Diretoria': 'Diretoria',
                                'comorbidade': 'Possui Comorbidade',
                                'desc_comorbidade': 'Descrição Comorbidade',
                                'tipo_sanguineo': 'Tipo Sanguíneo',
                                'plano_saude': 'Possui Plano de Saúde',
                                'nome_plano': 'Nome do Plano',
                                'estado_civil': 'Estado Civil',
                                'nome_conjuge': 'Nome Cônjuge/Companheiro(a)',
                                'idade_conjuge': 'Idade Cônjuge/Companheiro(a)',
                                'possui_filhos': 'Possui Filhos',
                                'qtd_filhos': 'Quantidade de Filhos',
                                'emerg1_nome': 'Emergência 1 - Nome',
                                'emerg1_telefone': 'Emergência 1 - Telefone',
                                'emerg1_parentesco': 'Emergência 1 - Parentesco',
                                'emerg2_nome': 'Emergência 2 - Nome',
                                'emerg2_telefone': 'Emergência 2 - Telefone',
                                'emerg2_parentesco': 'Emergência 2 - Parentesco'
                            }

                            # ===== PESQUISA E FILTROS =====
                            st.markdown("### 🔍 Pesquisa e Filtros")
                            col_busca, col_diretoria = st.columns([2, 1])

                            with col_busca:
                                termo_busca = st.text_input(
                                    "Buscar por nome, CPF, e-mail ou telefone",
                                    key="termo_busca",
                                    placeholder="Digite para pesquisar..."
                                )

                            with col_diretoria:
                                diretorias_disponiveis = ["Todas"] + sorted(
                                    [d for d in df["Diretoria"].unique().tolist() if d.strip()]
                                )
                                filtro_diretoria = st.selectbox(
                                    "Filtrar por Diretoria",
                                    diretorias_disponiveis,
                                    key="filtro_diretoria"
                                )

                            # Aplicar filtro de busca (usa nomes originais da planilha)
                            df_filtrado = df.copy()
                            if termo_busca:
                                termo = termo_busca.lower()
                                mascara = (
                                    df_filtrado["nome"].str.lower().str.contains(termo, na=False) |
                                    df_filtrado["cpf"].str.lower().str.contains(termo, na=False) |
                                    df_filtrado["email"].str.lower().str.contains(termo, na=False) |
                                    df_filtrado["telefone"].str.lower().str.contains(termo, na=False)
                                )
                                df_filtrado = df_filtrado[mascara]

                            # Aplicar filtro de diretoria
                            if filtro_diretoria != "Todas":
                                df_filtrado = df_filtrado[df_filtrado["Diretoria"] == filtro_diretoria]

                            # ===== ORDENAÇÃO =====
                            col_ord_campo, col_ord_dir = st.columns([2, 1])
                            with col_ord_campo:
                                # Mostrar nomes amigáveis no selectbox
                                colunas_display = [NOMES_EXIBICAO.get(c, c) for c in df.columns.tolist()]
                                coluna_idx = st.selectbox(
                                    "Ordenar por",
                                    range(len(colunas_display)),
                                    index=1,  # Nome por padrão
                                    format_func=lambda x: colunas_display[x],
                                    key="coluna_ordenar"
                                )
                                coluna_ordenar = df.columns[coluna_idx]
                            with col_ord_dir:
                                direcao = st.radio(
                                    "Direção",
                                    ["Crescente (A→Z)", "Decrescente (Z→A)"],
                                    horizontal=True,
                                    key="direcao_ordenar"
                                )

                            ascendente = direcao == "Crescente (A→Z)"
                            df_filtrado = df_filtrado.sort_values(by=coluna_ordenar, ascending=ascendente, ignore_index=True)

                            st.markdown(f"**{len(df_filtrado)}** registro(s) encontrado(s)")
                            st.markdown("---")

                            # ===== EXIBIÇÃO DA TABELA =====
                            df_filtrado_exibicao = df_filtrado.rename(columns=NOMES_EXIBICAO)
                            st.dataframe(df_filtrado_exibicao, use_container_width=True, height=400)

                            # Download CSV (dados filtrados)
                            csv = df_filtrado_exibicao.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 Baixar como CSV",
                                data=csv,
                                file_name=f"funcionarios_{datetime.now(FUSO_BRASIL).strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )

                            st.markdown("---")

                            # ===== EDITAR / EXCLUIR REGISTROS =====
                            st.markdown("### ✏️ Editar ou Excluir Registro")

                            if len(df_filtrado) == 0:
                                st.info("Nenhum registro para editar ou excluir com os filtros atuais.")
                            else:
                                # Seleção do registro
                                opcoes_registro = [
                                    f"{i+1} - {row['nome']} (CPF: {row['cpf']})"
                                    for i, row in df_filtrado.iterrows()
                                ]
                                registro_selecionado = st.selectbox(
                                    "Selecione o registro",
                                    opcoes_registro,
                                    key="registro_selecionado"
                                )

                                idx_filtrado = opcoes_registro.index(registro_selecionado)
                                registro = df_filtrado.iloc[idx_filtrado]

                                tab_editar, tab_excluir = st.tabs(["✏️ Editar", "🗑️ Excluir"])

                                # ===== ABA EDITAR =====
                                with tab_editar:
                                    with st.form("form_editar"):
                                        st.markdown(f"**Editando:** {registro['nome']}")

                                        col1, col2 = st.columns(2)
                                        with col1:
                                            edit_nome = st.text_input("Nome Completo", value=registro.get("nome", ""), key="edit_nome")
                                            edit_cpf = st.text_input("CPF", value=registro.get("cpf", ""), key="edit_cpf")
                                            edit_email = st.text_input("E-mail", value=registro.get("email", ""), key="edit_email")
                                            edit_telefone = st.text_input("Telefone", value=registro.get("telefone", ""), key="edit_telefone")
                                            edit_idade = st.text_input("Idade", value=str(registro.get("idade", "")), key="edit_idade")
                                            edit_data_nasc = st.text_input("Data de Nascimento", value=registro.get("data_nascimento", ""), key="edit_data_nasc")
                                            edit_endereco = st.text_area("Endereço", value=registro.get("endereco", ""), key="edit_endereco")

                                        with col2:
                                            diretorias = ["GABINETE", "DAFIN", "DAPP", "DIPAS", "DIRES", "DIRSIN"]
                                            idx_dir = diretorias.index(registro.get("Diretoria", "GABINETE")) if registro.get("Diretoria", "") in diretorias else 0
                                            edit_diretoria = st.selectbox("Diretoria", diretorias, index=idx_dir, key="edit_diretoria")

                                            edit_comorbidade = st.radio("Possui Comorbidade?", ["Não", "Sim"], index=0 if registro.get("comorbidade", "Não") == "Não" else 1, key="edit_comorbidade")
                                            edit_desc_comorbidade = st.text_area("Descrição Comorbidade", value=registro.get("desc_comorbidade", ""), key="edit_desc_comorbidade")

                                            tipos_sang = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
                                            idx_ts = tipos_sang.index(registro.get("tipo_sanguineo", "O+")) if registro.get("tipo_sanguineo", "") in tipos_sang else 0
                                            edit_tipo_sang = st.selectbox("Tipo Sanguíneo", tipos_sang, index=idx_ts, key="edit_tipo_sang")

                                            edit_plano_saude = st.radio("Possui Plano de Saúde?", ["Não", "Sim"], index=0 if registro.get("plano_saude", "Não") == "Não" else 1, key="edit_plano_saude")
                                            edit_nome_plano = st.text_input("Nome do Plano", value=registro.get("nome_plano", ""), key="edit_nome_plano")

                                            estados_civis = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União Estável"]
                                            idx_ec = estados_civis.index(registro.get("estado_civil", "Solteiro(a)")) if registro.get("estado_civil", "") in estados_civis else 0
                                            edit_estado_civil = st.selectbox("Estado Civil", estados_civis, index=idx_ec, key="edit_estado_civil")

                                        st.markdown("**Família**")
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            edit_nome_conjuge = st.text_input("Nome Cônjuge/Companheiro(a)", value=registro.get("nome_conjuge", ""), key="edit_nome_conjuge")
                                            edit_idade_conjuge = st.text_input("Idade Cônjuge", value=str(registro.get("idade_conjuge", "")), key="edit_idade_conjuge")
                                        with col2:
                                            edit_possui_filhos = st.radio("Possui Filhos?", ["Não", "Sim"], index=0 if registro.get("possui_filhos", "Não") == "Não" else 1, key="edit_possui_filhos")
                                            edit_qtd_filhos = st.text_input("Quantidade de Filhos", value=str(registro.get("qtd_filhos", "0")), key="edit_qtd_filhos")

                                        st.markdown("**Contatos de Emergência**")
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            edit_e1_nome = st.text_input("Emergência 1 - Nome", value=registro.get("emerg1_nome", ""), key="edit_e1_nome")
                                        with col2:
                                            edit_e1_tel = st.text_input("Emergência 1 - Telefone", value=registro.get("emerg1_telefone", ""), key="edit_e1_tel")
                                        with col3:
                                            edit_e1_par = st.text_input("Emergência 1 - Parentesco", value=registro.get("emerg1_parentesco", ""), key="edit_e1_par")

                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            edit_e2_nome = st.text_input("Emergência 2 - Nome", value=registro.get("emerg2_nome", ""), key="edit_e2_nome")
                                        with col2:
                                            edit_e2_tel = st.text_input("Emergência 2 - Telefone", value=registro.get("emerg2_telefone", ""), key="edit_e2_tel")
                                        with col3:
                                            edit_e2_par = st.text_input("Emergência 2 - Parentesco", value=registro.get("emerg2_parentesco", ""), key="edit_e2_par")

                                        salvar_btn = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)

                                        if salvar_btn:
                                            erros_edicao = []
                                            if not edit_nome.strip():
                                                erros_edicao.append("Nome é obrigatório")
                                            if not validar_cpf(edit_cpf):
                                                erros_edicao.append("CPF inválido")
                                            if not validar_email(edit_email):
                                                erros_edicao.append("E-mail inválido")

                                            if erros_edicao:
                                                st.error("❌ Erros encontrados:")
                                                for e in erros_edicao:
                                                    st.write(f"• {e}")
                                            else:
                                                try:
                                                    linha_atualizada = [
                                                        registro.get("data_hora", ""),
                                                        edit_nome,
                                                        formatar_cpf(edit_cpf),
                                                        edit_endereco,
                                                        edit_email,
                                                        formatar_telefone(edit_telefone),
                                                        edit_idade,
                                                        edit_data_nasc,
                                                        edit_diretoria,
                                                        edit_comorbidade,
                                                        edit_desc_comorbidade,
                                                        edit_tipo_sang,
                                                        edit_plano_saude,
                                                        edit_nome_plano,
                                                        edit_estado_civil,
                                                        edit_nome_conjuge,
                                                        edit_idade_conjuge,
                                                        edit_possui_filhos,
                                                        edit_qtd_filhos,
                                                        edit_e1_nome,
                                                        formatar_telefone(edit_e1_tel),
                                                        edit_e1_par,
                                                        edit_e2_nome,
                                                        formatar_telefone(edit_e2_tel),
                                                        edit_e2_par
                                                    ]

                                                    # Buscar linha real na planilha pelo CPF + Nome
                                                    cpf_original = registro.get("cpf", "")
                                                    nome_original = registro.get("nome", "")
                                                    todas_linhas = sheet.get_all_values()
                                                    linha_real = None
                                                    for idx_l, linha in enumerate(todas_linhas):
                                                        if idx_l == 0:
                                                            continue  # pular cabeçalho
                                                        if len(linha) > 2 and linha[2] == cpf_original and linha[1] == nome_original:
                                                            linha_real = idx_l + 1  # gspread usa base 1
                                                            break

                                                    if linha_real:
                                                        nc = len(linha_atualizada)
                                                        ultima_coluna = chr(ord('A') + nc - 1) if nc <= 26 else 'Y'
                                                        intervalo = f"A{linha_real}:{ultima_coluna}{linha_real}"
                                                        sheet.update(intervalo, [linha_atualizada])
                                                        st.success("✅ Registro atualizado com sucesso!")
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Não foi possível localizar o registro na planilha.")

                                                except Exception as e:
                                                    st.error(f"❌ Erro ao atualizar: {str(e)}")

                                # ===== ABA EXCLUIR =====
                                with tab_excluir:
                                    st.markdown(f"**Registro selecionado:** {registro['nome']} — CPF: {registro['cpf']}")

                                    st.warning("⚠️ Esta ação é irreversível. O registro será permanentemente removido da planilha.")

                                    confirmar = st.checkbox("Confirmo que desejo excluir este registro", key="confirmar_exclusao")

                                    if st.button("🗑️ Excluir Registro", type="primary", disabled=not confirmar, key="btn_excluir"):
                                        try:
                                            cpf_original = registro.get("cpf", "")
                                            nome_original = registro.get("nome", "")
                                            todas_linhas = sheet.get_all_values()
                                            linha_real = None
                                            for idx_l, linha in enumerate(todas_linhas):
                                                if idx_l == 0:
                                                    continue
                                                if len(linha) > 2 and linha[2] == cpf_original and linha[1] == nome_original:
                                                    linha_real = idx_l + 1
                                                    break

                                            if linha_real:
                                                sheet.delete_rows(linha_real)
                                                st.success("✅ Registro excluído com sucesso!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Não foi possível localizar o registro na planilha.")
                                        except Exception as e:
                                            st.error(f"❌ Erro ao excluir: {str(e)}")

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
