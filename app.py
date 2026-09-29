import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="SIGER - Gestão de Riscos IFES", 
    page_icon="🛡️",
    layout="wide"
)

# Estilização CSS para alinhar todos os botões da barra lateral à esquerda
st.markdown("""
    <style>
    section[data-testid="stSidebar"] div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# Conexão segura com Supabase (com higienização da URL)
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    if url.endswith("/rest/v1"):
        url = url[:-8]
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# ---------------------------------------------------------
# BARRA LATERAL (MENU POR BOTÕES ALINHADOS À ESQUERDA)
# ---------------------------------------------------------
st.sidebar.title("🛡️️ SIGER")
st.sidebar.markdown("**Sistema de Gestão de Riscos nas IFES**")
st.sidebar.caption("PPGOP / UFSM")
st.sidebar.divider()

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Início"

def navegar_para(pagina):
    st.session_state.pagina_atual = pagina

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
    
    * **Fundamentação:** COSO ERM & Teoria Institucional
    * **Desenvolvimento:** Pesquisa Aplicada do Programa de Pós-Graduação em Gestão de Organizações Públicas (PPGOP/UFSM)
    """)
    st.info("👈 Utilize o menu lateral para navegar entre os módulos do sistema.")

# ---------------------------------------------------------
# PÁGINA: CADASTROS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Cadastros":
    st.title("📝 Módulo de Cadastros")
    
    aba_cadastro = st.radio(
        "Selecione o tipo de cadastro:",
        ["Unidades", "Objetivos Estratégicos", "Categorias de Risco", "Riscos"],
        horizontal=True
    )
    
    st.divider()
    
    # ---------------------------------------------------------
    # SUB-MÓDULO 1: UNIDADES
    # ---------------------------------------------------------
    if aba_cadastro == "Unidades":
        st.subheader("🏢 Cadastramento de Unidades / Setores Institucionais")
        
        tab_list_unid, tab_novo_unid = st.tabs(["🔍 Unidades Cadastradas", "➕ Nova Unidade"])
        
        with tab_list_unid:
            try:
                resposta_unid = supabase.table("unidades").select("*").execute()
                dados_unid = resposta_unid.data
                
                if dados_unid:
                    df_unid = pd.DataFrame(dados_unid)
                    st.write(f"Total de unidades cadastradas: **{len(df_unid)}**")
                    st.dataframe(
                        df_unid[["codigo", "sigla", "nome_extenso"]],
                        use_container_width=True,
                        column_config={
                            "codigo": "Código",
                            "sigla": "Sigla da Unidade",
                            "nome_extenso": "Nome por Extenso"
                        }
                    )
                else:
                    st.info("Nenhuma unidade cadastrada. Cadastre a primeira unidade na aba 'Nova Unidade'.")
            except Exception as e:
                st.error(f"Erro ao conectar com a tabela 'unidades': {e}")
                
        with tab_novo_unid:
            try:
                res_count = supabase.table("unidades").select("id").execute()
                proximo_num = len(res_count.data) + 1 if res_count.data else 1
            except:
                proximo_num = 1
                
            codigo_gerado = f"{proximo_num:03d}"
            st.write(f"**Código Sequencial da Unidade:** `{codigo_gerado}`")
            
            with st.form("form_cadastrar_unidade", clear_on_submit=True):
                sigla = st.text_input("Sigla da Unidade*", placeholder="Ex: PRAE, PRPGP, CCSH, REITORIA").upper()
                nome_extenso = st.text_input("Nome da Unidade por Extenso*", placeholder="Ex: Pró-Reitoria de Assuntos Estudantis")
                
                st.caption("* Campos obrigatórios.")
                submitted_unid = st.form_submit_button("💾 Salvar Unidade")
                
                if submitted_unid:
                    if not sigla or not nome_extenso:
                        st.warning("Por favor, preencha a Sigla e o Nome por Extenso da unidade.")
                    else:
                        dados_nova_unidade = {
                            "codigo": codigo_gerado,
                            "sigla": sigla,
                            "nome_extenso": nome_extenso
                        }
                        try:
                            supabase.table("unidades").insert(dados_nova_unidade).execute()
                            st.success(f"✅ Unidade '{sigla}' registrada com o código {codigo_gerado}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar unidade: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO 2: OBJETIVOS ESTRATÉGICOS
    # ---------------------------------------------------------
    elif aba_cadastro == "Objetivos Estratégicos":
        st.subheader("🎯 Cadastramento de Objetivos Estratégicos (PDI)")
        
        tab_list_oe, tab_novo_oe = st.tabs(["🔍 Objetivos Cadastrados", "➕ Novo Objetivo Estratégico"])
        
        with tab_list_oe:
            try:
                res_oe = supabase.table("objetivos_estrategicos").select("*").execute()
                if res_oe.data:
                    df_oe = pd.DataFrame(res_oe.data)
                    st.dataframe(df_oe[["codigo", "descricao"]], use_container_width=True, column_config={"codigo": "Código", "descricao": "Descrição do Objetivo Estratégico"})
                else:
                    st.info("Nenhum objetivo estratégico cadastrado.")
            except Exception as e:
                st.error(f"Erro ao carregar Objetivos Estratégicos. Verifique se a tabela 'objetivos_estrategicos' foi criada no Supabase. Detalhes: {e}")
                
        with tab_novo_oe:
            with st.form("form_cadastrar_oe", clear_on_submit=True):
                codigo_oe = st.text_input("Código do Objetivo*", placeholder="Ex: OE-01, OE-02")
                descricao_oe = st.text_area("Descrição do Objetivo Estratégico*", placeholder="Ex: Promover a excelência no ensino de graduação e pós-graduação")
                
                submitted_oe = st.form_submit_button("💾 Salvar Objetivo Estratégico")
                if submitted_oe:
                    if not codigo_oe or not descricao_oe:
                        st.warning("Preencha o Código e a Descrição.")
                    else:
                        try:
                            supabase.table("objetivos_estrategicos").insert({"codigo": codigo_oe, "descricao": descricao_oe}).execute()
                            st.success("✅ Objetivo Estratégico cadastrado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO 3: CATEGORIAS DE RISCO
    # ---------------------------------------------------------
    elif aba_cadastro == "Categorias de Risco":
        st.subheader("🏷️ Cadastramento de Categorias de Risco")
        
        tab_list_cat, tab_novo_cat = st.tabs(["🔍 Categorias Cadastradas", "➕ Nova Categoria"])
        
        with tab_list_cat:
            try:
                res_cat = supabase.table("categorias_risco").select("*").execute()
                if res_cat.data:
                    df_cat = pd.DataFrame(res_cat.data)
                    st.dataframe(df_cat[["id", "nome"]], use_container_width=True, column_config={"id": "ID", "nome": "Nome da Categoria"})
                else:
                    st.info("Nenhuma categoria cadastrada.")
            except Exception as e:
                st.error(f"Erro ao carregar Categorias. Verifique se a tabela 'categorias_risco' foi criada no Supabase. Detalhes: {e}")
                
        with tab_novo_cat:
            with st.form("form_cadastrar_cat", clear_on_submit=True):
                nome_cat = st.text_input("Nome da Categoria*", placeholder="Ex: Operacional, Estratégico, Financeiro, Conformidade")
                submitted_cat = st.form_submit_button("💾 Salvar Categoria")
                if submitted_cat:
                    if not nome_cat:
                        st.warning("Preencha o nome da categoria.")
                    else:
                        try:
                            supabase.table("categorias_risco").insert({"nome": nome_cat}).execute()
                            st.success("✅ Categoria cadastrada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO 4: RISCOS (FORMULÁRIO E EXIBIÇÃO REESTRUTURADOS)
    # ---------------------------------------------------------
    elif aba_cadastro == "Riscos":
        st.subheader("📋 Gestão e Cadastro de Riscos Institucionais")
        
        tab1, tab2 = st.tabs(["🔍 Riscos Cadastrados", "➕ Novo Risco"])
        
        # TAB 1: LISTAGEM COMPLETA DOS RISCOS
        with tab1:
            try:
                resposta = supabase.table("riscos").select("*").order("id", desc=True).execute()
                dados = resposta.data
                
                if dados:
                    df = pd.DataFrame(dados)
                    st.write(f"Total de riscos registrados: **{len(df)}**")
                    st.dataframe(
                        df[[
                            "id", "unidade", "processo", "objetivo_estrategico", "categoria",
                            "evento_risco", "causa", "consequencia", "probabilidade", "impacto",
                            "nivel_risco", "responsavel", "data_cadastro", "data_revisao", "situacao"
                        ]],
                        use_container_width=True,
                        column_config={
                            "id": "ID",
                            "unidade": "Unidade",
                            "processo": "Processo",
                            "objetivo_estrategico": "Objetivo Estratégico",
                            "categoria": "Categoria",
                            "evento_risco": "Evento de Risco",
                            "causa": "Causa",
                            "consequencia": "Consequência",
                            "probabilidade": "Prob. (1-5)",
                            "impacto": "Imp. (1-5)",
                            "nivel_risco": "Nível",
                            "responsavel": "Responsável",
                            "data_cadastro": "Data Cadastro",
                            "data_revisao": "Data Revisão",
                            "situacao": "Situação"
                        }
                    )
                else:
                    st.info("Nenhum risco cadastrado até o momento. Utilize a aba 'Novo Risco' para realizar o primeiro registro.")
            except Exception as e:
                st.error(f"Erro ao carregar dados do banco: {e}")
                
        # TAB 2: FORMULÁRIO DE CADASTRO DE RISCOS
        with tab2:
            # Carrega listas de apoio do Supabase
            try:
                res_unidades = supabase.table("unidades").select("codigo, sigla, nome_extenso").execute().data or []
                res_oe = supabase.table("objetivos_estrategicos").select("codigo, descricao").execute().data or []
                res_cat = supabase.table("categorias_risco").select("nome").execute().data or []
            except Exception as e:
                res_unidades, res_oe, res_cat = [], [], []

            opcoes_unid = [f"{u['codigo']} - {u['sigla']} ({u['nome_extenso']})" for u in res_unidades] if res_unidades else ["(Nenhuma unidade cadastrada)"]
            opcoes_oe = [f"{o['codigo']} - {o['descricao']}" for o in res_oe] if res_oe else ["(Nenhum objetivo cadastrado)"]
            opcoes_cat = [c['nome'] for c in res_cat] if res_cat else ["Operacional", "Estratégico", "Financeiro/Orçamentário", "Conformidade/Legal", "Imagem/Reputacional"]

            with st.form("form_cadastrar_risco", clear_on_submit=True):
                st.markdown("##### 1. Contexto do Risco")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    unidade_sel = st.selectbox("Unidade Responsável*", options=opcoes_unid)
                    processo_input = st.text_input("Processo Associado*", placeholder="Ex: Concessão de Bolsas, Pregão Eletrônico, Matrícula")
                with col_c2:
                    oe_sel = st.selectbox("Objetivo Estratégico Relacionado*", options=opcoes_oe)
                    categoria_sel = st.selectbox("Categoria do Risco*", options=opcoes_cat)

                st.markdown("##### 2. Identificação e Análise do Risco")
                evento_input = st.text_area("Evento de Risco*", placeholder="Descreva o evento incerto que pode afetar os objetivos...")
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    causa_input = st.text_area("Causa(s)*", placeholder="Quais fatores geram ou favorecem a ocorrência deste risco?")
                with col_i2:
                    consequencia_input = st.text_area("Consequência(s)*", placeholder="Quais os impactos caso o risco se concretize?")

                st.markdown("##### 3. Avaliação Qualitativa")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    prob_val = st.slider("Probabilidade (1: Muito Baixa a 5: Muito Alta)", 1, 5, 3)
                with col_a2:
                    imp_val = st.slider("Impacto (1: Muito Baixo a 5: Muito Alto)", 1, 5, 3)

                st.markdown("##### 4. Governança, Controle e Prazos")
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    resp_input = st.text_input("Responsável pelo Risco*", placeholder="Nome / Cargo do servidor responsável")
                    situacao_sel = st.selectbox("Situação Inicial*", ["Identificado", "Em Análise", "Em Tratamento", "Monitorado", "Encerrado/Mitigado"])
                with col_g2:
                    dt_cadastro = st.date_input("Data do Cadastro*", datetime.now())
                with col_g3:
                    dt_revisao = st.date_input("Data Prevista para Revisão*", datetime.now())

                st.caption("* Campos de preenchimento obrigatório/recomendado.")
                submitted_risco = st.form_submit_button("💾 Salvar Risco no Sistema")
                
                if submitted_risco:
                    if not evento_input or not processo_input or not resp_input:
                        st.warning("Preencha os campos obrigatórios (Processo, Evento de Risco e Responsável).")
                    else:
                        nivel_calc = prob_val * imp_val
                        novo_risco_dados = {
                            "unidade": unidade_sel,
                            "processo": processo_input,
                            "objetivo_estrategico": oe_sel,
                            "categoria": categoria_sel,
                            "evento_risco": evento_input,
                            "causa": causa_input,
                            "consequencia": consequencia_input,
                            "probabilidade": prob_val,
                            "impacto": imp_val,
                            "nivel_risco": nivel_calc,
                            "responsavel": resp_input,
                            "data_cadastro": dt_cadastro.strftime("%Y-%m-%d"),
                            "data_revisao": dt_revisao.strftime("%Y-%m-%d"),
                            "situacao": situacao_sel
                        }
                        try:
                            res_ins = supabase.table("riscos").insert(novo_risco_dados).execute()
                            
                            # Registra a primeira entrada no histórico de alterações
                            if res_ins.data:
                                novo_id = res_ins.data[0]["id"]
                                hist_dados = {
                                    "risco_id": novo_id,
                                    "data_alteracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "responsavel_alteracao": resp_input,
                                    "detalhes": f"Cadastro inicial do risco com Nível {nivel_calc} (Probabilidade: {prob_val}, Impacto: {imp_val}). Situação: {situacao_sel}."
                                }
                                try:
                                    supabase.table("risco_historico").insert(hist_dados).execute()
                                except:
                                    pass

                            st.success("✅ Risco registrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar o risco no banco de dados. Verifique se os campos da tabela 'riscos' estão corretos. Detalhes: {e}")

    else:
        st.info("Este tipo de cadastro será desenvolvido nas próximas etapas.")

# ---------------------------------------------------------
# DEMAIS PÁGINAS
# ---------------------------------------------------------
else:
    st.title(f"🛠️ {st.session_state.pagina_atual}")
    st.info("Módulo em fase de estruturação. Em breve implementaremos as funcionalidades desta área.")
