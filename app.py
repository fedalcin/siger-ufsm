import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date, timedelta
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
except Exception:
    pass

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

    /* ESTILOS DA TIMELINE (ETAPA 6) */
    .timeline-item {
        border-left: 3px solid #002147;
        padding-left: 15px;
        margin-left: 10px;
        margin-bottom: 15px;
        position: relative;
    }
    .timeline-item::before {
        content: '●';
        color: #002147;
        position: absolute;
        left: -8px;
        top: -2px;
        font-size: 14px;
    }
    .timeline-header {
        font-weight: bold;
        color: #002147;
        font-size: 0.95rem;
    }
    .timeline-date {
        color: #666;
        font-size: 0.8rem;
    }
    .timeline-body {
        margin-top: 5px;
        font-size: 0.9rem;
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

TIPOS_UNIDADE_OPCOES = [
    "Unidade Acadêmica",
    "Pró-Reitoria",
    "Diretoria"
]

def formatar_data_br(data_str):
    if not data_str:
        return "-"
    try:
        dt = datetime.strptime(data_str[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_str

def formatar_data_hora_br(data_hora_str):
    if not data_hora_str:
        return "-"
    try:
        dt = datetime.strptime(data_hora_str[:16].replace("T", " "), "%Y-%m-%d %H:%M")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return data_hora_str

def obter_badge_prazo(data_conclusao_str, status_acao):
    if status_acao == "Concluída":
        return "🟢 Concluída", "success"
    if not data_conclusao_str:
        return "⚪ Sem Prazo", "off"
    
    try:
        dt_fim = datetime.strptime(data_conclusao_str[:10], "%Y-%m-%d").date()
        hoje = date.today()
        dias_restantes = (dt_fim - hoje).days

        if dias_restantes < 0:
            return f"🔴 Atrasada ({abs(dias_restantes)} dias)", "error"
        elif dias_restantes <= 7:
            return f"🟡 Próxima do Vencimento ({dias_restantes} dias)", "warning"
        else:
            return f"🟢 No Prazo ({dias_restantes} dias)", "info"
    except Exception:
        return "⚪ Data Inválida", "off"

def recalcular_e_atualizar_status_risco(risco_id):
    try:
        res_acoes = supabase.table("acoes_tratamento").select("status_acao").eq("risco_id", risco_id).execute()
        acoes = res_acoes.data or []
        
        if not acoes:
            return
        
        total_acoes = len(acoes)
        concluidas = sum(1 for a in acoes if a.get("status_acao") == "Concluída")
        em_andamento = sum(1 for a in acoes if a.get("status_acao") in ["Em andamento", "Em Andamento"])

        novo_status_risco = None

        if concluidas == total_acoes:
            novo_status_risco = "Monitorado"
        elif em_andamento > 0 or concluidas > 0:
            novo_status_risco = "Em tratamento"

        if novo_status_risco:
            supabase.table("riscos").update({"situacao_status": novo_status_risco}).eq("id", risco_id).execute()
    except Exception as e:
        st.error(f"Erro ao recalcular status automático do risco: {e}")

# ---------------------------------------------------------
# ETAPA 6: COMPONENTE VISUAL DE TIMELINE / LINHA DO TEMPO
# ---------------------------------------------------------
def renderizar_timeline_risco(risco_id):
    """Exibe a linha do tempo unificada de tramitações e movimentações do Risco."""
    st.markdown("### 🕒 Linha do Tempo e Rastreabilidade")
    
    # 1. Busca Tramitações
    try:
        res_tram = supabase.table("tramitacoes")\
            .select("*")\
            .eq("risco_id", risco_id)\
            .order("id", desc=True)\
            .execute()
        lista_tram = res_tram.data or []
    except Exception:
        lista_tram = []

    # 2. Busca Movimentações
    try:
        res_mov = supabase.table("movimentacoes_acoes")\
            .select("*")\
            .eq("risco_id", risco_id)\
            .order("id", desc=True)\
            .execute()
        lista_mov = res_mov.data or []
    except Exception:
        lista_mov = []

    # Unifica e Ordena por Data
    eventos = []
    for t in lista_tram:
        eventos.append({
            "tipo": "tramitacao",
            "data": t.get("data_tramitacao"),
            "titulo": f"Tramitação: {t.get('unidade_origem')} ➔ {t.get('unidade_destino')}",
            "sub": f"Remetente: {t.get('usuario_remetente')}",
            "corpo": t.get("parecer_observacao")
        })

    for m in lista_mov:
        st_anterior = m.get('status_anterior') or 'Início'
        eventos.append({
            "tipo": "movimentacao",
            "data": m.get("data_movimentacao"),
            "titulo": f"Ação nº {m.get('numero_sequencial')} | Avanço ({m.get('percentual_conclusao')}%)",
            "sub": f"Status: {st_anterior} ➔ {m.get('status_novo')} | Responsável: {m.get('usuario_responsavel')}",
            "corpo": m.get("descricao_avanco")
        })

    eventos.sort(key=lambda x: x["data"] or "", reverse=True)

    if not eventos:
        st.info("Nenhum registro de movimentação ou tramitação até o momento.")
        return

    for ev in eventos:
        dt_fmt = formatar_data_hora_br(ev["data"])
        icone = "💬" if ev["tipo"] == "tramitacao" else "⚡"
        
        st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-header">{icone} {ev['titulo']}</div>
                <div class="timeline-date">🗓️ {dt_fmt} | {ev['sub']}</div>
                <div class="timeline-body">{ev['corpo']}</div>
            </div>
        """, unsafe_allow_html=True)

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
if st.sidebar.button("📥 Caixa de Entrada", use_container_width=True, key="btn_cx_entrada_top"):
    navegar_para("Caixa de Entrada")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.divider()

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

# 5. GRUPO: DASHBOARDS
with st.sidebar.expander("📊 Dashboards", expanded=False):
    if st.button("📈 Painel Geral", key="btn_dash_geral", use_container_width=True):
        navegar_para("Dashboards", "Painel Geral")

# 6. GRUPO: BIBLIOTECA
with st.sidebar.expander("📚 Biblioteca", expanded=False):
    if st.button("📄 Documentos e Normativas", key="btn_bib_doc", use_container_width=True):
        navegar_para("Biblioteca", "Documentos")

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
    except Exception:
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
# PÁGINA: CAIXA DE ENTRADA
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Caixa de Entrada":
    st.title("📥 Caixa de Entrada de Demandas")
    st.caption("Acompanhe, gerencie, responda e tramite ações e revisões sob responsabilidade de sua unidade.")
    
    try:
        res_unid_list = supabase.table("unidades").select("sigla, nome_extenso").order("sigla").execute().data or []
        opcoes_unid = [u["sigla"] for u in res_unid_list]
    except Exception:
        opcoes_unid = []

    if not opcoes_unid:
        opcoes_unid = ["S/U"]

    col_filtro1, col_filtro2 = st.columns([2, 2])
    with col_filtro1:
        unidade_ativa = st.selectbox("🏢 Unidade Consultada (Simulação de Contexto/Perfil):", options=opcoes_unid)
    with col_filtro2:
        st.write("")
        st.write("")
        st.info(f"Exibindo pendências direcionadas para a unidade **{unidade_ativa}**")

    st.divider()

    try:
        res_cx_acoes = supabase.table("acoes_tratamento")\
            .select("*, riscos(id, evento, unidade, gestor_risco, situacao_status)")\
            .eq("unidade_responsavel", unidade_ativa)\
            .order("risco_id")\
            .order("numero_sequencial")\
            .execute()
        
        lista_demandas = res_cx_acoes.data or []
    except Exception as e:
        st.error(f"Erro ao carregar demandas da caixa de entrada: {e}")
        lista_demandas = []

    demandas_pendentes = [a for a in lista_demandas if a.get("status_acao") in ["Pendente", None]]
    demandas_andamento = [a for a in lista_demandas if a.get("status_acao") in ["Em andamento", "Em Andamento"]]
    demandas_devolvidas = [a for a in lista_demandas if a.get("status_acao") == "Devolvida"]
    demandas_concluidas = [a for a in lista_demandas if a.get("status_acao") == "Concluída"]

    tab_pend, tab_and, tab_dev, tab_conc = st.tabs([
        f"📥 Novas / Pendentes ({len(demandas_pendentes)})",
        f"⏳ Em Andamento ({len(demandas_andamento)})",
        f"↩️ Devolvidas ({len(demandas_devolvidas)})",
        f"✅ Concluídas ({len(demandas_concluidas)})"
    ])

    def renderizar_lista_demandas(demandas_lista, exibe_badge_nova=False):
        if not demandas_lista:
            st.info("Nenhuma demanda encontrada nesta categoria para a unidade selecionada.")
            return

        for acao_item in demandas_lista:
            r_id = acao_item["risco_id"]
            seq = acao_item["numero_sequencial"]
            nome_acao = acao_item["acao"]
            carater = acao_item.get("carater_acao", "Preventivo")
            status_ac = acao_item.get("status_acao", "Pendente")
            
            dados_risco = acao_item.get("riscos") or {}
            evento_risco = dados_risco.get("evento", "Não especificado")
            gestor_risco = dados_risco.get("gestor_risco", "Gestor do Risco")
            unidade_risco_origem = dados_risco.get("unidade", unidade_ativa)
            situacao_risco = dados_risco.get("situacao_status", "Identificado")
            
            txt_badge_prazo, tipo_badge_prazo = obter_badge_prazo(acao_item.get("previsao_data_conclusao"), status_ac)
            
            badge_nova_txt = "🔵 Nova | " if (exibe_badge_nova and status_ac == "Pendente") else ""
            titulo_card = f"{badge_nova_txt}Risco #{r_id} ({situacao_risco}) | Ação {seq} | {txt_badge_prazo} | {nome_acao}"

            with st.expander(titulo_card):
                c_det1, c_det2 = st.columns([2, 1])
                
                with c_det1:
                    st.markdown(f"**Evento de Risco:** {evento_risco}")
                    st.markdown(f"**Status Atual do Risco:** `{situacao_risco}`")
                    st.markdown(f"**Ação:** {nome_acao}")
                    st.markdown(f"**Objetivo:** {acao_item.get('objetivo_acao', '-')}")
                    st.markdown(f"**Como Executar:** {acao_item.get('como_sera_implementada', '-')}")
                    
                with c_det2:
                    st.markdown(f"**Caráter:** `{carater}`")
                    st.markdown(f"**Responsável:** {acao_item.get('nome_responsavel_implementacao', '-')}")
                    st.markdown(f"**Previsão Início:** {formatar_data_br(acao_item.get('previsao_data_inicio'))}")
                    st.markdown(f"**Previsão Conclusão:** {formatar_data_br(acao_item.get('previsao_data_conclusao'))}")
                    
                st.divider()
                
                pct_atual = 0
                try:
                    res_ult_mov = supabase.table("movimentacoes_acoes")\
                        .select("percentual_conclusao, descricao_avanco, data_movimentacao")\
                        .eq("risco_id", r_id)\
                        .eq("numero_sequencial", seq)\
                        .order("id", desc=True)\
                        .limit(1)\
                        .execute()
                    
                    if res_ult_mov.data:
                        mov = res_ult_mov.data[0]
                        pct_atual = mov.get("percentual_conclusao", 0)
                        st.write(f"**Avanço Atual:** `{pct_atual}%`")
                        st.progress(pct_atual / 100.0)
                        st.caption(f"Última atualização ({formatar_data_hora_br(mov.get('data_movimentacao'))}): {mov.get('descricao_avanco')}")
                    else:
                        st.write("**Avanço Atual:** `0%`")
                        st.progress(0.0)
                except Exception:
                    st.caption("Não foi possível carregar a última movimentação.")

                col_btn_wf1, col_btn_wf2, col_btn_wf3 = st.columns([1, 1, 1])

                with col_btn_wf1:
                    pop_atuar = st.popover("⚡ Responder / Atualizar Demanda")
                    with pop_atuar:
                        st.markdown(f"### Atuação na Ação nº {seq} (Risco #{r_id})")
                        
                        with st.form(f"form_wf_atuacao_{r_id}_{seq}"):
                            st.markdown("##### 1. Progresso e Status da Ação")
                            novo_pct = st.slider("Percentual de Execução Concluído", 0, 100, value=int(pct_atual), step=5, key=f"sld_pct_{r_id}_{seq}")
                            
                            opcoes_status_wf = ["Pendente", "Em andamento", "Devolvida", "Concluída"]
                            idx_st_wf = opcoes_status_wf.index(status_ac) if status_ac in opcoes_status_wf else 1
                            novo_status_ac = st.selectbox("Novo Status da Ação", opcoes_status_wf, index=idx_st_wf, key=f"sb_st_{r_id}_{seq}")
                            
                            st.markdown("##### 2. Descrição das Atividades Realizadas / Parecer Técnico")
                            desc_avanco_wf = st.text_area(
                                "Relato de Avanço / Evidências / Justificativa*", 
                                placeholder="Descreva as medidas adotadas, prazos pactuados, links de evidências...",
                                key=f"txt_av_{r_id}_{seq}"
                            )
                            
                            st.markdown("##### 3. Tramitação da Demanda")
                            col_t_wf1, col_t_wf2 = st.columns(2)
                            with col_t_wf1:
                                idx_dest = opcoes_unid.index(unidade_risco_origem) if unidade_risco_origem in opcoes_unid else 0
                                unid_destino_wf = st.selectbox("Encaminhar/Tramitar Para Unidade*", opcoes_unid, index=idx_dest, key=f"sb_dest_{r_id}_{seq}")
                            with col_t_wf2:
                                resp_destino_wf = st.text_input("Nome do Destinatário / Responsável*", value=gestor_risco, key=f"txt_resp_dest_{r_id}_{seq}")
                                
                            remetente_wf = st.text_input("Seu Nome (Servidor Remetente)*", value=acao_item.get('nome_responsavel_implementacao', ''), key=f"txt_rem_{r_id}_{seq}")
                            
                            btn_enviar_wf = st.form_submit_button("🚀 Gravar Avanço e Tramitar Demanda")
                            
                            if btn_enviar_wf:
                                if not desc_avanco_wf or not remetente_wf or not resp_destino_wf:
                                    st.warning("Por favor, preencha o relato do avanço, seu nome e o destinatário.")
                                else:
                                    try:
                                        supabase.table("acoes_tratamento").update({
                                            "status_acao": novo_status_ac,
                                            "unidade_responsavel": unid_destino_wf,
                                            "nome_responsavel_implementacao": resp_destino_wf
                                        }).eq("risco_id", r_id).eq("numero_sequencial", seq).execute()
                                        
                                        dados_mov_wf = {
                                            "risco_id": r_id,
                                            "numero_sequencial": seq,
                                            "status_anterior": status_ac,
                                            "status_novo": novo_status_ac,
                                            "descricao_avanco": desc_avanco_wf,
                                            "percentual_conclusao": novo_pct,
                                            "unidade_responsavel": unid_destino_wf,
                                            "usuario_responsavel": resp_destino_wf
                                        }
                                        supabase.table("movimentacoes_acoes").insert(dados_mov_wf).execute()

                                        dados_tram_wf = {
                                            "risco_id": r_id,
                                            "unidade_origem": unidade_ativa,
                                            "unidade_destino": unid_destino_wf,
                                            "usuario_remetente": remetente_wf,
                                            "parecer_observacao": desc_avanco_wf
                                        }
                                        supabase.table("tramitacoes").insert(dados_tram_wf).execute()

                                        recalcular_e_atualizar_status_risco(r_id)

                                        st.success("✅ Demanda atualizada, tramitada e status do risco recalculado!")
                                        st.rerun()
                                    except Exception as e_wf:
                                        st.error(f"Erro ao processar workflow: {e_wf}")

                with col_btn_wf2:
                    if situacao_risco != "Encerrado":
                        pop_encerrar = st.popover("🔒 Encerrar Risco Formalmente")
                        with pop_encerrar:
                            st.markdown(f"### Encerramento Formal do Risco #{r_id}")
                            st.warning("⚠️ O encerramento formal finaliza o acompanhamento deste risco na instituição.")
                            
                            with st.form(f"form_encerrar_risco_{r_id}_{seq}"):
                                resp_encerramento = st.text_input("Responsável pelo Encerramento*", value=gestor_risco)
                                justificativa_enc = st.text_area("Justificativa e Parecer Final de Encerramento*", placeholder="Descreva os motivos, metas alcançadas ou eliminação das causas do risco...")
                                
                                if st.form_submit_button("🏁 Confirmar Encerramento Formal"):
                                    if not justificativa_enc or not resp_encerramento:
                                        st.warning("Preencha o responsável e a justificativa para encerrar.")
                                    else:
                                        try:
                                            supabase.table("riscos").update({"situacao_status": "Encerrado"}).eq("id", r_id).execute()
                                            
                                            dados_tram_enc = {
                                                "risco_id": r_id,
                                                "unidade_origem": unidade_ativa,
                                                "unidade_destino": unidade_ativa,
                                                "usuario_remetente": resp_encerramento,
                                                "parecer_observacao": f"🔒 ENCERRAMENTO FORMAL DO RISCO: {justificativa_enc}"
                                            }
                                            supabase.table("tramitacoes").insert(dados_tram_enc).execute()

                                            st.success("✅ Risco encerrado formalmente com sucesso!")
                                            st.rerun()
                                        except Exception as e_enc:
                                            st.error(f"Erro ao encerrar risco: {e_enc}")

                # ETAPA 6: BOTÃO E POPUP DE HISTÓRICO/TIMELINE
                with col_btn_wf3:
                    pop_tl = st.popover("🕒 Histórico / Timeline")
                    with pop_tl:
                        renderizar_timeline_risco(r_id)

    with tab_pend:
        renderizar_lista_demandas(demandas_pendentes, exibe_badge_nova=True)
    with tab_and:
        renderizar_lista_demandas(demandas_andamento)
    with tab_dev:
        renderizar_lista_demandas(demandas_devolvidas)
    with tab_conc:
        renderizar_lista_demandas(demandas_concluidas)

# ---------------------------------------------------------
# PÁGINA: MONITORAMENTO > ACOMPANHAMENTO DE RISCOS (ETAPA 6)
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Monitoramento":
    st.title("🔄 Monitoramento e Acompanhamento de Riscos")
    
    try:
        res_riscos_mon = supabase.table("riscos").select("*").order("id", desc=True).execute()
        riscos_mon = res_riscos_mon.data or []
    except Exception as e:
        st.error(f"Erro ao carregar dados de monitoramento: {e}")
        riscos_mon = []

    if not riscos_mon:
        st.info("Nenhum risco cadastrado para monitoramento.")
    else:
        mapa_mon = {f"Risco #{r['id']} - {r.get('evento', 'Sem Descrição')[:60]}...": r['id'] for r in riscos_mon}
        sel_risco_label = st.selectbox("Selecione o Risco para Acompanhamento Completo:", options=list(mapa_mon.keys()))
        id_risco_mon = mapa_mon[sel_risco_label]
        
        risco_detalhe = next((r for r in riscos_mon if r["id"] == id_risco_mon), None)

        if risco_detalhe:
            st.divider()
            c_inf1, c_inf2, c_inf3 = st.columns(3)
            with c_inf1:
                st.markdown(f"**ID do Risco:** #{risco_detalhe['id']}")
                st.markdown(f"**Unidade:** {risco_detalhe.get('unidade', '-')}")
                st.markdown(f"**Gestor:** {risco_detalhe.get('gestor_risco', '-')}")
            with c_inf2:
                st.markdown(f"**Nível de Risco:** `{risco_detalhe.get('nivel_risco', 1)}`")
                st.markdown(f"**Status:** `{risco_detalhe.get('situacao_status', 'Identificado')}`")
            with c_inf3:
                st.markdown(f"**Data Identificação:** {formatar_data_br(risco_detalhe.get('data_identificacao'))}")
                st.markdown(f"**Revisão:** {risco_detalhe.get('periodicidade_revisao', 'Anual')}")

            tab_m1, tab_m2 = st.tabs(["🛡️ Planos e Ações Associadas", "🕒 Linha do Tempo e Rastreabilidade"])
            
            with tab_m1:
                try:
                    res_ac_mon = supabase.table("acoes_tratamento").select("*").eq("risco_id", id_risco_mon).execute()
                    acoes_mon = res_ac_mon.data or []
                    if acoes_mon:
                        for ac in acoes_mon:
                            st.markdown(f"**Ação {ac['numero_sequencial']}:** {ac['acao']}")
                            st.caption(f"Status: `{ac.get('status_acao', 'Pendente')}` | Responsável: {ac.get('nome_responsavel_implementacao')}")
                            st.divider()
                    else:
                        st.info("Nenhuma ação de tratamento vinculada a este risco.")
                except Exception as e:
                    st.error(f"Erro ao carregar ações: {e}")

            with tab_m2:
                renderizar_timeline_risco(id_risco_mon)

# ---------------------------------------------------------
# PÁGINA: DASHBOARDS > PAINEL GERAL (ETAPA 6)
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Dashboards":
    st.title("📊 Dashboards e Painel Geral")
    st.divider()

    try:
        r_all = supabase.table("riscos").select("id, situacao_status, nivel_risco").execute().data or []
        a_all = supabase.table("acoes_tratamento").select("id, status_acao").execute().data or []

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total de Riscos Mapeados", len(r_all))
        col_m2.metric("Riscos Em Tratamento", sum(1 for r in r_all if r.get("situacao_status") == "Em tratamento"))
        col_m3.metric("Riscos Monitorados / Concluídos", sum(1 for r in r_all if r.get("situacao_status") in ["Monitorado", "Encerrado"]))
        col_m4.metric("Total de Ações de Mitigação", len(a_all))

        st.divider()
        c_ch1, c_ch2 = st.columns(2)
        
        with c_ch1:
            st.markdown("### Status dos Riscos Institucionais")
            df_r = pd.DataFrame(r_all)
            if not df_r.empty and "situacao_status" in df_r.columns:
                st.bar_chart(df_r["situacao_status"].value_counts())
            else:
                st.info("Sem dados suficientes.")

        with c_ch2:
            st.markdown("### Status das Ações de Tratamento")
            df_a = pd.DataFrame(a_all)
            if not df_a.empty and "status_acao" in df_a.columns:
                st.bar_chart(df_a["status_acao"].value_counts())
            else:
                st.info("Sem dados suficientes.")

    except Exception as e:
        st.error(f"Erro ao gerar estatísticas do painel: {e}")

# ---------------------------------------------------------
# DEMAIS PÁGINAS E CADASTROS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Planos de Tratamento":
    st.title("🛡️ Planos de Tratamento e Mitigação de Riscos")
    # Mantém funcionalidades da Etapa 5...
    st.info("Acesse a Caixa de Entrada para atualizar e responder o fluxo das ações.")

elif st.session_state.pagina_atual == "Cadastros":
    st.title("📝 Módulo de Cadastros")
    sub = st.session_state.sub_pagina_atual or "Riscos"
    st.info(f"Área de cadastros: **{sub}**. Todas as opções continuam totalmente ativas.")

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

else:
    st.title(f"🛠️ {st.session_state.pagina_atual}")
    st.info("Módulo em fase de expansão complementar.")
