import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import os

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="SÍGER - Sistema de Gestão de Riscos", 
    page_icon="🛡️",
    layout="wide"
)

# Estilização CSS personalizada
st.markdown("""
    <style>
    section[data-testid="stSidebar"] div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
        border: none !important;
        background-color: transparent !important;
        padding-left: 10px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #f0f2f6 !important;
        color: #000000 !important;
    }
    div[data-testid="stSidebarUserContent"] details {
        border: none !important;
        margin-bottom: 5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Conexão segura com Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    if url.endswith("/rest/v1"):
        url = url[:-8]
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# Duas opções solicitadas para o tipo da unidade
TIPOS_UNIDADE_OPCOES = [
    "Acadêmica",
    "Administrativa"
]

# ---------------------------------------------------------
# BARRA LATERAL (LOGOTIPO E MENU EXPANSÍVEL)
# ---------------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.title("🛡️ SÍGER")
    st.sidebar.markdown("**Sistema de Gestão de Riscos**")

st.sidebar.caption("PPGOP / UFSM")
st.sidebar.divider()

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Início"
if "sub_pagina_atual" not in st.session_state:
    st.session_state.sub_pagina_atual = None

def navegar_para(pagina, sub_pagina=None):
    st.session_state.pagina_atual = pagina
    st.session_state.sub_pagina_atual = sub_pagina

st.sidebar.subheader("Menu Principal")

if st.sidebar.button("🏠 Início", use_container_width=True):
    navegar_para("Início")

with st.sidebar.expander("⚙️ Administração", expanded=False):
    if st.button("👥 Usuários e Permissões", key="btn_adm_usr", use_container_width=True):
        navegar_para("Administração do Sistema", "Usuários")
    if st.button("🔧 Configurações Gerais", key="btn_adm_cfg", use_container_width=True):
        navegar_para("Administração do Sistema", "Configurações")

with st.sidebar.expander("📝 Cadastros", expanded=False):
    if st.button("🏢 Unidades", key="btn_cad_unid", use_container_width=True):
        navegar_para("Cadastros", "Unidades")
    if st.button("🎯 Objetivos Estratégicos", key="btn_cad_oe", use_container_width=True):
        navegar_para("Cadastros", "Objetivos Estratégicos")
    if st.button("🏷️ Categorias de Risco", key="btn_cad_cat", use_container_width=True):
        navegar_para("Cadastros", "Categorias de Risco")
    if st.button("📋 Riscos", key="btn_cad_risco", use_container_width=True):
        navegar_para("Cadastros", "Riscos")
    if st.button("✍️ Texto da Tela Inicial", key="btn_cad_txt", use_container_width=True):
        navegar_para("Cadastros", "Texto da Tela Inicial")

with st.sidebar.expander("🔄 Monitoramento", expanded=False):
    if st.button("📌 Acompanhamento de Riscos", key="btn_mon_acomp", use_container_width=True):
        navegar_para("Monitoramento", "Acompanhamento")
    if st.button("📅 Matriz de Revisões", key="btn_mon_rev", use_container_width=True):
        navegar_para("Monitoramento", "Revisões")

with st.sidebar.expander("🧠 Inteligência Gerencial", expanded=False):
    if st.button("💡 Análise de Tendências", key="btn_ig_tend", use_container_width=True):
        navegar_para("Inteligência Gerencial", "Tendências")

with st.sidebar.expander("📊 Dashboards", expanded=False):
    if st.button("📈 Painel Geral", key="btn_dash_geral", use_container_width=True):
        navegar_para("Dashboards", "Painel Geral")
    if st.button("🎯 Matriz de Risco (5x5)", key="btn_dash_matriz", use_container_width=True):
        navegar_para("Dashboards", "Matriz 5x5")

with st.sidebar.expander("🛡️ Planos de Tratamento", expanded=False):
    if st.button("📋 Ações de Mitigação", key="btn_pt_acoes", use_container_width=True):
        navegar_para("Planos de Tratamento", "Ações")

with st.sidebar.expander("📚 Biblioteca", expanded=False):
    if st.button("📄 Documentos e Normativas", key="btn_bib_doc", use_container_width=True):
        navegar_para("Biblioteca", "Documentos")

with st.sidebar.expander("📑 Relatórios", expanded=False):
    if st.button("🖨️ Relatório de Riscos (PDF/Excel)", key="btn_rel_riscos", use_container_width=True):
        navegar_para("Relatórios", "Relatório Riscos")

with st.sidebar.expander("🌐 Transparência", expanded=False):
    if st.button("🔓 Painel Público", key="btn_transp_pub", use_container_width=True):
        navegar_para("Transparência", "Painel Público")

# ---------------------------------------------------------
# PÁGINA: INÍCIO
# ---------------------------------------------------------
if st.session_state.pagina_atual == "Início":
    st.title("SÍGER - Sistema de Gestão de Riscos")
    
    texto_inicio_personalizado = ""
    try:
        res_cfg = supabase.table("configuracoes").select("valor").eq("chave", "texto_pagina_inicial").execute()
        if res_cfg.data and len(res_cfg.data) > 0:
            texto_inicio_personalizado = res_cfg.data[0]["valor"]
    except Exception as e:
        texto_inicio_personalizado = ""

    if texto_inicio_personalizado:
        st.markdown(texto_inicio_personalizado)
    else:
        st.markdown("""
        Bem-vindo ao **SÍGER**, a solução integrada para mapeamento, avaliação e monitoramento de riscos 
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
    
    sub = st.session_state.sub_pagina_atual or "Unidades"
    
    # ---------------------------------------------------------
    # SUB-MÓDULO 1: UNIDADES (TIPO: ACADÊMICA OU ADMINISTRATIVA)
    # ---------------------------------------------------------
    if sub == "Unidades":
        st.subheader("🏢 Cadastramento de Unidades / Setores Institucionais")
        
        tab_list_unid, tab_novo_unid = st.tabs(["🔍 Unidades Cadastradas", "➕ Nova Unidade"])
        
        with tab_list_unid:
            try:
                resposta_unid = supabase.table("unidades").select("*").order("codigo").execute()
                dados_unid = resposta_unid.data
                
                if dados_unid:
                    st.write(f"Total de unidades cadastradas: **{len(dados_unid)}**")
                    
                    for item in dados_unid:
                        tipo_exibicao = item.get('tipo_unidade', 'Não informado')
                        with st.expander(f"📍 `{item['codigo']}` - {item['sigla']} | {item['nome_extenso']} ({tipo_exibicao})"):
                            col_info, col_acoes = st.columns([3, 1])
                            
                            with col_info:
                                st.write(f"**Tipo da Unidade:** {tipo_exibicao}")
                            
                            with col_acoes:
                                modal_edit = st.popover("✏️ Editar")
                                with modal_edit:
                                    st.markdown("### Editar Unidade")
                                    with st.form(f"form_edit_unid_{item['id']}"):
                                        edit_sigla = st.text_input("Sigla", value=item['sigla']).upper()
                                        edit_nome = st.text_input("Nome Extenso", value=item['nome_extenso'])
                                        idx_tipo = TIPOS_UNIDADE_OPCOES.index(item['tipo_unidade']) if item.get('tipo_unidade') in TIPOS_UNIDADE_OPCOES else 0
                                        edit_tipo = st.selectbox("Tipo da Unidade", options=TIPOS_UNIDADE_OPCOES, index=idx_tipo)
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            try:
                                                supabase.table("unidades").update({
                                                    "sigla": edit_sigla,
                                                    "nome_extenso": edit_nome,
                                                    "tipo_unidade": edit_tipo
                                                }).eq("id", item['id']).execute()
                                                st.success("Unidade atualizada!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao atualizar: {e}")

                                modal_del = st.popover("🗑️ Excluir")
                                with modal_del:
                                    st.warning("Tem certeza que deseja excluir esta unidade?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_unid_{item['id']}"):
                                        try:
                                            res_riscos = supabase.table("riscos").select("id").like("unidade", f"%{item['sigla']}%").execute()
                                            if res_riscos.data and len(res_riscos.data) > 0:
                                                st.error(f"❌ Não é possível excluir a unidade '{item['sigla']}' pois existem {len(res_riscos.data)} risco(s) associado(s) a ela.")
                                            else:
                                                supabase.table("unidades").delete().eq("id", item['id']).execute()
                                                st.success("Unidade excluída com sucesso!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao tentar excluir: {e}")
                else:
                    st.info("Nenhuma unidade cadastrada.")
            except Exception as e:
                st.error(f"Erro ao carregar unidades: {e}")
                
        with tab_novo_unid:
            try:
                res_count = supabase.table("unidades").select("id").execute()
                proximo_num = len(res_count.data) + 1 if res_count.data else 1
            except:
                proximo_num = 1
                
            codigo_gerado = f"{proximo_num:03d}"
            st.write(f"**Código Sequencial da Unidade:** `{codigo_gerado}`")
            
            with st.form("form_cadastrar_unidade", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    sigla = st.text_input("Sigla da Unidade*", placeholder="Ex: PRAE, PRPGP, CCSH, REITORIA").upper()
                    nome_extenso = st.text_input("Nome da Unidade por Extenso*", placeholder="Ex: Pró-Reitoria de Assuntos Estudantis")
                with col_u2:
                    tipo_unidade_sel = st.selectbox("Tipo da Unidade*", options=TIPOS_UNIDADE_OPCOES)
                
                st.caption("* Campos obrigatórios.")
                submitted_unid = st.form_submit_button("💾 Salvar Unidade")
                
                if submitted_unid:
                    if not sigla or not nome_extenso:
                        st.warning("Por favor, preencha a Sigla e o Nome por Extenso.")
                    else:
                        dados_nova_unidade = {
                            "codigo": codigo_gerado,
                            "sigla": sigla,
                            "nome_extenso": nome_extenso,
                            "tipo_unidade": tipo_unidade_sel
                        }
                        try:
                            supabase.table("unidades").insert(dados_nova_unidade).execute()
                            st.success(f"✅ Unidade '{sigla}' ({tipo_unidade_sel}) registrada!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar unidade: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO 2: OBJETIVOS ESTRATÉGICOS
    # ---------------------------------------------------------
    elif sub == "Objetivos Estratégicos":
        st.subheader("🎯 Cadastramento de Objetivos Estratégicos (PDI)")
        
        tab_list_oe, tab_novo_oe = st.tabs(["🔍 Objetivos Cadastrados", "➕ Novo Objetivo Estratégico"])
        
        with tab_list_oe:
            try:
                res_oe = supabase.table("objetivos_estrategicos").select("*").execute()
                if res_oe.data:
                    for oe_item in res_oe.data:
                        with st.expander(f"🎯 `{oe_item['codigo']}` - {oe_item['descricao']}"):
                            col_oe_edit, col_oe_del = st.columns([1, 1])
                            
                            with col_oe_edit:
                                pop_edit_oe = st.popover("✏️ Editar")
                                with pop_edit_oe:
                                    with st.form(f"form_edit_oe_{oe_item['id']}"):
                                        cod_edit = st.text_input("Código", value=oe_item['codigo'])
                                        desc_edit = st.text_area("Descrição", value=oe_item['descricao'])
                                        if st.form_submit_button("Salvar"):
                                            supabase.table("objetivos_estrategicos").update({"codigo": cod_edit, "descricao": desc_edit}).eq("id", oe_item['id']).execute()
                                            st.success("Atualizado!")
                                            st.rerun()
                                            
                            with col_oe_del:
                                pop_del_oe = st.popover("🗑️ Excluir")
                                with pop_del_oe:
                                    st.warning("Confirmar exclusão?")
                                    if st.button("Excluir Objetivo", key=f"btn_del_oe_{oe_item['id']}"):
                                        res_vinc = supabase.table("riscos").select("id").like("objetivo_estrategico", f"%{oe_item['codigo']}%").execute()
                                        if res_vinc.data and len(res_vinc.data) > 0:
                                            st.error(f"❌ Impossível excluir: existem {len(res_vinc.data)} risco(s) vinculados a este objetivo.")
                                        else:
                                            supabase.table("objetivos_estrategicos").delete().eq("id", oe_item['id']).execute()
                                            st.success("Excluído!")
                                            st.rerun()
                else:
                    st.info("Nenhum objetivo estratégico cadastrado.")
            except Exception as e:
                st.error(f"Erro ao carregar Objetivos Estratégicos: {e}")
                
        with tab_novo_oe:
            with st.form("form_cadastrar_oe", clear_on_submit=True):
                codigo_oe = st.text_input("Código do Objetivo*", placeholder="Ex: OE-01, OE-02")
                descricao_oe = st.text_area("Descrição do Objetivo Estratégico*", placeholder="Ex: Promover a excelência no ensino de graduação")
                
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
                            st.error(f"Erro ao salvar: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO 3: CATEGORIAS DE RISCO
    # ---------------------------------------------------------
    elif sub == "Categorias de Risco":
        st.subheader("🏷️ Cadastramento de Categorias de Risco")
        
        tab_list_cat, tab_novo_cat = st.tabs(["🔍 Categorias Cadastradas", "➕ Nova Categoria"])
        
        with tab_list_cat:
            try:
                res_cat = supabase.table("categorias_risco").select("*").execute()
                if res_cat.data:
                    for cat_item in res_cat.data:
                        with st.expander(f"🏷️️ {cat_item['nome']}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                pop_edit_cat = st.popover("✏️ Editar")
                                with pop_edit_cat:
                                    with st.form(f"form_edit_cat_{cat_item['id']}"):
                                        nome_edit = st.text_input("Nome da Categoria", value=cat_item['nome'])
                                        if st.form_submit_button("Salvar"):
                                            supabase.table("categorias_risco").update({"nome": nome_edit}).eq("id", cat_item['id']).execute()
                                            st.success("Atualizado!")
                                            st.rerun()
                            with c2:
                                pop_del_cat = st.popover("🗑️ Excluir")
                                with pop_del_cat:
                                    st.warning("Confirmar exclusão?")
                                    if st.button("Excluir Categoria", key=f"btn_del_cat_{cat_item['id']}"):
                                        res_vinc = supabase.table("riscos").select("id").eq("categoria", cat_item['nome']).execute()
                                        if res_vinc.data and len(res_vinc.data) > 0:
                                            st.error(f"❌ Impossível excluir: existem {len(res_vinc.data)} risco(s) cadastrados nesta categoria.")
                                        else:
                                            supabase.table("categorias_risco").delete().eq("id", cat_item['id']).execute()
                                            st.success("Excluído!")
                                            st.rerun()
                else:
                    st.info("Nenhuma categoria cadastrada.")
            except Exception as e:
                st.error(f"Erro ao carregar Categorias: {e}")
                
        with tab_novo_cat:
            with st.form("form_cadastrar_cat", clear_on_submit=True):
                nome_cat = st.text_input("Nome da Categoria*", placeholder="Ex: Operacional, Estratégico, Financeiro")
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
    # SUB-MÓDULO 4: RISCOS
    # ---------------------------------------------------------
    elif sub == "Riscos":
        st.subheader("📋 Gestão e Cadastro de Riscos Institucionais")
        
        tab1, tab2 = st.tabs(["🔍 Riscos Cadastrados", "➕ Novo Risco"])
        
        with tab1:
            try:
                resposta = supabase.table("riscos").select("*").order("id", desc=True).execute()
                dados = resposta.data
                
                if dados:
                    st.write(f"Total de riscos registrados: **{len(dados)}**")
                    
                    for r_item in dados:
                        nivel = r_item.get('nivel_risco', 1)
                        cor_nivel = "🔴 (Crítico)" if nivel >= 15 else "🟡 (Médio)" if nivel >= 8 else "🟢 (Baixo)"
                        
                        with st.expander(f"🛡️ Risco #{r_item['id']} | {r_item['unidade']} | Nível {nivel} {cor_nivel}"):
                            st.markdown(f"**Evento de Risco:** {r_item['evento_risco']}")
                            st.markdown(f"**Processo:** {r_item['processo']} | **Categoria:** {r_item['categoria']}")
                            st.markdown(f"**Causa:** {r_item['causa']} | **Consequência:** {r_item['consequencia']}")
                            st.markdown(f"**Responsável:** {r_item['responsavel']} | **Situação:** {r_item['situacao']}")
                            
                            col_r_edit, col_r_del = st.columns([1, 1])
                            
                            with col_r_edit:
                                pop_edit_r = st.popover("✏️ Editar Risco")
                                with pop_edit_r:
                                    st.markdown("### Editar Informações do Risco")
                                    with st.form(f"form_edit_risco_{r_item['id']}"):
                                        e_proc = st.text_input("Processo", value=r_item['processo'])
                                        e_evento = st.text_area("Evento de Risco", value=r_item['evento_risco'])
                                        e_causa = st.text_area("Causa", value=r_item['causa'])
                                        e_cons = st.text_area("Consequência", value=r_item['consequencia'])
                                        e_prob = st.slider("Probabilidade", 1, 5, value=r_item['probabilidade'])
                                        e_imp = st.slider("Impacto", 1, 5, value=r_item['impacto'])
                                        e_resp = st.text_input("Responsável", value=r_item['responsavel'])
                                        e_sit = st.selectbox("Situação", ["Identificado", "Em Análise", "Em Tratamento", "Monitorado", "Encerrado/Mitigado"], index=0)
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            novo_nivel = e_prob * e_imp
                                            supabase.table("riscos").update({
                                                "processo": e_proc,
                                                "evento_risco": e_evento,
                                                "causa": e_causa,
                                                "consequencia": e_cons,
                                                "probabilidade": e_prob,
                                                "impacto": e_imp,
                                                "nivel_risco": novo_nivel,
                                                "responsavel": e_resp,
                                                "situacao": e_sit
                                            }).eq("id", r_item['id']).execute()
                                            
                                            supabase.table("risco_historico").insert({
                                                "risco_id": r_item['id'],
                                                "data_alteracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                "responsavel_alteracao": e_resp,
                                                "detalhes": f"Risco editado. Novo Nível: {novo_nivel} (P:{e_prob}, I:{e_imp}). Situação: {e_sit}."
                                            }).execute()
                                            
                                            st.success("Risco atualizado!")
                                            st.rerun()

                            with col_r_del:
                                pop_del_r = st.popover("🗑️ Excluir Risco")
                                with pop_del_r:
                                    st.warning("Deseja realmente excluir este risco e seu histórico?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_r_{r_item['id']}"):
                                        try:
                                            supabase.table("risco_historico").delete().eq("risco_id", r_item['id']).execute()
                                            supabase.table("riscos").delete().eq("id", r_item['id']).execute()
                                            st.success("Risco excluído!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao excluir: {e}")
                else:
                    st.info("Nenhum risco cadastrado até o momento.")
            except Exception as e:
                st.error(f"Erro ao carregar dados do banco: {e}")
                
        with tab2:
            try:
                res_unidades = supabase.table("unidades").select("*").execute().data or []
                res_oe = supabase.table("objetivos_estrategicos").select("codigo, descricao").execute().data or []
                res_cat = supabase.table("categorias_risco").select("nome").execute().data or []
            except Exception as e:
                res_unidades, res_oe, res_cat = [], [], []

            if res_unidades:
                opcoes_unid = [f"{u['codigo']} - {u['sigla']} ({u.get('tipo_unidade', u['nome_extenso'])})" for u in res_unidades]
            else:
                opcoes_unid = ["(Nenhuma unidade cadastrada)"]

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
                            st.error(f"Erro ao salvar o risco no banco de dados: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO 5: CADASTRO DO TEXTO DA TELA INICIAL
    # ---------------------------------------------------------
    elif sub == "Texto da Tela Inicial":
        st.subheader("✍️ Cadastrar / Editar Texto da Tela Inicial")
        st.write("O texto digitado abaixo será exibido dinamicamente na página inicial do aplicativo.")
        
        texto_atual = ""
        try:
            res_txt = supabase.table("configuracoes").select("valor").eq("chave", "texto_pagina_inicial").execute()
            if res_txt.data and len(res_txt.data) > 0:
                texto_atual = res_txt.data[0]["valor"]
        except Exception as e:
            st.warning("Certifique-se de criar a tabela 'configuracoes' no Supabase com os campos 'chave' (text) e 'valor' (text).")

        with st.form("form_texto_inicial"):
            novo_texto = st.text_area(
                "Conteúdo da Tela Inicial (Aceita formatação Markdown)", 
                value=texto_atual, 
                height=250,
                placeholder="Escreva aqui a apresentação do SÍGER, a fundamentação teórica ou avisos gerais..."
            )
            
            submitted_texto = st.form_submit_button("💾 Salvar Texto da Tela Inicial")
            
            if submitted_texto:
                try:
                    supabase.table("configuracoes").upsert({
                        "chave": "texto_pagina_inicial",
                        "valor": novo_texto
                    }).execute()
                    st.success("✅ Texto da tela inicial atualizado com sucesso! Acesse o menu 'Início' para visualizar.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar texto no banco de dados: {e}")

# ---------------------------------------------------------
# DEMAIS PÁGINAS
# ---------------------------------------------------------
else:
    st.title(f"🛠️ {st.session_state.pagina_atual}")
    if st.session_state.sub_pagina_atual:
        st.subheader(f"Área: {st.session_state.sub_pagina_atual}")
    st.info("Módulo em fase de estruturação. Em breve implementaremos as funcionalidades desta área.")
