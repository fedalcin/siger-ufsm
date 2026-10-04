import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
import os
import bcrypt

# ---------------------------------------------------------
# IMPORTAÇÃO DO MÓDULO DE CÁLCULOS SIGER
# ---------------------------------------------------------

try:
    from calculos_siger import (
        IET_METRICAS,
        calcular_icp,
        calcular_iet,
        calcular_itr,
        carregar_dados_siger,
        classificar_iar,
        obter_cor_indicador,
    )
except Exception as e:
    st.error(f"Erro ao importar calculos_siger.py: {e}")

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
    favicon_app = "🛡"

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

    /* ESTILOS DA TIMELINE */
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

# ---------------------------------------------------------
# CONSTANTES E REGRAS DE CÁLCULO DA ETAPA 2 (MATRIZ DE RISCO)
# ---------------------------------------------------------
LABELS_PROBABILIDADE = {
    1: "1 - Raro",
    2: "2 - Pouco Provável",
    3: "3 - Provável",
    4: "4 - Muito Provável",
    5: "5 - Quase Certo"
}

LABELS_IMPACTO = {
    1: "1 - Insignificante",
    2: "2 - Pequeno",
    3: "3 - Moderado",
    4: "4 - Grande",
    5: "5 - Catastrófico"
}

def calcular_nivel_e_classificacao(probabilidade: int, impacto: int):
    """
    Calcula o Nível de Risco (Probabilidade x Impacto) e define a Classificação Térmica
    Regras da Etapa 2:
      - 1 a 5: Baixo (Verde)
      - 6 a 12: Médio (Amarelo)
      - 15 a 25: Crítico (Vermelho)
    """
    nivel = probabilidade * impacto
    if nivel >= 15:
        classificacao = "Crítico"
        badge = f"🔴 {nivel} ({classificacao})"
        cor_hex = "#ff4b4b"
    elif nivel >= 6:
        classificacao = "Médio"
        badge = f"🟡 {nivel} ({classificacao})"
        cor_hex = "#ffa800"
    else:
        classificacao = "Baixo"
        badge = f"🟢 {nivel} ({classificacao})"
        cor_hex = "#00c853"
        
    return nivel, classificacao, badge, cor_hex

# ---------------------------------------------------------
# AUTENTICAÇÃO E SESSÃO DO USUÁRIO
# ---------------------------------------------------------
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

def verificar_senha(senha_fornecida, senha_hash):
    try:
        return bcrypt.checkpw(senha_fornecida.encode('utf-8'), senha_hash.encode('utf-8'))
    except Exception:
        return False

def gerar_hash_senha(senha):
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def realizar_login(email, senha):
    try:
        res = supabase.table("usuarios")\
            .select("*, perfis(nome)")\
            .eq("email", email.strip().lower())\
            .eq("ativo", True)\
            .execute()
        
        if res.data and len(res.data) > 0:
            usr = res.data[0]
            hash_bd = usr.get("senha_hash")
            if verificar_senha(senha, hash_bd):
                st.session_state.usuario_logado = {
                    "id": usr["id"],
                    "nome": usr["nome"],
                    "email": usr["email"],
                    "unidade": usr.get("unidade_sigla"),
                    "perfil": usr.get("perfis", {}).get("nome", "Leitor") if usr.get("perfis") else "Leitor"
                }
                return True, "Login realizado com sucesso!"
            else:
                return False, "Senha incorreta."
        return False, "Usuário não encontrado ou inativo."
    except Exception as e:
        return False, f"Erro na conexão de autenticação: {e}"

def tela_login():
    col_c1, col_c2, col_c3 = st.columns([1, 1.2, 1])
    with col_c2:
        st.write("")
        st.write("")
        if url_logo_siger:
            st.image(url_logo_siger, use_container_width=True)
        else:
            st.title("🛡️ SIGER")
        
        st.subheader("Acesso ao Sistema")
        
        with st.form("form_login"):
            email_input = st.text_input("E-mail institucional", placeholder="usuario@instituicao.edu.br")
            senha_input = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("🔑 Entrar no Sistema", use_container_width=True)
            
            if btn_entrar:
                if not email_input or not senha_input:
                    st.warning("Preencha todos os campos para continuar.")
                else:
                    sucesso, msg = realizar_login(email_input, senha_input)
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# Bloqueia aplicação caso não esteja autenticado
if not st.session_state.usuario_logado:
    tela_login()
    st.stop()

# ---------------------------------------------------------
# HELPER DE PERMISSÕES (RBAC)
# ---------------------------------------------------------
usr_atual = st.session_state.usuario_logado
perfil_usr = usr_atual["perfil"]
is_admin = perfil_usr == "Admin"
is_gestor = perfil_usr in ["Admin", "Gestor"]

# ---------------------------------------------------------
# FUNÇÕES AUXILIARES DE FORMATAÇÃO E REGRAS
# ---------------------------------------------------------
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
# COMPONENTE VISUAL DE TIMELINE / LINHA DO TEMPO
# ---------------------------------------------------------
def renderizar_timeline_risco(risco_id):
    st.markdown("### 🕒 Linha do Tempo e Rastreabilidade")
    
    try:
        res_tram = supabase.table("tramitacoes")\
            .select("*")\
            .eq("risco_id", risco_id)\
            .order("id", desc=True)\
            .execute()
        lista_tram = res_tram.data or []
    except Exception:
        lista_tram = []

    try:
        res_mov = supabase.table("movimentacoes_acoes")\
            .select("*")\
            .eq("risco_id", risco_id)\
            .order("id", desc=True)\
            .execute()
        lista_mov = res_mov.data or []
    except Exception:
        lista_mov = []

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
# BARRA LATERAL (USER INFO & MENU EXPANSÍVEL)
# ---------------------------------------------------------
if url_logo_siger:
    st.sidebar.image(url_logo_siger, use_container_width=True)
elif os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.title("SIGER")
    st.sidebar.markdown("**Sistema de Gestão de Riscos**")

st.sidebar.divider()

# Informações do Usuário Logado
st.sidebar.markdown(f"👤 **{usr_atual['nome']}**")
st.sidebar.caption(f"Perfil: `{perfil_usr}` | Unidade: `{usr_atual['unidade'] or 'Todas'}`")
if st.sidebar.button("🚪 Sair / Logout", use_container_width=True, key="btn_logout_top"):
    st.session_state.usuario_logado = None
    st.rerun()

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

# 1. GRUPO: ADMINISTRAÇÃO (Visível apenas para Admin)
if is_admin:
    with st.sidebar.expander("⚙ Administração", expanded=False):
        if st.button("👥 Usuários e Permissões", key="btn_adm_usr", use_container_width=True):
            navegar_para("Administração do Sistema", "Usuários")
        if st.button("🔧 Configurações Gerais", key="btn_adm_cfg", use_container_width=True):
            navegar_para("Administração do Sistema", "Configurações")

# 2. GRUPO: CADASTROS
with st.sidebar.expander("📝 Cadastros", expanded=False):
    if is_admin:
        if st.button("🏢 Unidades", key="btn_cad_unid", use_container_width=True):
            navegar_para("Cadastros", "Unidades")
        if st.button("🎯 Objetivos Estratégicos", key="btn_cad_oe", use_container_width=True):
            navegar_para("Cadastros", "Objetivos Estratégicos")
        if st.button("🏷️ Categorias de Risco", key="btn_cad_cat", use_container_width=True):
            navegar_para("Cadastros", "Categorias de Risco")
        if st.button("🖼️ Identidade Visual", key="btn_cad_id_vis", use_container_width=True):
            navegar_para("Cadastros", "Identidade Visual")
        if st.button("📚 Documentos da Biblioteca", key="btn_cad_doc_bib", use_container_width=True):
            navegar_para("Cadastros", "Documentos da Biblioteca")
        if st.button("✍ Texto da Tela Inicial", key="btn_cad_txt", use_container_width=True):
            navegar_para("Cadastros", "Texto da Tela Inicial")
            
    if is_gestor:
        if st.button("📋 Riscos", key="btn_cad_risco", use_container_width=True):
            navegar_para("Cadastros", "Riscos")

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
# PÁGINA: ADMINISTRAÇÃO DO SISTEMA (USUÁRIOS E CONFIGURAÇÕES)
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Administração do Sistema" and is_admin:
    sub = st.session_state.sub_pagina_atual or "Usuários"
    
    if sub == "Usuários":
        st.title("👥 Gestão de Usuários e Permissões")
        
        tab_users_list, tab_user_new = st.tabs(["🔍 Usuários Cadastrados", "➕ Cadastrar Novo Usuário"])
        
        with tab_users_list:
            try:
                res_u = supabase.table("vw_usuarios_detalhados").select("*").order("nome").execute()
                lista_u = res_u.data or []
                
                if lista_u:
                    st.write(f"Total de usuários cadastrados: **{len(lista_u)}**")
                    for u_item in lista_u:
                        st_ativo = "🟢 Ativo" if u_item.get("ativo") else "🔴 Inativo"
                        with st.expander(f"👤 {u_item['nome']} ({u_item['email']}) - Perfil: {u_item.get('perfil_nome')} | {st_ativo}"):
                            st.write(f"**Unidade:** {u_item.get('unidade_sigla') or 'Todas'}")
                            st.write(f"**Data de Criação:** {formatar_data_hora_br(u_item.get('criado_em'))}")
                            
                            pop_edit_u = st.popover("✏️ Editar Usuário")
                            with pop_edit_u:
                                with st.form(f"form_edit_user_{u_item['id']}"):
                                    e_nome = st.text_input("Nome", value=u_item["nome"])
                                    e_ativo = st.checkbox("Ativo", value=u_item.get("ativo", True))
                                    
                                    # Perfis
                                    res_p = supabase.table("perfis").select("*").execute().data or []
                                    mapa_perfis = {p["nome"]: p["id"] for p in res_p}
                                    idx_p = list(mapa_perfis.keys()).index(u_item.get("perfil_nome")) if u_item.get("perfil_nome") in mapa_perfis else 0
                                    e_perfil = st.selectbox("Perfil de Acesso", list(mapa_perfis.keys()), index=idx_p)
                                    
                                    # Unidades
                                    res_un = supabase.table("unidades").select("sigla").execute().data or []
                                    opts_un = ["Nenhuma / Todas"] + [un["sigla"] for un in res_un]
                                    idx_u_sig = opts_un.index(u_item.get("unidade_sigla")) if u_item.get("unidade_sigla") in opts_un else 0
                                    e_unid = st.selectbox("Unidade Responsável", opts_un, index=idx_u_sig)
                                    
                                    nueva_pass = st.text_input("Nova Senha (deixe em branco se não desejar alterar)", type="password")
                                    
                                    if st.form_submit_button("💾 Salvar"):
                                        dados_upd = {
                                            "nome": e_nome,
                                            "ativo": e_ativo,
                                            "perfil_id": mapa_perfis[e_perfil],
                                            "unidade_sigla": None if e_unid == "Nenhuma / Todas" else e_unid
                                        }
                                        if nueva_pass.strip():
                                            dados_upd["senha_hash"] = gerar_hash_senha(nueva_pass.strip())
                                            
                                        supabase.table("usuarios").update(dados_upd).eq("id", u_item["id"]).execute()
                                        st.success("Usuário atualizado com sucesso!")
                                        st.rerun()
                else:
                    st.info("Nenhum usuário cadastrado.")
            except Exception as e:
                st.error(f"Erro ao carregar usuários: {e}")
                
        with tab_user_new:
            with st.form("form_novo_usuario", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    new_nome = st.text_input("Nome Completo*")
                    new_email = st.text_input("E-mail Institucional*")
                    new_senha = st.text_input("Senha Inicial*", type="password")
                with col_u2:
                    res_p = supabase.table("perfis").select("*").execute().data or []
                    mapa_perfis = {p["nome"]: p["id"] for p in res_p}
                    new_perfil = st.selectbox("Perfil de Acesso*", list(mapa_perfis.keys()))
                    
                    res_un = supabase.table("unidades").select("sigla").execute().data or []
                    opts_un = ["Nenhuma / Todas"] + [un["sigla"] for un in res_un]
                    new_unid = st.selectbox("Unidade Responsável", opts_un)
                    
                if st.form_submit_button("💾 Cadastrar Usuário"):
                    if not new_nome or not new_email or not new_senha:
                        st.warning("Preencha todos os campos obrigatórios.")
                    else:
                        try:
                            hash_pw = gerar_hash_senha(new_senha)
                            supabase.table("usuarios").insert({
                                "nome": new_nome,
                                "email": new_email.strip().lower(),
                                "senha_hash": hash_pw,
                                "perfil_id": mapa_perfis[new_perfil],
                                "unidade_sigla": None if new_unid == "Nenhuma / Todas" else new_unid,
                                "ativo": True
                            }).execute()
                            st.success("✅ Usuário criado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar usuário: {e}")

# ---------------------------------------------------------
# PÁGINA: CAIXA DE ENTRADA
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Caixa de Entrada":
    st.title("📥 Caixa de Entrada de Demandas")
    st.caption("Acompanhe, gerencie, responda e tramite ações sob responsabilidade de sua unidade.")
    
    try:
        res_unid_list = supabase.table("unidades").select("sigla, nome_extenso").order("sigla").execute().data or []
        opcoes_unid = [u["sigla"] for u in res_unid_list]
    except Exception:
        opcoes_unid = []

    if not opcoes_unid:
        opcoes_unid = ["S/U"]

    # Se usuário for restrito à sua unidade, seleciona ela por padrão
    unidade_usuario = usr_atual.get("unidade")
    idx_unid_def = opcoes_unid.index(unidade_usuario) if unidade_usuario in opcoes_unid else 0

    col_filtro1, col_filtro2 = st.columns([2, 2])
    with col_filtro1:
        if is_admin or not unidade_usuario:
            unidade_ativa = st.selectbox("🏢 Unidade Consultada:", options=opcoes_unid, index=idx_unid_def)
        else:
            unidade_ativa = unidade_usuario
            st.selectbox("🏢 Unidade Consultada:", options=[unidade_usuario], disabled=True)
            
    with col_filtro2:
        st.write("")
        st.write("")
        st.info(f"Exibindo pendências para **{unidade_ativa}**")

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
            st.info("Nenhuma demanda encontrada nesta categoria.")
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
                    if is_gestor:
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
                                    placeholder="Descreva as medidas adotadas, prazos pactuados...",
                                    key=f"txt_av_{r_id}_{seq}"
                                )
                                
                                st.markdown("##### 3. Tramitação da Demanda")
                                col_t_wf1, col_t_wf2 = st.columns(2)
                                with col_t_wf1:
                                    idx_dest = opcoes_unid.index(unidade_risco_origem) if unidade_risco_origem in opcoes_unid else 0
                                    unid_destino_wf = st.selectbox("Encaminhar/Tramitar Para Unidade*", opcoes_unid, index=idx_dest, key=f"sb_dest_{r_id}_{seq}")
                                with col_t_wf2:
                                    resp_destino_wf = st.text_input("Nome do Destinatário / Responsável*", value=gestor_risco, key=f"txt_resp_dest_{r_id}_{seq}")
                                    
                                remetente_wf = st.text_input("Seu Nome (Servidor Remetente)*", value=usr_atual["nome"], key=f"txt_rem_{r_id}_{seq}")
                                
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
                    if situacao_risco != "Encerrado" and is_gestor:
                        pop_encerrar = st.popover("🔒 Encerrar Risco Formalmente")
                        with pop_encerrar:
                            st.markdown(f"### Encerramento Formal do Risco #{r_id}")
                            st.warning("⚠️ O encerramento formal finaliza o acompanhamento deste risco.")
                            
                            with st.form(f"form_encerrar_risco_{r_id}_{seq}"):
                                resp_encerramento = st.text_input("Responsável pelo Encerramento*", value=usr_atual["nome"], key=f"txt_resp_enc_{r_id}_{seq}")
                                justificativa_enc = st.text_area("Justificativa e Parecer Final*", placeholder="Descreva os motivos...", key=f"txt_just_enc_{r_id}_{seq}")
                                
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

                with col_btn_wf3:
                    pop_hist = st.popover("🕒 Linha do Tempo")
                    with pop_hist:
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
# PÁGINA: PLANOS DE TRATAMENTO / AÇÕES DE MITIGAÇÃO
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Planos de Tratamento":
    st.title("🛡 Planos de Tratamento e Mitigação de Riscos")
    
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
                    
                    dt_inicio_fmt = formatar_data_br(acao_item.get('previsao_data_inicio'))
                    dt_conclusao_fmt = formatar_data_br(acao_item.get('previsao_data_conclusao'))
                    
                    with st.expander(f"{badge_carater} Risco #{r_id} | Ação {seq}: {nome_acao}"):
                        st.markdown(f"**Risco:** {evento_txt}")
                        st.markdown(f"**Caráter da Ação:** {carater}")
                        st.markdown(f"**Status da Ação:** `{acao_item.get('status_acao', 'Pendente')}`")
                        st.markdown(f"**Objetivo da Ação:** {acao_item['objetivo_acao']}")
                        st.markdown(f"**Unidade Responsável:** {acao_item['unidade_responsavel']}")
                        st.markdown(f"**Responsável pela Implementação:** {acao_item['nome_responsavel_implementacao']}")
                        st.markdown(f"**Como será Implementada:** {acao_item['como_sera_implementada']}")
                        st.markdown(f"**Período de Execução:** {dt_inicio_fmt} até {dt_conclusao_fmt}")
                        
                        if is_gestor:
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
                                            recalcular_e_atualizar_status_risco(r_id)
                                            st.success("Ação removida e status do risco atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao excluir ação: {e}")
            else:
                st.info("Nenhuma ação de tratamento/mitigação cadastrada até o momento.")
        except Exception as e:
            st.error(f"Erro ao carregar ações de tratamento: {e}")
            
    with tab_nova_acao:
        if not is_gestor:
            st.warning("Seu perfil de usuário possui acesso apenas de leitura.")
        else:
            try:
                res_riscos_db = supabase.table("riscos").select("id, evento, unidade").order("id").execute().data or []
                res_unid_db = supabase.table("unidades").select("sigla, nome_extenso").order("sigla").execute().data or []
            except Exception:
                res_riscos_db, res_unid_db = [], []
                
            if not res_riscos_db:
                st.warning("⚠️ É necessário ter pelo menos um Risco cadastrado no sistema para criar um Plano de Tratamento.")
            else:
                mapa_riscos = {f"Risco #{r['id']} - {r['evento'] if r['evento'] else 'Sem Risco'}" : (r['id'], r['unidade']) for r in res_riscos_db}
                
                opcoes_unid_siglas = [u['sigla'] for u in res_unid_db] if res_unid_db else ["S/U"]

                risco_selecionado_label = st.selectbox("Selecione o Risco Mapeado*", options=list(mapa_riscos.keys()))
                id_risco_sel, unidade_origem_risco = mapa_riscos[risco_selecionado_label]
                
                try:
                    res_seq = supabase.table("acoes_tratamento").select("numero_sequencial").eq("risco_id", id_risco_sel).order("numero_sequencial", desc=True).limit(1).execute()
                    prox_seq = (res_seq.data[0]["numero_sequencial"] + 1) if res_seq.data else 1
                except Exception:
                    prox_seq = 1
                    
                st.info(f"📌 Esta será a **Ação nº {prox_seq}** associada ao **Risco #{id_risco_sel}**.")

                with st.form("form_cadastrar_acao_tratamento", clear_on_submit=True):
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        acao_input = st.text_input("Ação de Mitigação*", placeholder="Ex: Implantar rotina diária de backup automatizado")
                        carater_sel = st.selectbox("Caráter da Ação*", options=["Preventivo", "Corretivo", "Compensatório"])
                        unidade_resp_sel = st.selectbox("Unidade Responsável pela Ação*", options=opcoes_unid_siglas)
                    with col_a2:
                        nome_resp_input = st.text_input("Nome do Responsável pela Implementação*", value=usr_atual["nome"])
                        dt_inicio = st.date_input("Previsão da Data do Início*", datetime.now(), format="DD/MM/YYYY")
                        dt_conclusao = st.date_input("Previsão da Data da Conclusão*", datetime.now(), format="DD/MM/YYYY")

                    objetivo_input = st.text_area("Objetivo da Ação*", placeholder="O que se pretende alcançar com esta ação?")
                    como_input = st.text_area("Como será Implementada a Ação*", placeholder="Descreva o passo a passo...")

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
                                "previsao_data_conclusao": dt_conclusao.strftime("%Y-%m-%d"),
                                "status_acao": "Pendente"
                            }
                            try:
                                supabase.table("acoes_tratamento").insert(dados_nova_acao).execute()
                                
                                dados_mov_inicial = {
                                    "risco_id": id_risco_sel,
                                    "numero_sequencial": prox_seq,
                                    "status_anterior": None,
                                    "status_novo": "Pendente",
                                    "descricao_avanco": "Ação cadastrada e aguardando início de implementação.",
                                    "percentual_conclusao": 0,
                                    "unidade_responsavel": unidade_resp_sel,
                                    "usuario_responsavel": nome_resp_input
                                }
                                supabase.table("movimentacoes_acoes").insert(dados_mov_inicial).execute()

                                dados_tramitacao_acao = {
                                    "risco_id": id_risco_sel,
                                    "unidade_origem": unidade_origem_risco or unidade_resp_sel,
                                    "unidade_destino": unidade_resp_sel,
                                    "usuario_remetente": usr_atual["nome"],
                                    "parecer_observacao": f"Ação nº {prox_seq} registrada e atribuída a {nome_resp_input}."
                                }
                                supabase.table("tramitacoes").insert(dados_tramitacao_acao).execute()

                                supabase.table("riscos").update({"situacao_status": "Em tratamento"}).eq("id", id_risco_sel).execute()

                                st.success(f"✅ Ação nº {prox_seq} cadastrada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar ação no banco de dados: {e}")

# ---------------------------------------------------------
# PÁGINA: CADASTROS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Cadastros":
    st.title("📝 Módulo de Cadastros")
    sub = st.session_state.sub_pagina_atual or "Riscos"
    
    if sub == "Unidades" and is_admin:
        st.subheader("🏢 Cadastramento de Unidades / Setores Institucionais")
        tab_list_unid, tab_novo_unid = st.tabs(["🔍 Unidades Cadastradas", "➕ Nova Unidade"])
        
        with tab_list_unid:
            try:
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
                                            res_riscos = supabase.table("riscos").select("id").eq("unidade", sigla_item).execute()
                                            if res_riscos.data and len(res_riscos.data) > 0:
                                                st.error(f"❌ Impossível excluir '{sigla_item}'. Existem {len(res_riscos.data)} risco(s) vinculados.")
                                            else:
                                                supabase.table("unidades").delete().eq("sigla", sigla_item).execute()
                                                st.toast(f"Unidade '{sigla_item}' excluída!", icon="🗑")
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
                
                submitted_unid = st.form_submit_button("💾 Salvar Unidade")
                
                if submitted_unid:
                    if not sigla or not nome_extenso:
                        st.warning("Por favor, preencha a Sigla e o Nome por Extenso.")
                    else:
                        try:
                            supabase.table("unidades").insert({
                                "sigla": sigla,
                                "nome_extenso": nome_extenso,
                                "tipo_unidade": tipo_unidade_sel
                            }).execute()
                            st.toast(f"✅ Unidade '{sigla}' registrada!", icon="🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar unidade: {e}")

    elif sub == "Riscos" and is_gestor:
        st.subheader("📋 Gestão e Cadastro de Riscos Institucionais")
        tab1, tab2 = st.tabs(["🔍 Riscos Cadastrados", "➕ Novo Risco"])
        
        with tab1:
            try:
                resposta = supabase.table("riscos").select("*").order("id", desc=True).execute()
                dados = resposta.data
                
                if dados:
                    st.write(f"Total de riscos registrados: **{len(dados)}**")
                    
                    for r_item in dados:
                        p_val = r_item.get('probabilidade', 1)
                        i_val = r_item.get('impacto', 1)
                        _, _, badge_risco, _ = calcular_nivel_e_classificacao(p_val, i_val)
                        
                        dt_ident_fmt = formatar_data_br(r_item.get('data_identificacao'))
                        st_risco = r_item.get('situacao_status', 'Identificado')
                        
                        with st.expander(f"🛡️ Risco #{r_item['id']} ({st_risco}) | {r_item['unidade']} | {badge_risco}"):
                            st.markdown(f"**Risco:** {r_item.get('evento', '')}")
                            st.markdown(f"**Causa:** {r_item.get('causa', '')} | **Consequência:** {r_item.get('consequencia', '')}")
                            st.markdown(f"**Probabilidade:** {LABELS_PROBABILIDADE.get(p_val, p_val)} | **Impacto:** {LABELS_IMPACTO.get(i_val, i_val)}")
                            st.markdown(f"**Gestor:** {r_item.get('gestor_risco', '')} | **Situação Atual:** `{st_risco}`")
                            st.markdown(f"**Data de Identificação:** {dt_ident_fmt}")
                            
                            col_r_edit, col_r_del, col_r_enc = st.columns([1, 1, 1])
                            
                            with col_r_edit:
                                pop_edit_r = st.popover("✏️ Editar Risco")
                                with pop_edit_r:
                                    with st.form(f"form_edit_risco_{r_item['id']}"):
                                        e_evento = st.text_area("Risco", value=r_item.get('evento', ''))
                                        e_causa = st.text_area("Causa", value=r_item.get('causa', ''))
                                        e_cons = st.text_area("Consequência", value=r_item.get('consequencia', ''))
                                        
                                        st.markdown("---")
                                        st.markdown("##### 🧮 Reavaliação do Risco (Etapa 2)")
                                        e_prob = st.slider(
                                            "Probabilidade", 
                                            1, 5, 
                                            value=p_val, 
                                            format="%d",
                                            help="1: Raro | 2: Pouco Provável | 3: Provável | 4: Muito Provável | 5: Quase Certo"
                                        )
                                        st.caption(f"Probabilidade Selecionada: **{LABELS_PROBABILIDADE[e_prob]}**")

                                        e_imp = st.slider(
                                            "Impacto", 
                                            1, 5, 
                                            value=i_val, 
                                            format="%d",
                                            help="1: Insignificante | 2: Pequeno | 3: Moderado | 4: Grande | 5: Catastrófico"
                                        )
                                        st.caption(f"Impacto Selecionado: **{LABELS_IMPACTO[e_imp]}**")

                                        e_nv_calc, e_class_calc, e_badge_calc, _ = calcular_nivel_e_classificacao(e_prob, e_imp)
                                        st.info(f"Nível Recalculado: **{e_badge_calc}**")
                                        st.markdown("---")

                                        e_resp = st.text_input("Gestor do Risco", value=r_item.get('gestor_risco', ''))
                                        
                                        options_status = ['Identificado', 'Em análise', 'Em tratamento', 'Monitorado', 'Encerrado', 'Cancelado']
                                        curr_status = r_item.get('situacao_status', 'Identificado')
                                        idx_st = options_status.index(curr_status) if curr_status in options_status else 0
                                        e_sit = st.selectbox("Situação", options_status, index=idx_st)
                                        
                                        if st.form_submit_button("💾 Salvar Alterações"):
                                            supabase.table("riscos").update({
                                                "evento": e_evento,
                                                "causa": e_causa,
                                                "consequencia": e_cons,
                                                "probabilidade": e_prob,
                                                "impacto": e_imp,
                                                "nivel_risco": e_nv_calc,
                                                "gestor_risco": e_resp,
                                                "situacao_status": e_sit
                                            }).eq("id", r_item['id']).execute()
                                            
                                            st.success("Risco e Matriz atualizados com sucesso!")
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

                            with col_r_enc:
                                if st_risco != "Encerrado":
                                    pop_enc_cad = st.popover("🔒 Encerrar Formalmente")
                                    with pop_enc_cad:
                                        with st.form(f"form_encerrar_cad_r_{r_item['id']}"):
                                            resp_enc_cad = st.text_input("Gestor/Responsável*", value=usr_atual["nome"])
                                            justificativa_enc_cad = st.text_area("Justificativa*", placeholder="Informe o parecer...")
                                            
                                            if st.form_submit_button("🏁 Confirmar Encerramento"):
                                                if not justificativa_enc_cad or not resp_enc_cad:
                                                    st.warning("Preencha todos os campos obrigatórios.")
                                                else:
                                                    try:
                                                        supabase.table("riscos").update({"situacao_status": "Encerrado"}).eq("id", r_item['id']).execute()
                                                        
                                                        dados_tram_enc = {
                                                            "risco_id": r_item['id'],
                                                            "unidade_origem": r_item.get('unidade', 'S/U'),
                                                            "unidade_destino": r_item.get('unidade', 'S/U'),
                                                            "usuario_remetente": resp_enc_cad,
                                                            "parecer_observacao": f"🔒 ENCERRAMENTO FORMAL DO RISCO: {justificativa_enc_cad}"
                                                        }
                                                        supabase.table("tramitacoes").insert(dados_tram_enc).execute()

                                                        st.success("✅ Risco encerrado formalmente!")
                                                        st.rerun()
                                                    except Exception as e_enc:
                                                        st.error(f"Erro ao encerrar risco: {e_enc}")
                else:
                    st.info("Nenhum risco cadastrado até o momento.")
            except Exception as e:
                st.error(f"Erro ao carregar dados do banco: {e}")
                
        with tab2:
            try:
                res_unidades = supabase.table("unidades").select("sigla, nome_extenso").order("sigla").execute().data or []
                res_oe = supabase.table("objetivos_estrategicos").select("codigo, descricao").order("codigo").execute().data or []
                res_cat = supabase.table("categorias_riscos").select("id, tipo, sub_tipo").order("tipo").execute().data or []
            except Exception:
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

                st.markdown("##### 2. Identificação do Risco")
                evento_input = st.text_area("Risco*", placeholder="Descreva o evento de risco")
                
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    causa_input = st.text_area("Causa(s)*", placeholder="Quais fatores geram este risco?")
                with col_i2:
                    consequencia_input = st.text_area("Consequência(s)*", placeholder="Quais os impactos institucionais?")

                st.markdown("##### 3. Avaliação Qualitativa e Matriz de Riscos (Regras Etapa 2)")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    prob_val = st.slider("Probabilidade (P)*", 1, 5, 3)
                    st.caption(f"Nível Selecionado: **{LABELS_PROBABILIDADE[prob_val]}**")
                with col_a2:
                    imp_val = st.slider("Impacto (I)*", 1, 5, 3)
                    st.caption(f"Nível Selecionado: **{LABELS_IMPACTO[imp_val]}**")

                nivel_calc, class_calc, badge_calc, _ = calcular_nivel_e_classificacao(prob_val, imp_val)
                
                st.markdown(f"""
                > **Cálculo Automático (Etapa 2):**
                > - **Fórmula:** $Nível = Probabilidade (P) \\times Impacto (I)$
                > - **Resultado do Nível:** **{nivel_calc}**
                > - **Classificação Térmica:** **{badge_calc}**
                """)

                st.markdown("##### 4. Governança e Prazos")
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    resp_input = st.text_input("Gestor do Risco*", value=usr_atual["nome"])
                with col_g2:
                    dt_identificacao = st.date_input("Data de Identificação*", datetime.now(), format="DD/MM/YYYY")
                with col_g3:
                    periodicidade_sel = st.selectbox("Periodicidade de Revisão", ["Mensal", "Trimestral", "Semestral", "Anual"])

                submitted_risco = st.form_submit_button("💾 Salvar Risco Mapeado")
                
                if submitted_risco:
                    if not evento_input or not resp_input:
                        st.warning("Preencha todos os campos obrigatórios (*).")
                    else:
                        unidade_sigla = mapa_unidades[unid_label]
                        
                        novo_risco_dados = {
                            "unidade": unidade_sigla,
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
                            "situacao_status": "Identificado"
                        }
                        try:
                            res_novo_risco = supabase.table("riscos").insert(novo_risco_dados).execute()
                            
                            if res_novo_risco.data and len(res_novo_risco.data) > 0:
                                novo_risco_id = res_novo_risco.data[0]["id"]
                                dados_tramitacao_inicial = {
                                    "risco_id": novo_risco_id,
                                    "unidade_origem": unidade_sigla,
                                    "unidade_destino": unidade_sigla,
                                    "usuario_remetente": resp_input,
                                    "parecer_observacao": f"Registro inicial e avaliação do risco. Matriz: {badge_calc}."
                                }
                                supabase.table("tramitacoes").insert(dados_tramitacao_inicial).execute()

                            st.success(f"✅ Risco registrado com sucesso! Classificação: {badge_calc}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar o risco no banco de dados: {e}")

# ---------------------------------------------------------
# PÁGINA: MONITORAMENTO
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Monitoramento":
    st.title("📌 Monitoramento e Acompanhamento de Riscos")
    
    try:
        res_riscos = supabase.table("riscos").select("*").order("id", desc=True).execute()
        lista_riscos = res_riscos.data or []
    except Exception as e:
        st.error(f"Erro ao carregar riscos: {e}")
        lista_riscos = []

    if not lista_riscos:
        st.info("Nenhum risco cadastrado para monitoramento.")
    else:
        mapa_riscos_mon = {f"Risco #{r['id']} | {r['unidade']} - {r['evento'][:50]}...": r for r in lista_riscos}
        risco_sel_label = st.selectbox("Selecione o Risco para Acompanhamento 360°:", list(mapa_riscos_mon.keys()))
        risco_obj = mapa_riscos_mon[risco_sel_label]
        r_id = risco_obj["id"]

        st.divider()

        t_visao, t_acoes, t_timeline = st.tabs([
            "🔍 Visão Geral e Indicadores", 
            "📋 Ações de Tratamento Vinculadas", 
            "🕒 Timeline / Linha do Tempo Visual"
        ])

        with t_visao:
            p_val = risco_obj.get("probabilidade", 1)
            i_val = risco_obj.get("impacto", 1)
            nv_val, class_val, badge_val, cor_hex = calcular_nivel_e_classificacao(p_val, i_val)

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            col_m1.metric("Nível de Risco (Matriz Etapa 2)", f"{nv_val}", f"{class_val}")
            col_m2.metric("Probabilidade", f"{p_val} / 5", LABELS_PROBABILIDADE.get(p_val, ""))
            col_m3.metric("Impacto", f"{i_val} / 5", LABELS_IMPACTO.get(i_val, ""))
            col_m4.metric("Situação Atual", risco_obj.get("situacao_status", "Identificado"))

            st.markdown("---")
            st.markdown(f"**Matriz de Avaliação:** {badge_val}")
            st.markdown(f"**Evento:** {risco_obj.get('evento')}")
            st.markdown(f"**Causa:** {risco_obj.get('causa', '-')}")
            st.markdown(f"**Consequência:** {risco_obj.get('consequencia', '-')}")
            st.markdown(f"**Unidade:** {risco_obj.get('unidade')} | **Gestor:** {risco_obj.get('gestor_risco')}")

        with t_acoes:
            try:
                res_ac = supabase.table("acoes_tratamento").select("*").eq("risco_id", r_id).order("numero_sequencial").execute()
                lista_ac = res_ac.data or []
                
                if lista_ac:
                    for ac in lista_ac:
                        seq = ac["numero_sequencial"]
                        st_ac = ac.get("status_acao", "Pendente")
                        bad_prazo, _ = obter_badge_prazo(ac.get("previsao_data_conclusao"), st_ac)
                        
                        with st.expander(f"Ação #{seq}: {ac['acao']} ({st_ac}) | {bad_prazo}"):
                            st.write(f"**Objetivo:** {ac.get('objetivo_acao')}")
                            st.write(f"**Responsável:** {ac.get('nome_responsavel_implementacao')} ({ac.get('unidade_responsavel')})")
                            st.write(f"**Como Executar:** {ac.get('como_sera_implementada')}")
                            st.write(f"**Período:** {formatar_data_br(ac.get('previsao_data_inicio'))} até {formatar_data_br(ac.get('previsao_data_conclusao'))}")
                else:
                    st.info("Nenhuma ação cadastrada para este risco.")
            except Exception as e:
                st.error(f"Erro ao carregar ações: {e}")

        with t_timeline:
            renderizar_timeline_risco(r_id)

# ---------------------------------------------------------
# PÁGINA: DASHBOARDS
# ---------------------------------------------------------

elif st.session_state.pagina_atual == "Dashboards":
    st.title("📊 Painel de Indicadores SIGER")
    st.caption("Índices de Execução, Cumprimento de Prazos, Tratamento de Riscos e Atenção Rápida")
    st.divider()
    
    # Carregar dados diretamente do Supabase/SIGER
    try:
        df_planos, df_riscos = carregar_dados_siger()
    except Exception as e:
        st.error(f"Erro ao carregar dados dos indicadores: {e}")
        df_planos, df_riscos = pd.DataFrame(), pd.DataFrame()
    
    if df_planos.empty and df_riscos.empty:
        st.warning("Nenhum dado encontrado no banco para gerar os indicadores SIGER.")
    else:
        # 1. Filtros na Barra Lateral
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros do Dashboard")
        
        # Filtro por Eixo
        eixos_disponiveis = ["Todos"] + (list(df_planos["eixo"].unique()) if "eixo" in df_planos.columns else [])
        eixo_sel = st.sidebar.selectbox("Filtrar por Eixo", eixos_disponiveis)
        
        # Filtro por Status
        status_disponiveis = ["Todos"] + (list(df_planos["status"].unique()) if "status" in df_planos.columns else [])
        status_sel = st.sidebar.selectbox("Filtrar por Status", status_disponiveis)
        
        # Aplicar Filtros nos Planos
        df_f = df_planos.copy()
        if not df_f.empty:
            if eixo_sel != "Todos" and "eixo" in df_f.columns:
                df_f = df_f[df_f["eixo"] == eixo_sel]
            if status_sel != "Todos" and "status" in df_f.columns:
                df_f = df_f[df_f["status"] == status_sel]
            
        # 2. Cálculo dos Indicadores SIGER
        iet_val, iet_desc = calcular_iet(df_f)
        icp_val, icp_desc = calcular_icp(df_f)
        itr_val, itr_desc = calcular_itr(df_riscos)
        iar_val, iar_cat, iar_desc = classificar_iar(iet_val, icp_val, itr_val)
        
        # 3. Cards com os Resultados
        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
        
        with c_kpi1:
            st.metric(label="IET (Execução)", value=f"{iet_val:.1f}%")
            st.caption(f"**Situação:** {iet_desc}")
            
        with c_kpi2:
            st.metric(label="ICP (Prazos)", value=f"{icp_val:.1f}%")
            st.caption(f"**Situação:** {icp_desc}")
            
        with c_kpi3:
            st.metric(label="ITR (Riscos)", value=f"{itr_val:.1f}%")
            st.caption(f"**Situação:** {itr_desc}")
            
        with c_kpi4:
            st.metric(label="IAR (Atenção)", value=f"{iar_val:.1f}")
            st.caption(f"**Nível:** {iar_cat}")

        st.markdown("---")
        
        # 4. Tabela Resumo por Eixo
        if not df_planos.empty and "eixo" in df_planos.columns:
            st.subheader("📌 Desempenho por Eixo Estratégico")
            
            eixos = df_planos["eixo"].unique()
            dados_eixos = []
            
            for e in eixos:
                sub_df = df_planos[df_planos["eixo"] == e]
                v_iet, _ = calcular_iet(sub_df)
                v_icp, _ = calcular_icp(sub_df)
                dados_eixos.append({
                    "Eixo": e,
                    "Total de Planos": len(sub_df),
                    "IET (%)": round(v_iet, 1),
                    "ICP (%)": round(v_icp, 1)
                })
                
            df_resumo = pd.DataFrame(dados_eixos)
            st.dataframe(df_resumo, use_container_width=True)

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
# DEMAIS PÁGINAS / FALLBACK
# ---------------------------------------------------------
else:
    st.title(f"🛠️ {st.session_state.pagina_atual}")
    if st.session_state.sub_pagina_atual:
        st.subheader(f"Área: {st.session_state.sub_pagina_atual}")
    st.info("Você não possui permissão para acessar esta área ou o módulo está em estruturação.")
