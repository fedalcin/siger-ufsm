import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime
import os

# ---------------------------------------------------------
# CONEXÃO COM SUPABASE
# ---------------------------------------------------------
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    if url.endswith("/rest/v1"):
        url = url[:-8]
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# ---------------------------------------------------------
# CARREGAMENTO DINÂMICO DA IDENTIDADE VISUAL & FAVICON
# ---------------------------------------------------------
url_logo_siger = None
url_logo_reduzido = None
url_logo_instituicao = None

try:
    res_siger = supabase.table("configuracoes").select("valor").eq("chave", "url_logo_siger").execute()
    if res_siger.data and len(res_siger.data) > 0:
        url_logo_siger = res_siger.data[0]["valor"]

    res_red = supabase.table("configuracoes").select("valor").eq("chave", "url_logo_reduzido").execute()
    if res_red.data and len(res_red.data) > 0:
        url_logo_reduzido = res_red.data[0]["valor"]
        
    res_inst = supabase.table("configuracoes").select("valor").eq("chave", "url_logo_instituicao").execute()
    if res_inst.data and len(res_inst.data) > 0:
        url_logo_instituicao = res_inst.data[0]["valor"]
except:
    pass

# Define o ícone da aba do navegador (Chrome Favicon)
if url_logo_reduzido:
    favicon_app = url_logo_reduzido
elif url_logo_siger:
    favicon_app = url_logo_siger
elif os.path.exists("logo.png"):
    favicon_app = "logo.png"
else:
    favicon_app = "🛡️"

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA E ESTILOS CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="SIGER - Sistema de Gestão de Riscos", 
    page_icon=favicon_app,
    layout="wide"
)

# Estilização CSS personalizada
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        padding-top: 0rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.2rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    div[data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stImage"] {
        margin-top: 0rem !important;
        margin-bottom: 0rem !important;
        padding-top: 0rem !important;
    }

    section[data-testid="stSidebar"] hr {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
    }
    section[data-testid="stSidebar"] h3 {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary {
        background-color: #002147 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-weight: bold !important;
        margin-bottom: 4px !important;
        border: 1px solid #001733 !important;
        transition: background-color 0.3s ease;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary:hover {
        background-color: #003366 !important;
        color: #ffffff !important;
        cursor: pointer;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary p,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    .btn-inicio-sidebar button {
        background-color: #002147 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        width: 100% !important;
        text-align: left !important;
        border: 1px solid #001733 !important;
    }
    .btn-inicio-sidebar button:hover {
        background-color: #003366 !important;
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stExpander"] div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        width: calc(100% - 20px) !important;
        margin-left: 20px !important;
        border: none !important;
        background-color: #f8f9fa !important;
        color: #333333 !important;
        padding-left: 10px !important;
        margin-top: 2px !important;
        margin-bottom: 2px !important;
        border-radius: 4px !important;
        border-left: 3px solid #002147 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] div.stButton > button:hover {
        background-color: #e2e8f0 !important;
        color: #002147 !important;
        font-weight: bold !important;
        border-left: 4px solid #003366 !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
    }
    
    .texto-justificado {
        text-align: justify !important;
        text-justify: inter-word !important;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

TIPOS_UNIDADE_OPCOES = [
    "Unidade Acadêmica",
    "Pró-Reitoria",
    "Diretoria"
]

# Função auxiliar para formatar strings YYYY-MM-DD para DD/MM/AAAA na exibição
def formatar_data_br(data_str):
    if not data_str:
        return "-"
    try:
        dt = datetime.strptime(data_str[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_str

# Função auxiliar para formatar strings de data/hora ISO para DD/MM/AAAA HH:MM na exibição
def formatar_data_hora_br(data_hora_str):
    if not data_hora_str:
        return "-"
    try:
        dt = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return data_hora_str

# ---------------------------------------------------------
# BARRA LATERAL (LOGOTIPO SIGER E MENU EXPANSÍVEL)
# ---------------------------------------------------------
if url_logo_siger:
    st.sidebar.image(url_logo_siger, use_container_width=True)
elif os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.title("SIGER")
    st.sidebar.markdown("**Sistema de Gestão de Riscos**")

st.sidebar.divider()

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Início"
if "sub_pagina_atual" not in st.session_state:
    st.session_state.sub_pagina_atual = None

def navegar_para(pagina, sub_pagina=None):
    st.session_state.pagina_atual = pagina
    st.session_state.sub_pagina_atual = sub_pagina

st.sidebar.subheader("Menu Principal")

st.sidebar.markdown('<div class="btn-inicio-sidebar">', unsafe_allow_html=True)
if st.sidebar.button("🏠 Início", use_container_width=True, key="btn_inicio_top"):
    navegar_para("Início")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# 1. GRUPO: ADMINISTRAÇÃO
with st.sidebar.expander("⚙️ Administração", expanded=False):
    if st.button("👥 Usuários e Permissões", key="btn_adm_usr", use_container_width=True):
        navegar_para("Administração do Sistema", "Usuários")
    if st.button("🔧 Configurações Gerais", key="btn_adm_cfg", use_container_width=True):
        navegar_para("Administração do Sistema", "Configurações")

# 2. GRUPO: CADASTROS
with st.sidebar.expander("📝 Cadastros", expanded=False):
    if st.button("🏢 Unidades", key="btn_cad_unid", use_container_width=True):
        navegar_para("Cadastros", "Unidades")
    if st.button("🎯 Objetivos Estratégicos", key="btn_cad_oe", use_container_width=True):
        navegar_para("Cadastros", "Objetivos Estratégicos")
    if st.button("🏷️ Categorias de Risco", key="btn_cad_cat", use_container_width=True):
        navegar_para("Cadastros", "Categorias de Risco")
    if st.button("📋 Riscos", key="btn_cad_risco", use_container_width=True):
        navegar_para("Cadastros", "Riscos")
    if st.button("🖼️ Identidade Visual", key="btn_cad_id_vis", use_container_width=True):
        navegar_para("Cadastros", "Identidade Visual")
    if st.button("📚 Documentos da Biblioteca", key="btn_cad_doc_bib", use_container_width=True):
        navegar_para("Cadastros", "Documentos da Biblioteca")
    if st.button("✍ Texto da Tela Inicial", key="btn_cad_txt", use_container_width=True):
        navegar_para("Cadastros", "Texto da Tela Inicial")

# 3. GRUPO: PLANOS DE TRATAMENTO
with st.sidebar.expander("🛡️ Planos de Tratamento", expanded=False):
    if st.button("📋 Ações de Mitigação", key="btn_pt_acoes", use_container_width=True):
        navegar_para("Planos de Tratamento", "Ações")

# 4. GRUPO: MONITORAMENTO
with st.sidebar.expander("🔄 Monitoramento", expanded=False):
    if st.button("📌 Acompanhamento de Riscos", key="btn_mon_acomp", use_container_width=True):
        navegar_para("Monitoramento", "Acompanhamento")
    if st.button("📅 Matriz de Revisões", key="btn_mon_rev", use_container_width=True):
        navegar_para("Monitoramento", "Revisões")

# 5. GRUPO: INTELIGÊNCIA GERENCIAL
with st.sidebar.expander("🧠 Inteligência Gerencial", expanded=False):
    if st.button("💡 Análise de Tendências", key="btn_ig_tend", use_container_width=True):
        navegar_para("Inteligência Gerencial", "Tendências")

# 6. GRUPO: DASHBOARDS
with st.sidebar.expander("📊 Dashboards", expanded=False):
    if st.button("📈 Painel Geral", key="btn_dash_geral", use_container_width=True):
        navegar_para("Dashboards", "Painel Geral")
    if st.button("🎯 Matriz de Risco (5x5)", key="btn_dash_matriz", use_container_width=True):
        navegar_para("Dashboards", "Matriz 5x5")

# 7. GRUPO: BIBLIOTECA
with st.sidebar.expander("📚 Biblioteca", expanded=False):
    if st.button("📄 Documentos e Normativas", key="btn_bib_doc", use_container_width=True):
        navegar_para("Biblioteca", "Documentos")

# 8. GRUPO: RELATÓRIOS
with st.sidebar.expander("📑 Relatórios", expanded=False):
    if st.button("🖨️ Relatório de Riscos (PDF/Excel)", key="btn_rel_riscos", use_container_width=True):
        navegar_para("Relatórios", "Relatório Riscos")

# 9. GRUPO: TRANSPARÊNCIA
with st.sidebar.expander("🌐 Transparência", expanded=False):
    if st.button("🔓 Painel Público", key="btn_transp_pub", use_container_width=True):
        navegar_para("Transparência", "Painel Público")

# ---------------------------------------------------------
# PÁGINA: INÍCIO
# ---------------------------------------------------------
if st.session_state.pagina_atual == "Início":
    if url_logo_instituicao:
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.title("SIGER - Sistema de Gestão de Riscos")
        with col_t2:
            st.image(url_logo_instituicao, width=180)
    else:
        st.title("SIGER - Sistema de Gestão de Riscos")
    
    texto_inicio_personalizado = ""
    try:
        res_cfg = supabase.table("configuracoes").select("valor").eq("chave", "texto_pagina_inicial").execute()
        if res_cfg.data and len(res_cfg.data) > 0:
            texto_inicio_personalizado = res_cfg.data[0]["valor"]
    except Exception as e:
        texto_inicio_personalizado = ""

    if texto_inicio_personalizado:
        st.markdown(f'<div class="texto-justificado">{texto_inicio_personalizado}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="texto-justificado">
        Bem-vindo ao <b>SIGER</b>, a solução integrada para mapeamento, avaliação e monitoramento de riscos 
        institucionais no âmbito das Instituições Federais de Ensino Superior (IFES).
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    st.info("👈 Utilize o menu lateral para navegar entre os módulos do sistema.")

# ---------------------------------------------------------
# PÁGINA: PLANOS DE TRATAMENTO / AÇÕES DE MITIGAÇÃO
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Planos de Tratamento":
    st.title("🛡️ Planos de Tratamento e Mitigação de Riscos")
    
    tab_list_acoes, tab_nova_acao = st.tabs(["🔍 Ações Cadastradas", "➕ Cadastrar Nova Ação de Mitigação"])
    
    with tab_list_acoes:
        try:
            res_acoes = supabase.table("acoes_tratamento").select("*, riscos(id, evento, unidade)").order("risco_id").order("numero_sequencial").execute()
            
            if res_acoes.data:
                st.write(f"Total de ações de tratamento registradas: **{len(res_acoes.data)}**")
                
                for acao_item in res_acoes.data:
                    r_id = acao_item["risco_id"]
                    seq = acao_item["numero_sequencial"]
                    carater = acao_item["carater_acao"]
                    nome_acao = acao_item["acao"]
                    
                    dados_risco_rel = acao_item.get("riscos") or {}
                    evento_txt = dados_risco_rel.get("evento", "Não especificado")
                    
                    badge_carater = "🟢" if carater == "Preventivo" else "🟡" if carater == "Corretivo" else "🔵"
                    
                    # Formatação visual das datas no padrão DD/MM/AAAA
                    dt_inicio_fmt = formatar_data_br(acao_item.get('previsao_data_inicio'))
                    dt_conclusao_fmt = formatar_data_br(acao_item.get('previsao_data_conclusao'))
                    
                    with st.expander(f"{badge_carater} Risco #{r_id} | Ação {seq}: {nome_acao}"):
                        st.markdown(f"**Risco:** {evento_txt}")
                        st.markdown(f"**Caráter da Ação:** {carater}")
                        st.markdown(f"**Objetivo da Ação:** {acao_item['objetivo_acao']}")
                        st.markdown(f"**Unidade Responsável:** {acao_item['unidade_responsavel']}")
                        st.markdown(f"**Responsável pela Implementação:** {acao_item['nome_responsavel_implementacao']}")
                        st.markdown(f"**Como será Implementada:** {acao_item['como_sera_implementada']}")
                        st.markdown(f"**Período de Execução:** {dt_inicio_fmt} até {dt_conclusao_fmt}")
                        
                        col_ac_edit, col_ac_del = st.columns([1, 1])
                        
                        with col_ac_edit:
                            pop_edit_ac = st.popover("✏ Editar Ação")
                            with pop_edit_ac:
                                with st.form(f"form_edit_acao_{r_id}_{seq}"):
                                    edit_nome_ac = st.text_input("Ação", value=nome_acao)
                                    
                                    idx_carater = ["Preventivo", "Corretivo", "Compensatório"].index(carater) if carater in ["Preventivo", "Corretivo", "Compensatório"] else 0
                                    edit_carater = st.selectbox("Caráter da Ação", ["Preventivo", "Corretivo", "Compensatório"], index=idx_carater)
                                    
                                    edit_obj = st.text_area("Objetivo da Ação", value=acao_item['objetivo_acao'])
                                    edit_resp = st.text_input("Responsável pela Implementação", value=acao_item['nome_responsavel_implementacao'])
                                    edit_como = st.text_area("Como será Implementada", value=acao_item['como_sera_implementada'])
                                    
                                    d_i = datetime.strptime(acao_item['previsao_data_inicio'], "%Y-%m-%d").date() if acao_item.get('previsao_data_inicio') else datetime.now().date()
                                    d_f = datetime.strptime(acao_item['previsao_data_conclusao'], "%Y-%m-%d").date() if acao_item.get('previsao_data_conclusao') else datetime.now().date()
                                    
                                    edit_dt_i = st.date_input("Previsão Início", value=d_i, format="DD/MM/YYYY")
                                    edit_dt_f = st.date_input("Previsão Conclusão", value=d_f, format="DD/MM/YYYY")
                                    
                                    if st.form_submit_button("💾 Salvar Alterações"):
                                        if edit_dt_f < edit_dt_i:
                                            st.error("A data de conclusão não pode ser anterior à data de início.")
                                        else:
                                            supabase.table("acoes_tratamento").update({
                                                "acao": edit_nome_ac,
                                                "carater_acao": edit_carater,
                                                "objetivo_acao": edit_obj,
                                                "nome_responsavel_implementacao": edit_resp,
                                                "como_sera_implementada": edit_como,
                                                "previsao_data_inicio": edit_dt_i.strftime("%Y-%m-%d"),
                                                "previsao_data_conclusao": edit_dt_f.strftime("%Y-%m-%d")
                                            }).eq("risco_id", r_id).eq("numero_sequencial", seq).execute()
                                            
                                            st.success("Ação atualizada!")
                                            st.rerun()

                        with col_ac_del:
                            pop_del_ac = st.popover("🗑️ Excluir Ação")
                            with pop_del_ac:
                                st.warning("Deseja remover esta ação de mitigação?")
                                if st.button("Confirmar Exclusão", key=f"btn_del_ac_{r_id}_{seq}"):
                                    try:
                                        supabase.table("acoes_tratamento").delete().eq("risco_id", r_id).eq("numero_sequencial", seq).execute()
                                        st.success("Ação removida com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao excluir ação: {e}")
            else:
                st.info("Nenhuma ação de tratamento/mitigação cadastrada até o momento.")
        except Exception as e:
            st.error(f"Erro ao carregar ações de tratamento: {e}")
            
    with tab_nova_acao:
        try:
            res_riscos_db = supabase.table("riscos").select("id, evento, unidade").order("id").execute().data or []
            res_unid_db = supabase.table("unidades").select("sigla, nome_extenso").order("sigla").execute().data or []
        except Exception as e:
            res_riscos_db, res_unid_db = [], []
            
        if not res_riscos_db:
            st.warning("⚠️ É necessário ter pelo menos um Risco cadastrado no sistema para criar um Plano de Tratamento.")
        else:
            mapa_riscos = {f"Risco #{r['id']} - {r['evento'] if r['evento'] else 'Sem Risco'}" : r['id'] for r in res_riscos_db}
            
            if res_unid_db:
                opcoes_unid_siglas = [u['sigla'] for u in res_unid_db]
            else:
                opcoes_unid_siglas = ["S/U"]

            risco_selecionado_label = st.selectbox("Selecione o Risco Mapeado*", options=list(mapa_riscos.keys()))
            id_risco_sel = mapa_riscos[risco_selecionado_label]
            
            try:
                res_seq = supabase.table("acoes_tratamento").select("numero_sequencial").eq("risco_id", id_risco_sel).order("numero_sequencial", desc=True).limit(1).execute()
                prox_seq = (res_seq.data[0]["numero_sequencial"] + 1) if res_seq.data else 1
            except:
                prox_seq = 1
                
            st.info(f"📌 Esta será a **Ação nº {prox_seq}** associada ao **Risco #{id_risco_sel}**.")

            with st.form("form_cadastrar_acao_tratamento", clear_on_submit=True):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    acao_input = st.text_input("Ação de Mitigação*", placeholder="Ex: Implantar rotina diária de backup automatizado")
                    carater_sel = st.selectbox("Caráter da Ação*", options=["Preventivo", "Corretivo", "Compensatório"])
                    unidade_resp_sel = st.selectbox("Unidade Responsável pela Ação*", options=opcoes_unid_siglas)
                with col_a2:
                    nome_resp_input = st.text_input("Nome do Responsável pela Implementação*", placeholder="Ex: João da Silva (Coordenador de TI)")
                    dt_inicio = st.date_input("Previsão da Data do Início*", datetime.now(), format="DD/MM/YYYY")
                    dt_conclusao = st.date_input("Previsão da Data da Conclusão*", datetime.now(), format="DD/MM/YYYY")

                objetivo_input = st.text_area("Objetivo da Ação*", placeholder="O que se pretende alcançar com esta ação?")
                como_input = st.text_area("Como será Implementada a Ação*", placeholder="Descreva o passo a passo e o procedimento operacional...")

                st.caption("* Campos de preenchimento obrigatório.")
                submitted_acao = st.form_submit_button("💾 Salvar Ação de Tratamento")

                if submitted_acao:
                    if not acao_input or not objetivo_input or not nome_resp_input or not como_input:
                        st.warning("Por favor, preencha todos os campos obrigatórios do formulário.")
                    elif dt_conclusao < dt_inicio:
                        st.error("A Previsão da Data de Conclusão não pode ser anterior à Data do Início.")
                    else:
                        dados_nova_acao = {
                            "risco_id": id_risco_sel,
                            "numero_sequencial": prox_seq,
                            "acao": acao_input,
                            "carater_acao": carater_sel,
                            "objetivo_acao": objetivo_input,
                            "unidade_responsavel": unidade_resp_sel,
                            "nome_responsavel_implementacao": nome_resp_input,
                            "como_sera_implementada": como_input,
                            "previsao_data_inicio": dt_inicio.strftime("%Y-%m-%d"),
                            "previsao_data_conclusao": dt_conclusao.strftime("%Y-%m-%d")
                        }
                        try:
                            supabase.table("acoes_tratamento").insert(dados_nova_acao).execute()
                            st.success(f"✅ Ação nº {prox_seq} para o Risco #{id_risco_sel} cadastrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar ação no banco de dados: {e}")

# ---------------------------------------------------------
# PÁGINA: CADASTROS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Cadastros":
    st.title("📝 Módulo de Cadastros")
    sub = st.session_state.sub_pagina_atual or "Unidades"
    
    # ---------------------------------------------------------
    # SUB-MÓDULO: UNIDADES (AJUSTADO PARA TRATAMENTO DE EXCLUSÃO E RLS)
    # ---------------------------------------------------------
    if sub == "Unidades":
        st.subheader("🏢 Cadastramento de Unidades / Setores Institucionais")
        tab_list_unid, tab_novo_unid = st.tabs(["🔍 Unidades Cadastradas", "➕ Nova Unidade"])
        
        with tab_list_unid:
            try:
                # Consulta ordenando pela sigla limpa
                resposta_unid = supabase.table("unidades").select("*").order("sigla").execute()
                dados_unid = resposta_unid.data
                
                if dados_unid:
                    st.write(f"Total de unidades cadastradas: **{len(dados_unid)}**")
                    for item in dados_unid:
                        sigla_item = str(item['sigla']).strip()
                        nome_item = item.get('nome_extenso', '')
                        tipo_exibicao = item.get('tipo_unidade', 'Não informado')
                        
                        with st.expander(f"📍 **{sigla_item}** | {nome_item} ({tipo_exibicao})"):
                            col_info, col_acoes = st.columns([3, 1])
                            with col_info:
                                st.write(f"**Sigla:** {sigla_item}")
                                st.write(f"**Nome por Extenso:** {nome_item}")
                                st.write(f"**Tipo da Unidade:** {tipo_exibicao}")
                            
                            with col_acoes:
                                modal_edit = st.popover("✏️ Editar")
                                with modal_edit:
                                    st.markdown("### Editar Unidade")
                                    with st.form(f"form_edit_unid_{sigla_item}"):
                                        st.write(f"**Sigla:** `{sigla_item}` (Chave Primária)")
                                        edit_nome = st.text_input("Nome Extenso", value=nome_item)
                                        val_atual = item.get('tipo_unidade')
                                        idx_tipo = TIPOS_UNIDADE_OPCOES.index(val_atual) if val_atual in TIPOS_UNIDADE_OPCOES else 0
                                        edit_tipo = st.selectbox("Tipo da Unidade*", options=TIPOS_UNIDADE_OPCOES, index=idx_tipo)
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            try:
                                                supabase.table("unidades").update({
                                                    "nome_extenso": edit_nome,
                                                    "tipo_unidade": edit_tipo
                                                }).eq("sigla", sigla_item).execute()
                                                st.toast("Unidade atualizada com sucesso!", icon="✅")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao atualizar: {e}")

                                modal_del = st.popover("🗑️ Excluir")
                                with modal_del:
                                    st.warning(f"Tem certeza que deseja excluir a unidade '{sigla_item}'?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_unid_{sigla_item}"):
                                        try:
                                            # Checagem de Riscos
                                            res_riscos = supabase.table("riscos").select("id").eq("unidade", sigla_item).execute()
                                            if res_riscos.data and len(res_riscos.data) > 0:
                                                st.error(f"❌ Não é possível excluir '{sigla_item}'. Existem {len(res_riscos.data)} risco(s) vinculados.")
                                            else:
                                                # Executa a exclusão com tratamento completo do retorno
                                                res_del = supabase.table("unidades").delete().eq("sigla", sigla_item).execute()
                                                
                                                # Se a política de RLS bloquear, o Supabase não apaga nenhuma linha e retorna lista vazia
                                                if hasattr(res_del, 'data') and len(res_del.data) == 0:
                                                    st.error("⚠️ A exclusão foi bloqueada pelas políticas de segurança (RLS) do Supabase ou a sigla não foi localizada. Habilite a regra de 'DELETE' para a role 'anon/authenticated' no console do Supabase.")
                                                else:
                                                    st.toast(f"Unidade '{sigla_item}' excluída com sucesso!", icon="🗑️")
                                                    st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao tentar excluir: {e}")
                else:
                    st.info("Nenhuma unidade cadastrada.")
            except Exception as e:
                st.error(f"Erro ao carregar unidades: {e}")
                
        with tab_novo_unid:
            with st.form("form_cadastrar_unidade", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    sigla = st.text_input("Sigla da Unidade*", placeholder="Ex: PRAE, PRPGP, CCSH, REITORIA").upper().strip()
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
                            "sigla": sigla,
                            "nome_extenso": nome_extenso,
                            "tipo_unidade": tipo_unidade_sel
                        }
                        try:
                            supabase.table("unidades").insert(dados_nova_unidade).execute()
                            st.toast(f"✅ Unidade '{sigla}' registrada!", icon="🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar unidade: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO: OBJETIVOS ESTRATÉGICOS
    # ---------------------------------------------------------
    elif sub == "Objetivos Estratégicos":
        st.subheader("🎯 Cadastramento de Objetivos Estratégicos (PDI)")
        tab_list_oe, tab_novo_oe = st.tabs(["🔍 Objetivos Cadastrados", "➕ Novo Objetivo Estratégico"])
        
        with tab_list_oe:
            try:
                res_oe = supabase.table("objetivos_estrategicos").select("*").order("codigo").execute()
                if res_oe.data:
                    st.write(f"Total de objetivos cadastrados: **{len(res_oe.data)}**")
                    for oe_item in res_oe.data:
                        cod_oe = oe_item['codigo']
                        desc_oe = oe_item['descricao']
                        desafio_oe = oe_item.get('desafio', '')
                        dimensao_oe = oe_item.get('dimensao', '')
                        
                        with st.expander(f"🎯 `{cod_oe}` - {desc_oe}"):
                            st.markdown(f"**Dimensão:** {dimensao_oe}")
                            st.markdown(f"**Desafio:** {desafio_oe}")
                            
                            col_oe_edit, col_oe_del = st.columns([1, 1])
                            
                            with col_oe_edit:
                                pop_edit_oe = st.popover("✏️ Editar Objetivo")
                                with pop_edit_oe:
                                    with st.form(f"form_edit_oe_{cod_oe}"):
                                        st.write(f"**Código:** `{cod_oe}`")
                                        desc_edit = st.text_area("Descrição*", value=desc_oe)
                                        dimensao_edit = st.text_input("Dimensão*", value=dimensao_oe)
                                        desafio_edit = st.text_area("Desafio*", value=desafio_oe)
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            if not desc_edit or not dimensao_edit or not desafio_edit:
                                                st.warning("Preencha todos os campos obrigatórios.")
                                            else:
                                                try:
                                                    supabase.table("objetivos_estrategicos").update({
                                                        "descricao": desc_edit,
                                                        "dimensao": dimensao_edit,
                                                        "desafio": desafio_edit
                                                    }).eq("codigo", cod_oe).execute()
                                                    st.success("Objetivo Estratégico atualizado!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro ao atualizar: {e}")
                                            
                            with col_oe_del:
                                pop_del_oe = st.popover("🗑️ Excluir Objetivo")
                                with pop_del_oe:
                                    st.warning(f"Confirmar exclusão do objetivo '{cod_oe}'?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_oe_{cod_oe}"):
                                        try:
                                            res_vinc = supabase.table("riscos").select("id").eq("objetivo_estrategico", cod_oe).execute()
                                            if res_vinc.data and len(res_vinc.data) > 0:
                                                st.error(f"❌ Impossível excluir: existem {len(res_vinc.data)} risco(s) vinculados a este objetivo.")
                                            else:
                                                supabase.table("objetivos_estrategicos").delete().eq("codigo", cod_oe).execute()
                                                st.success("Objetivo Estratégico excluído!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao excluir: {e}")
                else:
                    st.info("Nenhum objetivo estratégico cadastrado.")
            except Exception as e:
                st.error(f"Erro ao carregar Objetivos Estratégicos: {e}")
                
        with tab_novo_oe:
            with st.form("form_cadastrar_oe", clear_on_submit=True):
                col_o1, col_o2 = st.columns(2)
                with col_o1:
                    codigo_oe = st.text_input("Código do Objetivo*", placeholder="Ex: OE-01, OE-02")
                    dimensao_oe = st.text_input("Dimensão*", placeholder="Ex: Ensino, Governança, Infraestrutura, Pessoas")
                with col_o2:
                    descricao_oe = st.text_area("Descrição do Objetivo Estratégico*", placeholder="Ex: Promover a excelência no ensino de graduação")
                
                desafio_oe = st.text_area("Desafio*", placeholder="Ex: Ampliar o uso de tecnologias educacionais inovadoras e metodologias ativas")
                
                st.caption("* Todos os campos são de preenchimento obrigatório.")
                submitted_oe = st.form_submit_button("💾 Salvar Objetivo Estratégico")
                
                if submitted_oe:
                    if not codigo_oe or not descricao_oe or not dimensao_oe or not desafio_oe:
                        st.warning("Por favor, preencha o Código, a Descrição, a Dimensão e o Desafio.")
                    else:
                        try:
                            supabase.table("objetivos_estrategicos").insert({
                                "codigo": codigo_oe,
                                "descricao": descricao_oe,
                                "dimensao": dimensao_oe,
                                "desafio": desafio_oe
                            }).execute()
                            st.success(f"✅ Objetivo Estratégico '{codigo_oe}' cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar objetivo estratégico: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO: CATEGORIAS DE RISCOS
    # ---------------------------------------------------------
    elif sub == "Categorias de Risco":
        st.subheader("🏷 Cadastramento de Categorias de Risco (Tipo e Sub-tipo)")
        tab_list_cat, tab_novo_cat = st.tabs(["🔍 Categorias Cadastradas", "➕ Nova Categoria"])
        
        with tab_list_cat:
            try:
                res_cat = supabase.table("categorias_riscos").select("*").order("tipo").execute()
                if res_cat.data:
                    st.write(f"Total de categorias cadastradas: **{len(res_cat.data)}**")
                    for cat_item in res_cat.data:
                        tipo_val = cat_item.get('tipo', 'Não Informado')
                        subtipo_val = cat_item.get('sub_tipo', '')
                        detalhamento_val = cat_item.get('detalhamento', '')
                        
                        titulo_cat = f"🏷️ **{tipo_val}**" + (f" / *{subtipo_val}*" if subtipo_val else "")
                        
                        with st.expander(titulo_cat):
                            if detalhamento_val:
                                st.markdown(f"**Detalhamento:** {detalhamento_val}")
                                
                            c1, c2 = st.columns(2)
                            with c1:
                                pop_edit_cat = st.popover("✏ Edit Categoria")
                                with pop_edit_cat:
                                    with st.form(f"form_edit_cat_{cat_item['id']}"):
                                        tipo_edit = st.text_input("Tipo de Risco*", value=tipo_val)
                                        subtipo_edit = st.text_input("Sub-tipo de Risco*", value=subtipo_val)
                                        detalhamento_edit = st.text_area("Detalhamento", value=detalhamento_val or "")
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            if not tipo_edit or not subtipo_edit:
                                                st.warning("Tipo e Sub-tipo são obrigatórios.")
                                            else:
                                                supabase.table("categorias_riscos").update({
                                                    "tipo": tipo_edit,
                                                    "sub_tipo": subtipo_edit,
                                                    "detalhamento": detalhamento_edit
                                                }).eq("id", cat_item['id']).execute()
                                                st.success("Categoria atualizada com sucesso!")
                                                st.rerun()
                            with c2:
                                pop_del_cat = st.popover("🗑️ Excluir Categoria")
                                with pop_del_cat:
                                    st.warning("Confirmar exclusão desta categoria?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_cat_{cat_item['id']}"):
                                        try:
                                            res_vinc = supabase.table("riscos").select("id").eq("categoria_risco", cat_item['id']).execute()
                                            if res_vinc.data and len(res_vinc.data) > 0:
                                                st.error(f"❌ Impossível excluir: existem {len(res_vinc.data)} risco(s) vinculados a esta categoria.")
                                            else:
                                                supabase.table("categorias_riscos").delete().eq("id", cat_item['id']).execute()
                                                st.success("Categoria excluída!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao excluir: {e}")
                else:
                    st.info("Nenhuma categoria de risco cadastrada.")
            except Exception as e:
                st.error(f"Erro ao carregar Categorias de Risco: {e}")
                
        with tab_novo_cat:
            with st.form("form_cadastrar_cat", clear_on_submit=True):
                col_cat1, col_cat2 = st.columns(2)
                with col_cat1:
                    tipo_cat = st.text_input("Tipo de Risco*", placeholder="Ex: Operacional, Estratégico, Financeiro, Legal")
                with col_cat2:
                    subtipo_cat = st.text_input("Sub-tipo de Risco*", placeholder="Ex: Falha de Sistema, Fraude Interna, Perda Orçamentária")
                
                detalhamento_cat = st.text_area("Detalhamento (Opcional)", placeholder="Descrição complementar do tipo/sub-tipo de risco...")
                
                st.caption("* Tipo e Sub-tipo são de preenchimento obrigatório.")
                submitted_cat = st.form_submit_button("💾 Salvar Categoria")
                
                if submitted_cat:
                    if not tipo_cat or not subtipo_cat:
                        st.warning("Por favor, preencha tanto o Tipo quanto o Sub-tipo.")
                    else:
                        try:
                            supabase.table("categorias_riscos").insert({
                                "tipo": tipo_cat,
                                "sub_tipo": subtipo_cat,
                                "detalhamento": detalhamento_cat
                            }).execute()
                            st.success(f"✅ Categoria '{tipo_cat} / {subtipo_cat}' cadastrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar categoria no banco: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO: RISCOS
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
                        dt_ident_fmt = formatar_data_br(r_item.get('data_identificacao'))
                        
                        with st.expander(f"🛡️ Risco #{r_item['id']} | {r_item['unidade']} | Nível {nivel} {cor_nivel}"):
                            st.markdown(f"**Risco:** {r_item.get('evento', '')}")
                            st.markdown(f"**Causa:** {r_item.get('causa', '')} | **Consequência:** {r_item.get('consequencia', '')}")
                            st.markdown(f"**Gestor:** {r_item.get('gestor_risco', '')} | **Situação:** {r_item.get('situacao_status', '')}")
                            st.markdown(f"**Data de Identificação:** {dt_ident_fmt}")
                            
                            col_r_edit, col_r_del = st.columns([1, 1])
                            
                            with col_r_edit:
                                pop_edit_r = st.popover("✏️ Editar Risco")
                                with pop_edit_r:
                                    st.markdown("### Editar Informações do Risco")
                                    with st.form(f"form_edit_risco_{r_item['id']}"):
                                        e_evento = st.text_area("Risco", value=r_item.get('evento', ''))
                                        e_causa = st.text_area("Causa", value=r_item.get('causa', ''))
                                        e_cons = st.text_area("Consequência", value=r_item.get('consequencia', ''))
                                        e_prob = st.slider("Probabilidade", 1, 5, value=r_item.get('probabilidade', 1))
                                        e_imp = st.slider("Impacto", 1, 5, value=r_item.get('impacto', 1))
                                        e_resp = st.text_input("Gestor do Risco", value=r_item.get('gestor_risco', ''))
                                        
                                        options_status = ['Identificado', 'Em Análise', 'Em Tratamento', 'Monitorado', 'Encerrado/Mitigado']
                                        curr_status = r_item.get('situacao_status', 'Identificado')
                                        idx_st = options_status.index(curr_status) if curr_status in options_status else 0
                                        e_sit = st.selectbox("Situação", options_status, index=idx_st)
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            novo_nivel = e_prob * e_imp
                                            supabase.table("riscos").update({
                                                "evento": e_evento,
                                                "causa": e_causa,
                                                "consequencia": e_cons,
                                                "probabilidade": e_prob,
                                                "impacto": e_imp,
                                                "nivel_risco": novo_nivel,
                                                "gestor_risco": e_resp,
                                                "situacao_status": e_sit
                                            }).eq("id", r_item['id']).execute()
                                            
                                            st.success("Risco atualizado!")
                                            st.rerun()

                            with col_r_del:
                                pop_del_r = st.popover("🗑️ Excluir Risco")
                                with pop_del_r:
                                    st.warning("Deseja realmente excluir este risco?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_r_{r_item['id']}"):
                                        try:
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
                res_unidades = supabase.table("unidades").select("sigla, nome_extenso").order("sigla").execute().data or []
                res_oe = supabase.table("objetivos_estrategicos").select("codigo, descricao").order("codigo").execute().data or []
                res_cat = supabase.table("categorias_riscos").select("id, tipo, sub_tipo").order("tipo").execute().data or []
            except Exception as e:
                res_unidades, res_oe, res_cat = [], [], []

            mapa_unidades = {f"{u['sigla']} - {u['nome_extenso']}": u['sigla'] for u in res_unidades} if res_unidades else {"S/U": None}
            mapa_oe = {f"{o['codigo']} - {o['descricao']}": o['codigo'] for o in res_oe} if res_oe else {"Nenhum": None}
            mapa_cat = {f"{c['tipo']} / {c['sub_tipo']}": c['id'] for c in res_cat} if res_cat else {"Nenhuma": None}

            with st.form("form_cadastrar_risco", clear_on_submit=True):
                st.markdown("##### 1. Contexto do Risco")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    unid_label = st.selectbox("Unidade Responsável*", options=list(mapa_unidades.keys()))
                with col_c2:
                    oe_label = st.selectbox("Objetivo Estratégico Relacionado*", options=list(mapa_oe.keys()))
                    cat_label = st.selectbox("Categoria do Risco*", options=list(mapa_cat.keys()))

                st.markdown("##### 2. Identificação e Análise do Risco")
                evento_input = st.text_area("Risco*", placeholder="Descreva o risco")
                
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    causa_input = st.text_area("Causa(s)*", placeholder="Quais fatores geram este risco?")
                with col_i2:
                    consequencia_input = st.text_area("Consequência(s)*", placeholder="Quais os impactos?")

                st.markdown("##### 3. Avaliação Qualitativa")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    prob_val = st.slider("Probabilidade (1 a 5)", 1, 5, 3)
                with col_a2:
                    imp_val = st.slider("Impacto (1 a 5)", 1, 5, 3)

                st.markdown("##### 4. Governança, Controle e Prazos")
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    resp_input = st.text_input("Gestor do Risco*", placeholder="Nome do servidor responsável")
                    situacao_sel = st.selectbox("Situação Inicial*", ['Identificado', 'Em Análise', 'Em Tratamento', 'Monitorado', 'Encerrado/Mitigado'])
                with col_g2:
                    dt_identificacao = st.date_input("Data de Identificação*", datetime.now(), format="DD/MM/YYYY")
                with col_g3:
                    periodicidade_sel = st.selectbox("Periodicidade de Revisão", ["Mensal", "Trimestral", "Semestral", "Anual"])

                st.caption("* Campos obrigatórios.")
                submitted_risco = st.form_submit_button("💾 Salvar Risco")
                
                if submitted_risco:
                    if not evento_input or not resp_input:
                        st.warning("Preencha os campos obrigatórios (Risco e Gestor do Risco).")
                    else:
                        nivel_calc = prob_val * imp_val
                        novo_risco_dados = {
                            "unidade": mapa_unidades[unid_label],
                            "objetivo_estrategico": mapa_oe[oe_label],
                            "categoria_risco": mapa_cat[cat_label],
                            "evento": evento_input,
                            "causa": causa_input,
                            "consequencia": consequencia_input,
                            "probabilidade": prob_val,
                            "impacto": imp_val,
                            "nivel_risco": nivel_calc,
                            "gestor_risco": resp_input,
                            "data_identificacao": dt_identificacao.strftime("%Y-%m-%d"),
                            "periodicidade_revisao": periodicidade_sel,
                            "situacao_status": situacao_sel
                        }
                        try:
                            supabase.table("riscos").insert(novo_risco_dados).execute()
                            st.success("✅ Risco registrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar o risco no banco de dados: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO: IDENTIDADE VISUAL
    # ---------------------------------------------------------
    elif sub == "Identidade Visual":
        st.subheader("🖼️ Gestão da Identidade Visual do Sistema")
        st.write("Personalize os logotipos exibidos no aplicativo SIGER.")
        st.divider()
        
        col_img1, col_img2, col_img3 = st.columns(3)
        
        with col_img1:
            st.markdown("### 1. Logotipo Completo SIGER")
            if url_logo_siger:
                st.image(url_logo_siger, width=180, caption="Logotipo Completo Atual")
            else:
                st.info("Nenhum logotipo completo enviado.")
                
            with st.form("form_logo_siger", clear_on_submit=True):
                arq_siger = st.file_uploader("Enviar Logo Completo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="upl_siger")
                if st.form_submit_button("💾 Salvar Logo Completo"):
                    if arq_siger:
                        try:
                            nome_siger = f"logo_siger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            supabase.storage.from_("identidade_visual").upload(
                                path=nome_siger, file=arq_siger.getvalue(), file_options={"content-type": arq_siger.type}
                            )
                            url_pub_siger = supabase.storage.from_("identidade_visual").get_public_url(nome_siger)
                            supabase.table("configuracoes").upsert({"chave": "url_logo_siger", "valor": url_pub_siger}).execute()
                            st.success("✅ Logo Completo do SIGER atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao enviar imagem: {e}")

        with col_img2:
            st.markdown("### 2. Logotipo Reduzido / Ícone")
            if url_logo_reduzido:
                st.image(url_logo_reduzido, width=80, caption="Ícone / Favicon Atual")
            else:
                st.info("Nenhum logotipo reduzido enviado.")
                
            with st.form("form_logo_reduzido", clear_on_submit=True):
                arq_red = st.file_uploader("Enviar Ícone/Logo Reduzido (PNG/JPG/ICO)", type=["png", "jpg", "jpeg", "ico"], key="upl_red")
                if st.form_submit_button("💾 Salvar Logo Reduzido"):
                    if arq_red:
                        try:
                            nome_red = f"logo_reduzido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            supabase.storage.from_("identidade_visual").upload(
                                path=nome_red, file=arq_red.getvalue(), file_options={"content-type": arq_red.type}
                            )
                            url_pub_red = supabase.storage.from_("identidade_visual").get_public_url(nome_red)
                            supabase.table("configuracoes").upsert({"chave": "url_logo_reduzido", "valor": url_pub_red}).execute()
                            st.success("✅ Logo Reduzido atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao enviar imagem: {e}")

        with col_img3:
            st.markdown("### 3. Logotipo da Instituição")
            if url_logo_instituicao:
                st.image(url_logo_instituicao, width=180, caption="Logo Institucional Atual")
            else:
                st.info("Nenhum logo da instituição enviado.")
                
            with st.form("form_logo_inst", clear_on_submit=True):
                arq_inst = st.file_uploader("Enviar Logo da Instituição (PNG/JPG)", type=["png", "jpg", "jpeg"], key="upl_inst")
                if st.form_submit_button("💾 Salvar Logo Instituição"):
                    if arq_inst:
                        try:
                            nome_inst = f"logo_instituicao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            supabase.storage.from_("identidade_visual").upload(
                                path=nome_inst, file=arq_inst.getvalue(), file_options={"content-type": arq_inst.type}
                            )
                            url_pub_inst = supabase.storage.from_("identidade_visual").get_public_url(nome_inst)
                            supabase.table("configuracoes").upsert({"chave": "url_logo_instituicao", "valor": url_pub_inst}).execute()
                            st.success("✅ Logo da Instituição atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao enviar imagem: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO: DOCUMENTOS DA BIBLIOTECA
    # ---------------------------------------------------------
    elif sub == "Documentos da Biblioteca":
        st.subheader("📚 Gerenciamento de Materiais e Documentos (PDF)")
        tab_list_doc, tab_novo_doc = st.tabs(["🔍 Documentos Cadastrados", "➕ Enviar Novo Documento PDF"])
        
        with tab_list_doc:
            try:
                res_doc = supabase.table("biblioteca").select("*").order("id", desc=True).execute()
                if res_doc.data:
                    for doc in res_doc.data:
                        dt_upload_fmt = formatar_data_hora_br(doc.get('data_upload'))
                        with st.expander(f"📄 {doc['titulo']} (Enviado em {dt_upload_fmt})"):
                            st.write(f"**Descrição:** {doc.get('descricao', 'Sem descrição')}")
                            
                            col_doc1, col_doc2 = st.columns([1, 1])
                            with col_doc1:
                                st.link_button("📥 Visualizar / Baixar PDF", doc['url_publica'])
                            with col_doc2:
                                pop_del_doc = st.popover("🗑 Excluir Documento")
                                with pop_del_doc:
                                    st.warning("Deseja realmente remover este arquivo da biblioteca?")
                                    if st.button("Confirmar Exclusão", key=f"btn_del_doc_{doc['id']}"):
                                        try:
                                            supabase.storage.from_("biblioteca_documentos").remove([doc['nome_arquivo']])
                                            supabase.table("biblioteca").delete().eq("id", doc['id']).execute()
                                            st.success("Documento removido!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao excluir arquivo: {e}")
                else:
                    st.info("Nenhum documento cadastrado na biblioteca.")
            except Exception as e:
                st.error(f"Erro ao carregar documentos: {e}")

        with tab_novo_doc:
            with st.form("form_upload_pdf", clear_on_submit=True):
                titulo_doc = st.text_input("Título do Documento / Normativa*")
                desc_doc = st.text_area("Descrição Breve / Resumo*")
                arquivo_pdf = st.file_uploader("Selecione o arquivo em formato PDF*", type=["pdf"])
                
                submitted_doc = st.form_submit_button("💾 Enviar Documento para a Biblioteca")
                
                if submitted_doc:
                    if not titulo_doc or not arquivo_pdf:
                        st.warning("Por favor, informe o título e selecione um arquivo PDF.")
                    else:
                        try:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            nome_limpo_arq = f"{timestamp}_{arquivo_pdf.name.replace(' ', '_')}"
                            bytes_data = arquivo_pdf.getvalue()
                            
                            supabase.storage.from_("biblioteca_documentos").upload(
                                path=nome_limpo_arq, file=bytes_data, file_options={"content-type": "application/pdf"}
                            )
                            url_publica = supabase.storage.from_("biblioteca_documentos").get_public_url(nome_limpo_arq)
                            
                            supabase.table("biblioteca").insert({
                                "titulo": titulo_doc,
                                "descricao": desc_doc,
                                "nome_arquivo": nome_limpo_arq,
                                "url_publica": url_publica,
                                "data_upload": datetime.now().strftime("%Y-%m-%d %H:%M")
                            }).execute()
                            
                            st.success("✅ Documento PDF enviado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar arquivo: {e}")

    # ---------------------------------------------------------
    # SUB-MÓDULO: CADASTRO DO TEXTO DA TELA INICIAL
    # ---------------------------------------------------------
    elif sub == "Texto da Tela Inicial":
        st.subheader("✍️ Cadastrar / Editar Texto da Tela Inicial")
        
        texto_atual = ""
        try:
            res_txt = supabase.table("configuracoes").select("valor").eq("chave", "texto_pagina_inicial").execute()
            if res_txt.data and len(res_txt.data) > 0:
                texto_atual = res_txt.data[0]["valor"]
        except Exception as e:
            pass

        with st.form("form_texto_inicial"):
            novo_texto = st.text_area("Conteúdo da Tela Inicial (Aceita Markdown)", value=texto_atual, height=250)
            submitted_texto = st.form_submit_button("💾 Salvar Texto da Tela Inicial")
            
            if submitted_texto:
                try:
                    supabase.table("configuracoes").upsert({
                        "chave": "texto_pagina_inicial",
                        "valor": novo_texto
                    }).execute()
                    st.success("✅ Texto atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar texto: {e}")

# ---------------------------------------------------------
# PÁGINA: BIBLIOTECA
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Biblioteca":
    st.title("📚 Biblioteca de Documentos e Normativas")
    st.divider()
    
    try:
        res_bib = supabase.table("biblioteca").select("*").order("id", desc=True).execute()
        if res_bib.data:
            st.write(f"Total de documentos disponíveis: **{len(res_bib.data)}**")
            for doc in res_bib.data:
                dt_upload_fmt = formatar_data_hora_br(doc.get('data_upload'))
                with st.expander(f"📄 {doc['titulo']} (Disponibilizado em {dt_upload_fmt})"):
                    st.write(doc.get('descricao', 'Sem descrição cadastrada.'))
                    st.link_button("📥 Acessar / Baixar PDF", doc['url_publica'])
        else:
            st.info("Nenhum documento disponível no momento.")
    except Exception as e:
        st.error(f"Erro ao carregar a biblioteca: {e}")

# ---------------------------------------------------------
# DEMAIS PÁGINAS
# ---------------------------------------------------------
else:
    st.title(f"🛠️ {st.session_state.pagina_atual}")
    if st.session_state.sub_pagina_atual:
        st.subheader(f"Área: {st.session_state.sub_pagina_atual}")
    st.info("Módulo em fase de estruturação. Em breve implementaremos as funcionalidades desta área.")
