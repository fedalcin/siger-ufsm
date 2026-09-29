import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E CONEXÃO
# ---------------------------------------------------------
st.set_page_config(page_title="SIGER - Gestão de Riscos IFES", layout="wide")

# Conectando ao Supabase usando as chaves seguras do Streamlit
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

st.title("🛡️ SIGER - Sistema de Gestão de Riscos nas IFES")
st.markdown("Ferramenta para Mapeamento, Avaliação e Monitoramento de Riscos (Base COSO / PTT Doutorado PPGOP-UFSM)")

# ---------------------------------------------------------
# MENU LATERAL - NAVEGAÇÃO
# ---------------------------------------------------------
menu = st.sidebar.selectbox("Navegação", ["Dashboard / Painel", "Cadastrar Novo Risco", "Matriz de Riscos"])

# ---------------------------------------------------------
# OPCÃO 1: CADASTRAR NOVO RISCO
# ---------------------------------------------------------
if menu == "Cadastrar Novo Risco":
    st.subheader("📋 Identificação e Avaliação do Risco")
    
    with st.form("form_risco", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            unidade = st.text_input("Unidade / Setor Responsável", placeholder="Ex: PRAE, PRPGP, CCSH")
            componente_coso = st.selectbox(
                "Componente COSO Relevante",
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
            descricao = st.text_area("Descrição do Risco / Evento", placeholder="Descreva o risco identificado...")

        with col2:
            probabilidade = st.slider("Probabilidade (1: Muito Baixa a 5: Muito Alta)", 1, 5, 3)
            impacto = st.slider("Impacto (1: Muito Baixo a 5: Muito Alto)", 1, 5, 3)
            plano_resposta = st.text_area("Plano de Resposta / Ação de Mitigação")
            
        submitted = st.form_submit_button("Salvar Risco no SIGER")
        
        if submitted:
            nivel = probabilidade * impacto
            dados = {
                "unidade": unidade,
                "componente_coso": componente_coso,
                "descricao_risco": descricao,
                "probabilidade": probabilidade,
                "impacto": impacto,
                "nivel_risco": nivel,
                "plano_resposta": plano_resposta
            }
            # Inserindo no Banco de Dados
            supabase.table("riscos").insert(dados).execute()
            st.success("✅ Risco cadastrado com sucesso no banco de dados!")

# ---------------------------------------------------------
# OPÇÃO 2: DASHBOARD / PAINEL
# ---------------------------------------------------------
elif menu == "Dashboard / Painel":
    st.subheader("📊 Visão Geral dos Riscos Mapeados")
    
    # Busca dados no Supabase
    resposta = supabase.table("riscos").select("*").execute()
    dados = resposta.data
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Métricas no topo
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total de Riscos Mapeados", len(df))
        col_m2.metric("Riscos Críticos (Nível >= 15)", len(df[df["nivel_risco"] >= 15]))
        col_m3.metric("Média Geral de Nível de Risco", round(df["nivel_risco"].mean(), 2))
        
        st.divider()
        st.dataframe(df[["id", "unidade", "componente_coso", "descricao_risco", "nivel_risco", "plano_resposta"]], use_container_width=True)
    else:
        st.info("Nenhum risco cadastrado até o momento.")

# ---------------------------------------------------------
# OPÇÃO 3: MATRIZ DE RISCOS (PROBABILIDADE X IMPACTO)
# ---------------------------------------------------------
elif menu == "Matriz de Riscos":
    st.subheader("📌 Matriz de Riscos (Probabilidade x Impacto)")
    
    resposta = supabase.table("riscos").select("*").execute()
    dados = resposta.data
    
    if dados:
        df = pd.DataFrame(dados)
        # Tabela cruzada contando riscos por Probabilidade x Impacto
        matriz = pd.crosstab(df['probabilidade'], df['impacto'])
        st.write("Distribuição da quantidade de riscos por célula de risco:")
        st.bar_chart(df.groupby('componente_coso')['nivel_risco'].mean())
    else:
        st.info("Sem dados suficientes para gerar a matriz.")
