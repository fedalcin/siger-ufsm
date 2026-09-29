import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="SIGER - Gestão de Riscos IFES", 
    page_icon="🛡️",
    layout="wide"
)

# Conexão segura com Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ---------------------------------------------------------
# BARRA LATERAL (MENU POR BOTÕES)
# ---------------------------------------------------------
st.sidebar.title("🛡️ SIGER")
st.sidebar.markdown("**Sistema de Gestão de Riscos nas IFES**")
st.sidebar.caption("PPGOP / UFSM")
st.sidebar.divider()

# Estado da sessão para controlar qual tela está ativa
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Início"

# Função auxiliar para trocar de página
def navegar_para(pagina):
    st.session_state.pagina_atual = pagina

# Lista de Botões do Menu Lateral
st.sidebar.subheader("Menu Principal")

if st.sidebar.button("🏠 Início", use_container_width=True):
    navegar_para("Início")

if st.sidebar.button("⚙️ Administração do Sistema", use_container_width=True):
    navegar_para("Administração do Sistema")

if st.sidebar.button("📝 Cadastros", use_container_width=True):
    navegar_para("Cadastros")

if st.sidebar.button("🔄 Monitoramento", use_container_width=True):
    navegar_para("Monitoramento")

if st.sidebar.button("🧠 Inteligência Gerencial", use_container_width=True):
    navegar_para("Inteligência Gerencial")

if st.sidebar.button("📊 Dashboards", use_container_width=True):
    navegar_para("Dashboards")

if st.sidebar.button("🛡️ Planos de Tratamento", use_container_width=True):
    navegar_para("Planos de Tratamento")

if st.sidebar.button("📚 Biblioteca", use_container_width=True):
    navegar_para("Biblioteca")

if st.sidebar.button("📑 Relatórios", use_container_width=True):
    navegar_para("Relatórios")

if st.sidebar.button("🌐 Transparência", use_container_width=True):
    navegar_para("Transparência")

# ---------------------------------------------------------
# PÁGINA: INÍCIO
# ---------------------------------------------------------
if st.session_state.pagina_atual == "Início":
    st.title("🛡️ SIGER - Sistema de Gestão de Riscos nas IFES")
    st.markdown("""
    Bem-vindo ao **SIGER**, a solução integrada para mapeamento, avaliação e monitoramento de riscos 
    institucionais no âmbito das Instituições Federais de Ensino Superior (IFES).
    
    * **Fundamentação:** COSO ERM (8 Componentes) & Teoria Institucional
    * **Desenvolvimento:** Pesquisa Aplicada do Programa de Pós-Graduação em Organizações e Mercados (PPGOP/UFSM)[cite: 1]
    """)
    st.info("👈 Utilize o menu lateral para navegar entre os módulos do sistema.")

# ---------------------------------------------------------
# PÁGINA: CADASTROS (FOCO EM RISCOS)
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Cadastros":
    st.title("📝 Módulo de Cadastros")
    
    # Submenu interno de Cadastros (Opcões futuras: Unidades, Processos, Riscos, etc.)
    aba_cadastro = st.radio(
        "Selecione o tipo de cadastro:",
        ["Riscos", "Unidades / Setores (Em breve)", "Processos / Atividades (Em breve)"],
        horizontal=True
    )
    
    st.divider()
    
    if aba_cadastro == "Riscos":
        st.subheader("📋 Gestão e Cadastro de Riscos Institucionais")
        
        # Abas para Separar Lista x Novo Cadastro
        tab1, tab2 = st.tabs(["🔍 Riscos Cadastrados", "➕ Novo Risco"])
        
        # TAB 1: VISUALIZAÇÃO DOS RISCOS
        with tab1:
            try:
                resposta = supabase.table("riscos").select("*").execute()
                dados = resposta.data
                
                if dados:
                    df = pd.DataFrame(dados)
                    st.write(f"Total de riscos registrados: **{len(df)}**")
                    
                    # Exibição organizada
                    st.dataframe(
                        df[["id", "unidade", "componente_coso", "descricao_risco", "probabilidade", "impacto", "nivel_risco", "plano_resposta"]],
                        use_container_width=True,
                        column_config={
                            "id": "ID",
                            "unidade": "Unidade/Setor",
                            "componente_coso": "Componente COSO",
                            "descricao_risco": "Descrição do Risco",
                            "probabilidade": "Prob. (1-5)",
                            "impacto": "Imp. (1-5)",
                            "nivel_risco": "Nível de Risco",
                            "plano_resposta": "Plano de Resposta/Mitigação"
                        }
                    )
                else:
                    st.info("Nenhum risco cadastrado até o momento. Utilize a aba 'Novo Risco' para realizar o primeiro registro.")
            except Exception as e:
                st.error(f"Erro ao carregar dados do banco: {e}")
                
        # TAB 2: FORMULÁRIO DE CADASTRO
        with tab2:
            with st.form("form_cadastrar_risco", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    unidade = st.text_input("Unidade / Setor Responsável*", placeholder="Ex: Pro-Reitoria de Planejamento, CCSH, PRAE")
                    componente_coso = st.selectbox(
                        "Componente COSO Relevante*",
                        [
                            "1. Ambiente Interno",
                            "2. Definição de Objetivos",
                            "3. Identificação de Eventos",
                            "4. Avaliação de Riscos",
                            "5. Resposta ao Risco",
                            "6. Atividades de Controle",
                            "7. Informação e Comunicação",
                            "8. Monitoramento"
                        ]
                    )
                    descricao = st.text_area("Descrição Detalhada do Risco / Evento*", placeholder="Descreva a causa, evento e consequência do risco...")

                with col2:
                    probabilidade = st.slider("Probabilidade (1: Muito Baixa a 5: Muito Alta)", 1, 5, 3)
                    impacto = st.slider("Impacto (1: Muito Baixo a 5: Muito Alto)", 1, 5, 3)
                    plano_resposta = st.text_area("Plano de Resposta Inicial / Ação Sugerida", placeholder="Medidas recomendadas para mitigar ou tratar este risco...")
                    
                st.caption("* Campos de preenchimento importante.")
                submitted = st.form_submit_button("💾 Salvar Risco no Sistema")
                
                if submitted:
                    if not unidade or not descricao:
                        st.warning("Por favor, preencha a 'Unidade' e a 'Descrição do Risco'.")
                    else:
                        nivel = probabilidade * impacto
                        dados_novo_risco = {
                            "unidade": unidade,
                            "componente_coso": componente_coso,
                            "descricao_risco": descricao,
                            "probabilidade": probabilidade,
                            "impacto": impacto,
                            "nivel_risco": nivel,
                            "plano_resposta": plano_resposta
                        }
                        
                        try:
                            supabase.table("riscos").insert(dados_novo_risco).execute()
                            st.success("✅ Risco cadastrado com sucesso! Acesse a aba 'Riscos Cadastrados' para visualizar.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco de dados: {e}")

    else:
        st.info("Este tipo de cadastro será desenvolvido nas próximas etapas.")

# ---------------------------------------------------------
# DEMAIS PÁGINAS (ESTRUTURA EM CONSTRUÇÃO)
# ---------------------------------------------------------
else:
    st.title(f"🛠️ {st.session_state.pagina_atual}")
    st.info("Módulo em fase de estruturação. Em breve implementaremos as funcionalidades desta área.")
