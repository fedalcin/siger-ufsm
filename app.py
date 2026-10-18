import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
import os
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
import base64

# ---------------------------------------------------------
# MÓDULO DE CRIPTOGRAFIA E NOTIFICAÇÕES POR E-MAIL (SMTP)
# ---------------------------------------------------------
def _obter_chave_fernet():
    key_base = st.secrets["SUPABASE_KEY"][:32].zfill(32)
    return base64.urlsafe_b64encode(key_base.encode())

def criptografar_texto(texto):
    if not texto: return ""
    f = Fernet(_obter_chave_fernet())
    return f.encrypt(texto.encode()).decode()

def descriptografar_texto(texto_cripto):
    if not texto_cripto: return ""
    try:
        f = Fernet(_obter_chave_fernet())
        return f.decrypt(texto_cripto.encode()).decode()
    except Exception:
        return texto_cripto

def obter_configuracoes_smtp():
    smtp_conf = {}
    try:
        res = supabase.table("configuracoes").select("chave, valor").like("chave", "smtp_%").execute()
        if res.data:
            mapa = {i["chave"]: i["valor"] for i in res.data}
            smtp_conf["server"] = mapa.get("smtp_server")
            smtp_conf["port"] = mapa.get("smtp_port", 587)
            smtp_conf["email"] = mapa.get("smtp_email")
            
            senha_cripto = mapa.get("smtp_password", "")
            smtp_conf["password"] = descriptografar_texto(senha_cripto)
    except Exception as e:
        print(f"Erro ao buscar SMTP do banco: {e}")

    if not smtp_conf.get("server") or not smtp_conf.get("email"):
        secrets_smtp = st.secrets.get("smtp", {})
        smtp_conf["server"] = secrets_smtp.get("server")
        smtp_conf["port"] = secrets_smtp.get("port", 587)
        smtp_conf["email"] = secrets_smtp.get("email")
        smtp_conf["password"] = secrets_smtp.get("password")

    return smtp_conf

def obter_emails_unidade_ou_usuario(unidade_sigla=None, nome_usuario=None):
    emails = []
    try:
        if nome_usuario and nome_usuario not in ["Toda a Unidade", "Todos os Servidores / Gestores"]:
            res_usr = supabase.table("usuarios").select("email").ilike("nome", f"%{nome_usuario.strip()}%").eq("ativo", True).execute()
            if res_usr.data:
                emails.extend([u["email"] for u in res_usr.data if u.get("email")])

        if unidade_sigla and unidade_sigla != "S/U":
            res_u_email = supabase.table("unidades").select("email_unidade").eq("sigla", unidade_sigla).execute()
            if res_u_email.data:
                em_sec = res_u_email.data[0].get("email_unidade")
                if em_sec:
                    emails.append(em_sec.strip())

            res_unid_usrs = supabase.table("usuarios").select("email").eq("unidade_sigla", unidade_sigla).eq("ativo", True).execute()
            if res_unid_usrs.data:
                emails.extend([u["email"] for u in res_unid_usrs.data if u.get("email")])

    except Exception as e:
        print(f"Erro ao buscar e-mails para notificação: {e}")
        
    return list(set(emails))

def enviar_email_notificacao_siger(destinatarios_list, assunto, mensagem_html):
    if not destinatarios_list:
        return False
    try:
        smtp_conf = obter_configuracoes_smtp()
        smtp_server = smtp_conf.get("server")
        smtp_port = smtp_conf.get("port", 587)
        smtp_user = smtp_conf.get("email")
        smtp_password = smtp_conf.get("password")

        if not smtp_server or not smtp_user or not smtp_password:
            return False

        emails_validos = list(set([e.strip().lower() for e in destinatarios_list if e and "@" in e]))
        if not emails_validos:
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = f"SIGER - Notificações <{smtp_user}>"
        msg["To"] = ", ".join(emails_validos)

        msg.attach(MIMEText(mensagem_html, "html"))

        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, emails_validos, msg.as_string())
            
        return True
    except Exception as e:
        print(f"⚠️ Falha ao enviar e-mail de notificação: {e}")
        return False

# Importação dos cálculos gerenciais e operacionais do SIGER
from calculos_siger import (
    calcular_situacao_revisao_risco,
    calcular_situacao_prazo_acao,
    calcular_iet,
    calcular_icp,
    calcular_itr,
    calcular_iar_risco,
    calcular_exposicao_agregada
)

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
    
    /* Cabeçalhos dos Expanders na Sidebar */
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

    /* Botões Início e Caixa de Entrada */
    .btn-inicio-sidebar button {
        background-color: #002147 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        width: 100% !important;
        border: 1px solid #001733 !important;
    }
    .btn-inicio-sidebar button:hover {
        background-color: #003366 !important;
        color: #ffffff !important;
    }

    /* Regra geral para o container dos botões da Sidebar */
    section[data-testid="stSidebar"] div.stButton > button {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
    }

    /* Botões do Menu Interno (dentro dos Expanders) */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] div.stButton > button {
        width: calc(100% - 20px) !important;
        margin-left: 20px !important;
        border: none !important;
        background-color: #f8f9fa !important;
        color: #333333 !important;
        padding: 6px 10px !important;
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

    /* REGRA CHAVE: Força o alinhamento à esquerda em todos os elementos de texto internos do Streamlit */
    section[data-testid="stSidebar"] div.stButton > button * {
        text-align: left !important;
        justify-content: flex-start !important;
        margin-left: 0 !important;
        width: 100% !important;
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

    /* ESTILOS DA MATRIZ DE RISCO 5X5 */
    .risk-matrix-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        font-size: 0.82rem;
    }
    .risk-matrix-table td, .risk-matrix-table th {
        border: 2px solid #ffffff;
        padding: 10px 4px;
        height: 52px;
        vertical-align: middle;
    }
    .cell-green { background-color: #28a745; color: white; font-weight: bold; }
    .cell-yellow { background-color: #ffc107; color: #333; font-weight: bold; }
    .cell-orange { background-color: #fd7e14; color: white; font-weight: bold; }
    .cell-red { background-color: #dc3545; color: white; font-weight: bold; }
    .cell-selected {
        outline: 4px solid #002147 !important;
        outline-offset: -4px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.6);
    }
    .risk-pin {
        background-color: #ffffff;
        color: #002147;
        border-radius: 12px;
        padding: 3px 6px;
        font-weight: 900;
        font-size: 0.78rem;
        display: inline-block;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

TIPOS_UNIDADE_OPCOES = [
    "Administração Central",
    "Unidade Acadêmica",
    "Pró-Reitoria",
    "Diretoria"
]

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
            .select("*, perfis(id, nome, permissoes_json)")\
            .eq("email", email.strip().lower())\
            .eq("ativo", True)\
            .execute()
        
        if res.data and len(res.data) > 0:
            usr = res.data[0]
            hash_bd = usr.get("senha_hash")
            if verificar_senha(senha, hash_bd):
                dados_perf = usr.get("perfis") or {}
                st.session_state.usuario_logado = {
                    "id": usr["id"],
                    "nome": usr["nome"],
                    "email": usr["email"],
                    "unidade": usr.get("unidade_sigla"),
                    "perfil_id": usr.get("perfil_id"),
                    "perfil": dados_perf.get("nome", "Leitor"),
                    "permissoes": dados_perf.get("permissoes_json") or {}
                }
                return True, "Login realizado com sucesso!"
            else:
                return False, "Senha incorreta."
        return False, "Usuário não encontrado ou inativo."
    except Exception as e:
        return False, f"Erro na conexão de autenticação: {e}"

def recarregar_permissoes_usuario_logado():
    """Recarrega dinamicamente do banco as permissões do usuário atual caso tenham sido alteradas"""
    if st.session_state.usuario_logado and st.session_state.usuario_logado.get("perfil_id"):
        try:
            p_id = st.session_state.usuario_logado["perfil_id"]
            res = supabase.table("perfis").select("nome, permissoes_json").eq("id", p_id).execute()
            if res.data:
                p_data = res.data[0]
                st.session_state.usuario_logado["perfil"] = p_data.get("nome")
                st.session_state.usuario_logado["permissoes"] = p_data.get("permissoes_json") or {}
        except Exception:
            pass

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

# Atualiza dinamicamente as permissões do usuário em cada recarga
recarregar_permissoes_usuario_logado()

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

def gerar_barra_progresso_ascii(pct):
    pct_val = max(0, min(100, int(pct or 0)))
    blocos = pct_val // 10
    vazios = 10 - blocos
    return f"{'█' * blocos}{'░' * vazios} {pct_val}%"

# ---------------------------------------------------------
# RECALCULADOR DE STATUS AUTOMÁTICO (REGRA DE TRANSIÇÃO)
# ---------------------------------------------------------
def recalcular_e_atualizar_status_risco(risco_id):
    try:
        res_r_atual = supabase.table("riscos").select("situacao_status").eq("id", risco_id).execute()
        if res_r_atual.data:
            st_atual_banco = res_r_atual.data[0].get("situacao_status")
            if st_atual_banco in ["Encerrado", "Cancelado"]:
                return

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
        st.error(f"Erro ao recalcular status do risco: {e}")

# ---------------------------------------------------------
# RENDERIZADOR DA MATRIZ DE RISCO 5X5 INDIVIDUAL
# ---------------------------------------------------------
def renderizar_matriz_risco_5x5(prob_alvo, imp_alvo, risco_id):
    matriz_cores = [
        ["cell-green", "cell-green", "cell-yellow", "cell-orange", "cell-orange"],
        ["cell-green", "cell-yellow", "cell-yellow", "cell-orange", "cell-red"],
        ["cell-yellow", "cell-yellow", "cell-orange", "cell-red", "cell-red"],
        ["cell-orange", "cell-orange", "cell-red", "cell-red", "cell-red"],
        ["cell-red", "cell-red", "cell-red", "cell-red", "cell-red"]
    ]

    html_code = """
    <table class="risk-matrix-table">
        <thead>
            <tr>
                <th style="width: 15%;">P \\ I</th>
                <th style="width: 17%;">1 (Muito Baixo)</th>
                <th style="width: 17%;">2 (Baixo)</th>
                <th style="width: 17%;">3 (Médio)</th>
                <th style="width: 17%;">4 (Alto)</th>
                <th style="width: 17%;">5 (Muito Alto)</th>
            </tr>
        </thead>
        <tbody>
    """

    for prob_idx in range(5, 0, -1):
        html_code += f"<tr><th>{prob_idx}</th>"
        for imp_idx in range(1, 6):
            cor_classe = matriz_cores[prob_idx - 1][imp_idx - 1]
            eh_selecionado = (prob_idx == prob_alvo and imp_idx == imp_alvo)
            
            sel_class = " cell-selected" if eh_selecionado else ""
            conteudo_celula = f"<span class='risk-pin'>🎯 #{risco_id}</span>" if eh_selecionado else f"{prob_idx * imp_idx}"

            html_code += f'<td class="{cor_classe}{sel_class}">{conteudo_celula}</td>'
        html_code += "</tr>"

    html_code += """
        </tbody>
    </table>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# ---------------------------------------------------------
# RENDERIZADOR DA MATRIZ DE RISCO 5X5 CONSOLIDADA (DASHBOARD)
# ---------------------------------------------------------
def renderizar_matriz_risco_5x5_consolidada(df_riscos_filtrados):
    matriz_cores = [
        ["cell-green", "cell-green", "cell-yellow", "cell-orange", "cell-orange"],
        ["cell-green", "cell-yellow", "cell-yellow", "cell-orange", "cell-red"],
        ["cell-yellow", "cell-yellow", "cell-orange", "cell-red", "cell-red"],
        ["cell-orange", "cell-orange", "cell-red", "cell-red", "cell-red"],
        ["cell-red", "cell-red", "cell-red", "cell-red", "cell-red"]
    ]

    contagem_celulas = {}
    if not df_riscos_filtrados.empty:
        for _, r in df_riscos_filtrados.iterrows():
            p = int(r.get("probabilidade") or 1)
            i = int(r.get("impacto") or 1)
            p = max(1, min(5, p))
            i = max(1, min(5, i))
            contagem_celulas[(p, i)] = contagem_celulas.get((p, i), 0) + 1

    html_code = """
    <table class="risk-matrix-table">
        <thead>
            <tr>
                <th style="width: 15%;">P \\ I</th>
                <th style="width: 17%;">1 (Muito Baixo)</th>
                <th style="width: 17%;">2 (Baixo)</th>
                <th style="width: 17%;">3 (Médio)</th>
                <th style="width: 17%;">4 (Alto)</th>
                <th style="width: 17%;">5 (Muito Alto)</th>
            </tr>
        </thead>
        <tbody>
    """

    for prob_idx in range(5, 0, -1):
        html_code += f"<tr><th>{prob_idx}</th>"
        for imp_idx in range(1, 6):
            cor_classe = matriz_cores[prob_idx - 1][imp_idx - 1]
            qtd = contagem_celulas.get((prob_idx, imp_idx), 0)
            
            if qtd > 0:
                conteudo = f"<span class='risk-pin'>📊 {qtd}</span>"
                sel_class = " cell-selected"
            else:
                conteudo = "-"
                sel_class = ""

            html_code += f'<td class="{cor_classe}{sel_class}">{conteudo}</td>'
        html_code += "</tr>"

    html_code += """
        </tbody>
    </table>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# ---------------------------------------------------------
# COMPONENTE VISUAL DE TIMELINE / LINHA DO TEMPO 360° UNIFICADA
# ---------------------------------------------------------
def renderizar_timeline_risco(risco_id):
    st.markdown("### 🕒 Linha do Tempo e Rastreabilidade 360°")
    
    eventos = []

    try:
        res_r = supabase.table("riscos").select("data_identificacao, gestor_risco, unidade, evento, justificativa_encerramento, usuario_encerramento, data_encerramento").eq("id", risco_id).execute()
        if res_r.data:
            r_data = res_r.data[0]
            dt_ident = r_data.get("data_identificacao")
            eventos.append({
                "tipo": "criacao",
                "data": f"{dt_ident}T00:00:00" if dt_ident else None,
                "titulo": f"🛡️ Criação / Registro do Risco #{risco_id}",
                "sub": f"Unidade: {r_data.get('unidade')} | Gestor: {r_data.get('gestor_risco')}",
                "corpo": f"Risco registrado no sistema: {r_data.get('evento')}"
            })

            if r_data.get("data_encerramento"):
                eventos.append({
                    "tipo": "encerramento",
                    "data": r_data.get("data_encerramento"),
                    "titulo": f"🔒 Encerramento Formal do Risco #{risco_id}",
                    "sub": f"Responsável: {r_data.get('usuario_encerramento') or 'Não informado'}",
                    "corpo": f"**Justificativa:** {r_data.get('justificativa_encerramento') or 'Sem justificativa registrada.'}"
                })
    except Exception:
        pass

    try:
        res_eval = supabase.table("avaliacoes_risco").select("*").eq("risco_id", risco_id).execute()
        for ev in (res_eval.data or []):
            dt_ev = ev.get("created_at") or ev.get("data_avaliacao")
            eventos.append({
                "tipo": "reavaliacao",
                "data": dt_ev,
                "titulo": f"🎯 Reavaliação de Risco (Nível {ev.get('nivel_risco')})",
                "sub": f"Probabilidade: {ev.get('probabilidade')} | Impacto: {ev.get('impacto')} | Avaliador: {ev.get('usuario_avaliador') or 'Sistema'}",
                "corpo": f"**Tipo:** {ev.get('tipo_avaliacao', 'Periódica')} | **Justificativa:** {ev.get('justificativa') or ev.get('observacao') or 'Sem observações'}"
            })
    except Exception:
        pass

    try:
        res_tram = supabase.table("tramitacoes").select("*").eq("risco_id", risco_id).execute()
        for t in (res_tram.data or []):
            eventos.append({
                "tipo": "tramitacao",
                "data": t.get("data_tramitacao"),
                "titulo": f"💬 Tramitação: {t.get('unidade_origem')} ➔ {t.get('unidade_destino')}",
                "sub": f"Remetente: {t.get('usuario_remetente')}",
                "corpo": t.get("parecer_observacao") or "Sem parecer cadastrado."
            })
    except Exception:
        pass

    try:
        res_mov = supabase.table("movimentacoes_acoes").select("*").eq("risco_id", risco_id).execute()
        for m in (res_mov.data or []):
            st_ant = m.get('status_anterior') or 'Início'
            pct = m.get('percentual_conclusao') if m.get('percentual_conclusao') is not None else 0
            eventos.append({
                "tipo": "movimentacao",
                "data": m.get("data_movimentacao"),
                "titulo": f"⚡ Ação nº {m.get('numero_sequencial')} | Avanço ({pct}%)",
                "sub": f"Status: {st_ant} ➔ {m.get('status_novo')} | Responsável: {m.get('usuario_responsavel')}",
                "corpo": m.get("descricao_avanco") or "Avanço registrado."
            })
    except Exception:
        pass

    for e in eventos:
        if not e["data"]:
            e["data"] = "1970-01-01T00:00:00"

    eventos.sort(key=lambda x: x["data"], reverse=True)

    if not eventos:
        st.info("Nenhum registro de movimentação ou histórico para este risco.")
        return

    icones_map = {
        "criacao": "📌",
        "reavaliacao": "🎯",
        "tramitacao": "💬",
        "movimentacao": "⚡",
        "encerramento": "🔒"
    }

    for ev in eventos:
        dt_fmt = formatar_data_hora_br(ev["data"]) if ev["data"] != "1970-01-01T00:00:00" else "Data não registrada"
        ic = icones_map.get(ev["tipo"], "🔹")
        
        st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-header">{ic} {ev['titulo']}</div>
                <div class="timeline-date">🗓️ {dt_fmt} | {ev['sub']}</div>
                <div class="timeline-body">{ev['corpo']}</div>
            </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# BARRA LATERAL (USER INFO & MENU EXPANSÍVEL DINÂMICO)
# ---------------------------------------------------------
if url_logo_siger:
    st.sidebar.image(url_logo_siger, use_container_width=True)
elif os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.title("SIGER")
    st.sidebar.markdown("**Sistema de Gestão de Riscos**")

st.sidebar.divider()

st.sidebar.markdown(f"👤 **{usr_atual['nome']}**")
st.sidebar.caption(f"Perfil: `{perfil_usr}` | Unidade: `{usr_atual['unidade'] or 'Todas'}`")

st.sidebar.divider()

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Início"
if "sub_pagina_atual" not in st.session_state:
    st.session_state.sub_pagina_atual = None

def navegar_para(pagina, sub_pagina=None):
    st.session_state.pagina_atual = pagina
    st.session_state.sub_pagina_atual = sub_pagina

perms = usr_atual.get("permissoes", {})

st.sidebar.subheader("Menu Principal")

# 1. Início e Caixa de Entrada
st.sidebar.markdown('<div class="btn-inicio-sidebar">', unsafe_allow_html=True)
if st.sidebar.button("🏠 Início", use_container_width=True, key="btn_inicio_top"):
    navegar_para("Início")
if is_admin or perms.get("cx_entrada", {}).get("ver", True):
    if st.sidebar.button("📥 Caixa de Entrada", use_container_width=True, key="btn_cx_entrada_top"):
        navegar_para("Caixa de Entrada")
st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.divider()

# Helper para checar se uma subpágina está liberada na matriz do usuário
def tem_acesso_subpagina(key_perm, default_val=False):
    if is_admin:
        return True
    return perms.get(key_perm, {}).get("acesso", default_val)

# 2. Expander Administração
items_adm = [
    ("👥 Usuários", "Usuários", "adm_usuarios"),
    ("🔐 Perfis e Permissões", "Perfis e Permissões", "adm_perfis"),
    ("🖼️ Identidade Visual", "Identidade Visual", "adm_id_visual"),
    ("✍ Texto da Tela Inicial", "Texto da Tela Inicial", "adm_texto_home"),
    ("🔧 Configurações Gerais", "Configurações Gerais", "adm_config_gerais")
]
items_adm_visiveis = [item for item in items_adm if tem_acesso_subpagina(item[2], False)]

if items_adm_visiveis:
    with st.sidebar.expander("⚙ Administração", expanded=False):
        for label, sub_p, key_perm in items_adm_visiveis:
            if st.button(label, key=f"btn_{key_perm}", use_container_width=True):
                navegar_para("Administração do Sistema", sub_p)

# 3. Expander Cadastros
items_cad = [
    ("🏢 Unidades", "Unidades", "cad_unidades"),
    ("🎯 Objetivos Estratégicos", "Objetivos Estratégicos", "cad_objetivos"),
    ("🏷️ Categorias de Risco", "Categorias de Risco", "cad_categorias"),
    ("📚 Documentos da Biblioteca", "Documentos da Biblioteca", "cad_doc_biblioteca")
]
items_cad_visiveis = [item for item in items_cad if tem_acesso_subpagina(item[2], False)]

if items_cad_visiveis:
    with st.sidebar.expander("📝 Cadastros", expanded=False):
        for label, sub_p, key_perm in items_cad_visiveis:
            if st.button(label, key=f"btn_{key_perm}", use_container_width=True):
                navegar_para("Cadastros", sub_p)

# 4. Expander Gestão de Riscos
items_gr = [
    ("📋 Riscos", "Riscos", "gr_riscos"),
    ("📋 Ações de Tratamento", "Ações de Tratamento", "gr_acoes"),
    ("🎯 Reavaliação do Nível de Risco", "Reavaliação do Nível de Risco", "gr_reavaliacao")
]
items_gr_visiveis = [item for item in items_gr if tem_acesso_subpagina(item[2], is_gestor)]

if items_gr_visiveis:
    with st.sidebar.expander("🛡️ Gestão de Riscos", expanded=False):
        for label, sub_p, key_perm in items_gr_visiveis:
            if st.button(label, key=f"btn_{key_perm}", use_container_width=True):
                navegar_para("Gestão de Riscos", sub_p)

# 5. Expander Dashboards
items_dash = [
    ("📌 Acompanhamento de Riscos", "Acompanhamento de Riscos", "dash_acomp"),
    ("📈 Painel Geral", "Painel Geral", "dash_geral")
]
items_dash_visiveis = [item for item in items_dash if tem_acesso_subpagina(item[2], is_gestor)]

if items_dash_visiveis:
    with st.sidebar.expander("📊 Dashboards", expanded=False):
        for label, sub_p, key_perm in items_dash_visiveis:
            if st.button(label, key=f"btn_{key_perm}", use_container_width=True):
                navegar_para("Dashboards", sub_p)

# 6. Expander Biblioteca
if is_admin or perms.get("bib_normativas", {}).get("leitura", True):
    with st.sidebar.expander("📚 Biblioteca", expanded=False):
        if st.button("📄 Documentos e Normativas", key="btn_bib_doc", use_container_width=True):
            navegar_para("Biblioteca", "Documentos e Normativas")

st.sidebar.divider()

if st.sidebar.button("🚪 Sair / Logout", use_container_width=True, key="btn_logout_bottom"):
    st.session_state.usuario_logado = None
    st.rerun()

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
# PÁGINA: ADMINISTRAÇÃO DO SISTEMA
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Administração do Sistema" and (is_admin or any(p.get("acesso") for k, p in perms.items() if k.startswith("adm_"))):
    sub = st.session_state.sub_pagina_atual or "Usuários"
    
    # 1. SUBPÁGINA: USUÁRIOS
    if sub == "Usuários":
        st.title("👥 Usuários")
        st.caption("Gerenciamento e cadastro de usuários do sistema.")
        
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
                                    
                                    res_p = supabase.table("perfis").select("*").execute().data or []
                                    mapa_perfis = {p["nome"]: p["id"] for p in res_p}
                                    idx_p = list(mapa_perfis.keys()).index(u_item.get("perfil_nome")) if u_item.get("perfil_nome") in mapa_perfis else 0
                                    e_perfil = st.selectbox("Perfil de Acesso", list(mapa_perfis.keys()), index=idx_p)
                                    
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

    # SUBPÁGINA: PERFIS E PERMISSÕES DE ACESSO
    elif sub == "Perfis e Permissões" and is_admin:
        st.title("🔐 Gerenciamento de Perfis e Permissões")
        st.caption("Configure individualmente o nível de acesso e operação para cada um dos 15 itens de menu do SIGER.")

        try:
            res_perfis = supabase.table("perfis").select("*").order("id").execute()
            lista_perfis = res_perfis.data or []
        except Exception as e:
            st.error(f"Erro ao carregar perfis: {e}")
            lista_perfis = []

        if lista_perfis:
            mapa_p = {p["nome"]: p for p in lista_perfis}
            
            perfil_sel_nome = st.selectbox(
                "🎯 Selecione o Perfil para Configurar Permissões:", 
                list(mapa_p.keys()),
                key="sb_selecao_perfil_matriz"
            )
            
            perfil_obj = mapa_p[perfil_sel_nome]
            p_id = perfil_obj["id"]

            # Reconsultar diretamente no banco para obter a matriz JSON fresca
            try:
                res_p_fresca = supabase.table("perfis").select("permissoes_json").eq("id", p_id).execute()
                m_perms = res_p_fresca.data[0].get("permissoes_json") if res_p_fresca.data else {}
            except Exception:
                m_perms = perfil_obj.get("permissoes_json") or {}

            if not isinstance(m_perms, dict):
                m_perms = {}

            # Helper para resgatar a permissão exata salva no JSON do perfil
            def def_perm(modulo, operacao, val_default=False):
                mod_dict = m_perms.get(modulo)
                if isinstance(mod_dict, dict) and operacao in mod_dict:
                    return bool(mod_dict[operacao])
                return val_default

            st.divider()

            # Sufixo limpo e exclusivo para prevenir colisões no Streamlit
            sfx = f"p{p_id}"

            with st.form(key=f"form_matriz_perm_{sfx}"):
                st.markdown("### ⚙️ 1. Módulo Administração")
                c1, c2, c3, c4, c5 = st.columns(5)
                
                with c1:
                    st.markdown("**👥 Usuários**")
                    p_usr_acc = st.checkbox("Acessar Usuários", value=def_perm("adm_usuarios", "acesso"), key=f"chk_usr_acc_{sfx}")
                    p_usr_inc = st.checkbox("Incluir Usuários", value=def_perm("adm_usuarios", "incluir"), key=f"chk_usr_inc_{sfx}")
                    p_usr_alt = st.checkbox("Alterar Usuários", value=def_perm("adm_usuarios", "alterar"), key=f"chk_usr_alt_{sfx}")
                    p_usr_exc = st.checkbox("Excluir Usuários", value=def_perm("adm_usuarios", "excluir"), key=f"chk_usr_exc_{sfx}")
                
                with c2:
                    st.markdown("**🔐 Perfis**")
                    p_prf_acc = st.checkbox("Acessar Perfis", value=def_perm("adm_perfis", "acesso"), key=f"chk_prf_acc_{sfx}")
                    p_prf_inc = st.checkbox("Incluir Perfis", value=def_perm("adm_perfis", "incluir"), key=f"chk_prf_inc_{sfx}")
                    p_prf_alt = st.checkbox("Alterar Perfis", value=def_perm("adm_perfis", "alterar"), key=f"chk_prf_alt_{sfx}")
                    p_prf_exc = st.checkbox("Excluir Perfis", value=def_perm("adm_perfis", "excluir"), key=f"chk_prf_exc_{sfx}")

                with c3:
                    st.markdown("**🖼️ Identidade Visual**")
                    p_idv_acc = st.checkbox("Acessar Id. Visual", value=def_perm("adm_id_visual", "acesso"), key=f"chk_idv_acc_{sfx}")
                    p_idv_alt = st.checkbox("Alterar Id. Visual", value=def_perm("adm_id_visual", "alterar"), key=f"chk_idv_alt_{sfx}")

                with c4:
                    st.markdown("**✍ Texto Inicial**")
                    p_txt_acc = st.checkbox("Acessar Texto Initial", value=def_perm("adm_texto_home", "acesso"), key=f"chk_txt_acc_{sfx}")
                    p_txt_alt = st.checkbox("Alterar Texto Initial", value=def_perm("adm_texto_home", "alterar"), key=f"chk_txt_alt_{sfx}")

                with c5:
                    st.markdown("**🔧 Config. Gerais**")
                    p_cfg_acc = st.checkbox("Acessar Config. Gerais", value=def_perm("adm_config_gerais", "acesso"), key=f"chk_cfg_acc_{sfx}")
                    p_cfg_alt = st.checkbox("Alterar Config. Gerais", value=def_perm("adm_config_gerais", "alterar"), key=f"chk_cfg_alt_{sfx}")

                st.divider()

                st.markdown("### 📝 2. Módulo Cadastros")
                c_c1, c_c2, c_c3, c_c4 = st.columns(4)
                
                with c_c1:
                    st.markdown("**🏢 Unidades**")
                    p_und_acc = st.checkbox("Acessar Unidades", value=def_perm("cad_unidades", "acesso"), key=f"chk_und_acc_{sfx}")
                    p_und_inc = st.checkbox("Incluir Unidades", value=def_perm("cad_unidades", "incluir"), key=f"chk_und_inc_{sfx}")
                    p_und_alt = st.checkbox("Alterar Unidades", value=def_perm("cad_unidades", "alterar"), key=f"chk_und_alt_{sfx}")
                    p_und_exc = st.checkbox("Excluir Unidades", value=def_perm("cad_unidades", "excluir"), key=f"chk_und_exc_{sfx}")

                with c_c2:
                    st.markdown("**🎯 Obj. Estratégicos**")
                    p_oe_acc = st.checkbox("Acessar Obj. Estratégicos", value=def_perm("cad_objetivos", "acesso"), key=f"chk_oe_acc_{sfx}")
                    p_oe_inc = st.checkbox("Incluir Obj. Estratégicos", value=def_perm("cad_objetivos", "incluir"), key=f"chk_oe_inc_{sfx}")
                    p_oe_alt = st.checkbox("Alterar Obj. Estratégicos", value=def_perm("cad_objetivos", "alterar"), key=f"chk_oe_alt_{sfx}")
                    p_oe_exc = st.checkbox("Excluir Obj. Estratégicos", value=def_perm("cad_objetivos", "excluir"), key=f"chk_oe_exc_{sfx}")

                with c_c3:
                    st.markdown("**🏷️ Categorias**")
                    p_cat_acc = st.checkbox("Acessar Categorias", value=def_perm("cad_categorias", "acesso"), key=f"chk_cat_acc_{sfx}")
                    p_cat_inc = st.checkbox("Incluir Categorias", value=def_perm("cad_categorias", "incluir"), key=f"chk_cat_inc_{sfx}")
                    p_cat_alt = st.checkbox("Alterar Categorias", value=def_perm("cad_categorias", "alterar"), key=f"chk_cat_alt_{sfx}")
                    p_cat_exc = st.checkbox("Excluir Categorias", value=def_perm("cad_categorias", "excluir"), key=f"chk_cat_exc_{sfx}")

                with c_c4:
                    st.markdown("**📚 Doc. Biblioteca**")
                    p_doc_acc = st.checkbox("Acessar Doc. Biblioteca", value=def_perm("cad_doc_biblioteca", "acesso"), key=f"chk_doc_acc_{sfx}")
                    p_doc_inc = st.checkbox("Incluir PDF Biblioteca", value=def_perm("cad_doc_biblioteca", "incluir"), key=f"chk_doc_inc_{sfx}")
                    p_doc_exc = st.checkbox("Excluir PDF Biblioteca", value=def_perm("cad_doc_biblioteca", "excluir"), key=f"chk_doc_exc_{sfx}")

                st.divider()

                st.markdown("### 🛡️ 3. Módulo Gestão de Riscos")
                c_g1, c_g2, c_g3 = st.columns(3)
                
                with c_g1:
                    st.markdown("**📋 Riscos**")
                    p_rsk_acc = st.checkbox("Acessar Riscos", value=def_perm("gr_riscos", "acesso", True), key=f"chk_rsk_acc_{sfx}")
                    p_rsk_inc = st.checkbox("Incluir Riscos", value=def_perm("gr_riscos", "incluir", True), key=f"chk_rsk_inc_{sfx}")
                    p_rsk_alt = st.checkbox("Alterar Riscos", value=def_perm("gr_riscos", "alterar", True), key=f"chk_rsk_alt_{sfx}")
                    p_rsk_exc = st.checkbox("Excluir Riscos", value=def_perm("gr_riscos", "excluir", True), key=f"chk_rsk_exc_{sfx}")

                with c_g2:
                    st.markdown("**📋 Ações de Tratamento**")
                    p_act_acc = st.checkbox("Acessar Ações", value=def_perm("gr_acoes", "acesso", True), key=f"chk_act_acc_{sfx}")
                    p_act_inc = st.checkbox("Incluir Ações", value=def_perm("gr_acoes", "incluir", True), key=f"chk_act_inc_{sfx}")
                    p_act_alt = st.checkbox("Alterar Ações", value=def_perm("gr_acoes", "alterar", True), key=f"chk_act_alt_{sfx}")
                    p_act_exc = st.checkbox("Excluir Ações", value=def_perm("gr_acoes", "excluir", True), key=f"chk_act_exc_{sfx}")

                with c_g3:
                    st.markdown("**🎯 Reavaliação de Risco**")
                    p_rev_acc = st.checkbox("Acessar Reavaliação", value=def_perm("gr_reavaliacao", "acesso", True), key=f"chk_rev_acc_{sfx}")
                    p_rev_alt = st.checkbox("Permitir Reavaliar Risco", value=def_perm("gr_reavaliacao", "alterar", True), key=f"chk_rev_alt_{sfx}")

                st.divider()

                st.markdown("### 📊 4. Módulo Dashboards & 📚 5. Biblioteca")
                c_d1, c_d2, c_d3 = st.columns(3)

                with c_d1:
                    st.markdown("**📌 Acompanhamento**")
                    p_d1_acc = st.checkbox("Acessar Dash Acompanhamento", value=def_perm("dash_acomp", "acesso", True), key=f"chk_d1_acc_{sfx}")
                    p_d1_outras = st.toggle("Ver Outras Unidades (Acomp)", value=def_perm("dash_acomp", "ver_outras_unidades", True), key=f"chk_d1_out_{sfx}")

                with c_d2:
                    st.markdown("**📈 Painel Geral**")
                    p_d2_acc = st.checkbox("Acessar Painel Geral", value=def_perm("dash_geral", "acesso", True), key=f"chk_d2_acc_{sfx}")
                    p_d2_outras = st.toggle("Ver Outras Unidades (Geral)", value=def_perm("dash_geral", "ver_outras_unidades", True), key=f"chk_d2_out_{sfx}")

                with c_d3:
                    st.markdown("**📄 Doc. e Normativas**")
                    p_bib_read = st.toggle("Permitir Leitura/Download Normativas", value=def_perm("bib_normativas", "leitura", True), key=f"chk_bib_rd_{sfx}")

                st.write("")
                btn_salvar_matriz = st.form_submit_button("💾 Salvar Matriz de Permissões do Perfil", use_container_width=True)

                if btn_salvar_matriz:
                    nova_matriz = {
                        "adm_usuarios": {"acesso": p_usr_acc, "incluir": p_usr_inc, "alterar": p_usr_alt, "excluir": p_usr_exc},
                        "adm_perfis": {"acesso": p_prf_acc, "incluir": p_prf_inc, "alterar": p_prf_alt, "excluir": p_prf_exc},
                        "adm_id_visual": {"acesso": p_idv_acc, "alterar": p_idv_alt},
                        "adm_texto_home": {"acesso": p_txt_acc, "alterar": p_txt_alt},
                        "adm_config_gerais": {"acesso": p_cfg_acc, "alterar": p_cfg_alt},
        
                        "cad_unidades": {"acesso": p_und_acc, "incluir": p_und_inc, "alterar": p_und_alt, "excluir": p_und_exc},
                        "cad_objetivos": {"acesso": p_oe_acc, "incluir": p_oe_inc, "alterar": p_oe_alt, "excluir": p_oe_exc},
                        "cad_categorias": {"acesso": p_cat_acc, "incluir": p_cat_inc, "alterar": p_cat_alt, "excluir": p_cat_exc},
                        "cad_doc_biblioteca": {"acesso": p_doc_acc, "incluir": p_doc_inc, "excluir": p_doc_exc},
        
                        "gr_riscos": {"acesso": p_rsk_acc, "incluir": p_rsk_inc, "alterar": p_rsk_alt, "excluir": p_rsk_exc},
                        "gr_acoes": {"acesso": p_act_acc, "incluir": p_act_inc, "alterar": p_act_alt, "excluir": p_act_exc},
                        "gr_reavaliacao": {"acesso": p_rev_acc, "alterar": p_rev_alt},
        
                        "dash_acomp": {"acesso": p_d1_acc, "ver_outras_unidades": p_d1_outras},
                        "dash_geral": {"acesso": p_d2_acc, "ver_outras_unidades": p_d2_outras},
                        "bib_normativas": {"leitura": p_bib_read}
                    }

                    try:
                        supabase.table("perfis").update({"permissoes_json": nova_matriz}).eq("id", p_id).execute()
        
                        if usr_atual.get("perfil_id") == p_id:
                            st.session_state.usuario_logado["permissoes"] = nova_matriz
            
                        st.toast(f"✅ Permissões do perfil '{perfil_sel_nome}' atualizadas com sucesso!", icon="🎉")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar matriz de permissões: {e}")

    # 2. SUBPÁGINA: IDENTIDADE VISUAL
    elif sub == "Identidade Visual":
        st.title("🖼️ Identidade Visual")
        st.caption("Personalize os logotipos exibidos no sistema enviando imagens diretamente para o armazenamento.")
        
        col_v1, col_v2, col_v3 = st.columns(3)
        
        def salvar_logo_storage_e_config(file_obj, key_config, file_name):
            try:
                bytes_data = file_obj.getvalue()
                bucket = supabase.storage.from_("identidade_visual")
                
                try:
                    bucket.remove([file_name])
                except Exception:
                    pass
                
                bucket.upload(file_name, bytes_data, {"content-type": file_obj.type})
                public_url = bucket.get_public_url(file_name)
                
                supabase.table("configuracoes").upsert({
                    "chave": key_config,
                    "valor": public_url
                }, on_conflict="chave").execute()
                
                return True, public_url
            except Exception as e:
                return False, str(e)

        with col_v1:
            st.markdown("##### 1. Logotipo Completo SIGER")
            if url_logo_siger:
                st.image(url_logo_siger, use_container_width=True)
            else:
                st.info("Logotipo completo padrão ativo.")
                
            up_siger = st.file_uploader("Enviar novo logo completo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="up_siger")
            if up_siger and st.button("💾 Atualizar Logo SIGER"):
                ok, res_url = salvar_logo_storage_e_config(up_siger, "url_logo_siger", "logo_siger.png")
                if ok:
                    st.success("Logo completo atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar imagem: {res_url}")

        with col_v2:
            st.markdown("##### 2. Logotipo Reduzido / Ícone (Favicon)")
            if url_logo_reduzido:
                st.image(url_logo_reduzido, width=100)
            else:
                st.info("Ícone reduzido padrão ativo.")
                
            up_red = st.file_uploader("Enviar novo ícone reduzido (PNG/JPG)", type=["png", "jpg", "jpeg"], key="up_red")
            if up_red and st.button("💾 Atualizar Logo Reduzido"):
                ok, res_url = salvar_logo_storage_e_config(up_red, "url_logo_reduzido", "logo_reduzido.png")
                if ok:
                    st.success("Logo reduzido atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar imagem: {res_url}")

        with col_v3:
            st.markdown("##### 3. Logotipo da Instituição")
            if url_logo_instituicao:
                st.image(url_logo_instituicao, use_container_width=True)
            else:
                st.info("Nenhum logotipo institucional cadastrado.")
                
            up_inst = st.file_uploader("Enviar logo institucional (PNG/JPG)", type=["png", "jpg", "jpeg"], key="up_inst")
            if up_inst and st.button("💾 Atualizar Logo Institucional"):
                ok, res_url = salvar_logo_storage_e_config(up_inst, "url_logo_instituicao", "logo_instituicao.png")
                if ok:
                    st.success("Logo institucional atualizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar imagem: {res_url}")

    # 3. SUBPÁGINA: TEXTO DA TELA INICIAL
    elif sub == "Texto da Tela Inicial":
        st.title("✍ Texto da Tela Inicial")
        st.caption("Altere a mensagem de boas-vindas apresentada na página inicial do sistema.")
        
        texto_atual = ""
        try:
            res_txt = supabase.table("configuracoes").select("valor").eq("chave", "texto_pagina_inicial").execute()
            if res_txt.data and len(res_txt.data) > 0:
                texto_atual = res_txt.data[0]["valor"]
        except Exception as e:
            st.error(f"Erro ao carregar texto atual: {e}")

        with st.form("form_edit_texto_inicial"):
            novo_texto_home = st.text_area(
                "Texto de Boas-Vindas e Apresentação (Suporta tags HTML como <b>, <br>, <i>)*", 
                value=texto_atual, 
                height=250
            )
            
            if st.form_submit_button("💾 Salvar Texto da Tela Inicial"):
                try:
                    supabase.table("configuracoes").upsert({
                        "chave": "texto_pagina_inicial",
                        "valor": novo_texto_home
                    }, on_conflict="chave").execute()
                    
                    st.success("✅ Texto da tela inicial atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar texto inicial: {e}")

    # 4. SUBPÁGINA: CONFIGURAÇÕES GERAIS
    elif sub in ["Configurações Gerais", "Configurações"]:
        st.title("🔧 Configurações Gerais")
        st.subheader("📧 Servidor de E-mail para Envio de Notificações (SMTP)")
        st.caption("Cadastre as credenciais do servidor de e-mail institucional para envio automatizado de alertas aos usuários.")

        cfg_smtp = {}
        try:
            res_cfg = supabase.table("configuracoes").select("chave, valor").like("chave", "smtp_%").execute()
            if res_cfg.data:
                cfg_smtp = {item["chave"]: item["valor"] for item in res_cfg.data}
        except Exception as e:
            st.error(f"Erro ao carregar configurações de e-mail: {e}")

        with st.form("form_config_smtp"):
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                smtp_servidor = st.text_input("Servidor SMTP*", value=cfg_smtp.get("smtp_server", "smtp.gmail.com"), placeholder="smtp.instituicao.edu.br")
                smtp_porta = st.number_input("Porta SMTP*", value=int(cfg_smtp.get("smtp_port", 587)), step=1)
            with c_s2:
                smtp_email = st.text_input("E-mail Remetente*", value=cfg_smtp.get("smtp_email", ""), placeholder="siger-notificacoes@instituicao.edu.br")
                
                senha_salva_cripto = cfg_smtp.get("smtp_password", "")
                senha_descriptografada = descriptografar_texto(senha_salva_cripto)
                
                smtp_senha = st.text_input("Senha do E-mail / App Password*", value=senha_descriptografada, type="password")

            st.caption("🔒 *A senha é mantida de forma criptografada na tabela de configurações.*")
            btn_salvar_smtp = st.form_submit_button("💾 Salvar Credenciais SMTP")

        if btn_salvar_smtp:
            if not smtp_servidor or not smtp_email or not smtp_senha:
                st.warning("Preencha todos os campos obrigatórios da configuração SMTP.")
            else:
                try:
                    senha_criptografada = criptografar_texto(smtp_senha)
                    configs_para_salvar = [
                        {"chave": "smtp_server", "valor": smtp_servidor.strip()},
                        {"chave": "smtp_port", "valor": str(smtp_porta)},
                        {"chave": "smtp_email", "valor": smtp_email.strip()},
                        {"chave": "smtp_password", "valor": senha_criptografada}
                    ]
                    for item in configs_para_salvar:
                        supabase.table("configuracoes").upsert(item, on_conflict="chave").execute()
                        
                    st.success("✅ Servidor de e-mail registrado e pronto para envio de notificações!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar credenciais: {e}")

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
        st.info(f"Exibindo demandas sob gestão da unidade **{unidade_ativa}**")

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
            gestor_risco_origem = dados_risco.get("gestor_risco", "Não informado")
            unidade_risco_origem = dados_risco.get("unidade", unidade_ativa)
            situacao_risco = dados_risco.get("situacao_status", "Identificado")
            
            ultimo_remetente_txt = "Registro Inicial"
            try:
                res_u_tram = supabase.table("tramitacoes")\
                    .select("usuario_remetente, unidade_origem, data_tramitacao")\
                    .eq("risco_id", r_id)\
                    .order("id", desc=True)\
                    .limit(1)\
                    .execute()
                if res_u_tram.data:
                    tram_d = res_u_tram.data[0]
                    ultimo_remetente_txt = f"{tram_d.get('usuario_remetente')} ({tram_d.get('unidade_origem')})"
            except Exception:
                pass

            txt_badge_prazo, _ = obter_badge_prazo(acao_item.get("previsao_data_conclusao"), status_ac)
            badge_nova_txt = "🔵 Nova | " if (exibe_badge_nova and status_ac == "Pendente") else ""
            titulo_card = f"{badge_nova_txt}Risco #{r_id} ({situacao_risco}) | Ação {seq} | {txt_badge_prazo} | {nome_acao}"

            with st.expander(titulo_card):
                c_det1, c_det2 = st.columns([2, 1])
                
                with c_det1:
                    st.markdown(f"**Evento de Risco:** {evento_risco}")
                    st.markdown(f"**Status Atual do Risco:** `{situacao_risco}`")
                    st.markdown(f"**Ação de Tratamento:** {nome_acao}")
                    st.markdown(f"**Objetivo:** {acao_item.get('objetivo_acao', '-')}")
                    st.markdown(f"**Como Executar:** {acao_item.get('como_sera_implementada', '-')}")
                    
                with c_det2:
                    st.markdown(f"**Caráter:** `{carater}`")
                    st.markdown(f"🛡️ **Gestor do Risco:** `{gestor_risco_origem}` ({unidade_risco_origem})")
                    st.markdown(f"👤 **Responsável pela Ação:** `{acao_item.get('nome_responsavel_implementacao', 'Toda a Unidade')}`")
                    st.markdown(f"📩 **Último Remetente:** `{ultimo_remetente_txt}`")
                    st.markdown(f"**Previsão Início:** {formatar_data_br(acao_item.get('previsao_data_inicio'))}")
                    st.markdown(f"**Previsão Conclusão:** {formatar_data_br(acao_item.get('previsao_data_conclusao'))}")
                    
                st.divider()
                
                pct_atual = acao_item.get("percentual_execucao") or 0
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
                        pct_atual = mov.get("percentual_conclusao", pct_atual)
                        st.write(f"**Avanço Atual:** `{pct_atual}%`")
                        st.progress(float(pct_atual) / 100.0)
                        st.caption(f"Última atualização ({formatar_data_hora_br(mov.get('data_movimentacao'))}): {mov.get('descricao_avanco')}")
                    else:
                        st.write(f"**Avanço Atual:** `{pct_atual}%`")
                        st.progress(float(pct_atual) / 100.0)
                except Exception:
                    st.caption("Não foi possível carregar a última movimentação.")

                col_btn_wf1, col_btn_wf2, col_btn_wf3 = st.columns([1, 1, 1])

                with col_btn_wf1:
                    if is_gestor:
                        pop_atuar = st.popover("⚡ Responder / Atualizar Demanda")
                        with pop_atuar:
                            st.markdown(f"### Atuação na Ação nº {seq} (Risco #{r_id})")
                            
                            idx_dest_def = opcoes_unid.index(unidade_risco_origem) if unidade_risco_origem in opcoes_unid else 0
                            unid_destino_wf = st.selectbox(
                                "Encaminhar Para Unidade*", 
                                opcoes_unid, 
                                index=idx_dest_def, 
                                key=f"sb_dest_out_{r_id}_{seq}"
                            )

                            try:
                                res_u_dest = supabase.table("usuarios")\
                                    .select("nome")\
                                    .eq("unidade_sigla", unid_destino_wf)\
                                    .eq("ativo", True)\
                                    .order("nome")\
                                    .execute().data or []
                            except Exception:
                                res_u_dest = []

                            usrs_filtrados = [u["nome"] for u in res_u_dest if u.get("nome")]
                            opts_resp_dest = ["Toda a Unidade"] + usrs_filtrados

                            with st.form(f"form_wf_atuacao_{r_id}_{seq}"):
                                st.markdown("##### 1. Progresso e Status da Ação")
                                novo_pct = st.slider("Percentual de Execução Concluído", 0, 100, value=int(pct_atual), step=5, key=f"sld_pct_{r_id}_{seq}")
                                
                                opcoes_status_wf = ["Pendente", "Em andamento", "Devolvida", "Concluída"]
                                idx_st_wf = opcoes_status_wf.index(status_ac) if status_ac in opcoes_status_wf else 1
                                novo_status_ac = st.selectbox("Novo Status da Ação", opcoes_status_wf, index=idx_st_wf, key=f"sb_st_{r_id}_{seq}")
                                
                                st.markdown("##### 2. Relato de Avanço / Parecer Técnico")
                                desc_avanco_wf = st.text_area(
                                    "Relato de Avanço / Evidências / Justificativa*", 
                                    placeholder="Descreva as medidas adotadas, providências tomadas...",
                                    key=f"txt_av_{r_id}_{seq}"
                                )
                                
                                st.markdown("##### 3. Encaminhamento e Tramitação")
                                col_t_wf1, col_t_wf2 = st.columns(2)
                                with col_t_wf1:
                                    resp_destino_wf = st.selectbox(
                                        "Destinatário / Responsável Específico*", 
                                        options=opts_resp_dest, 
                                        index=0, 
                                        key=f"sb_resp_dest_{r_id}_{seq}"
                                    )
                                with col_t_wf2:
                                    st.text_input("Remetente (Seu Usuário)", value=usr_atual["nome"], disabled=True, key=f"txt_rem_dis_{r_id}_{seq}")
                                
                                btn_enviar_wf = st.form_submit_button("🚀 Gravar Avanço e Tramitar Demanda")
                                
                                if btn_enviar_wf:
                                    if not desc_avanco_wf.strip():
                                        st.warning("Por favor, preencha o relato do avanço / parecer técnico.")
                                    else:
                                        try:
                                            remetente_efetivo = usr_atual["nome"]
                                            resp_destino_final = resp_destino_wf
                                            nome_para_email = None if resp_destino_final == "Toda a Unidade" else resp_destino_final

                                            dados_update_acao = {
                                                "status_acao": novo_status_ac,
                                                "percentual_execucao": novo_pct,
                                                "unidade_responsavel": unid_destino_wf,
                                                "nome_responsavel_implementacao": resp_destino_final
                                            }
                                            
                                            if novo_status_ac == "Concluída":
                                                dados_update_acao["data_conclusao_efetiva"] = date.today().strftime("%Y-%m-%d")

                                            supabase.table("acoes_tratamento").update(dados_update_acao).eq("risco_id", r_id).eq("numero_sequencial", seq).execute()
                                            
                                            dados_mov_wf = {
                                                "risco_id": r_id,
                                                "numero_sequencial": seq,
                                                "status_anterior": status_ac,
                                                "status_novo": novo_status_ac,
                                                "descricao_avanco": desc_avanco_wf,
                                                "percentual_conclusao": novo_pct,
                                                "unidade_responsavel": unid_destino_wf,
                                                "usuario_responsavel": resp_destino_final
                                            }
                                            supabase.table("movimentacoes_acoes").insert(dados_mov_wf).execute()

                                            dados_tram_wf = {
                                                "risco_id": r_id,
                                                "unidade_origem": unidade_ativa,
                                                "unidade_destino": unid_destino_wf,
                                                "usuario_remetente": remetente_efetivo,
                                                "parecer_observacao": desc_avanco_wf
                                            }
                                            supabase.table("tramitacoes").insert(dados_tram_wf).execute()

                                            recalcular_e_atualizar_status_risco(r_id)

                                            emails_dest = obter_emails_unidade_ou_usuario(unidade_sigla=unid_destino_wf, nome_usuario=nome_para_email)
                                            if emails_dest:
                                                assunto_e = f"💬 [SIGER] Tramitação de Demanda - Risco #{r_id} (Ação {seq})"
                                                corpo_html = f"""
                                                <h3>Tramitação de Demanda no SIGER</h3>
                                                <p>Olá,</p>
                                                <p>A ação nº <b>{seq}</b> do Risco <b>#{r_id}</b> foi tramitada por <b>{remetente_efetivo}</b> ({unidade_ativa}) para a sua unidade (<b>{unid_destino_wf}</b>).</p>
                                                <ul>
                                                    <li><b>Status:</b> {novo_status_ac} ({novo_pct}%)</li>
                                                    <li><b>Destinatário Atribuído:</b> {resp_destino_final}</li>
                                                    <li><b>Relato / Parecer:</b> {desc_avanco_wf}</li>
                                                </ul>
                                                <p>Acesse a Caixa de Entrada do SIGER para acompanhar a demanda.</p>
                                                """
                                                enviar_email_notificacao_siger(emails_dest, assunto_e, corpo_html)

                                            st.success("✅ Demanda atualizada, tramitada e notificação por e-mail enviada!")
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
                                st.text_input("Responsável pelo Encerramento", value=usr_atual["nome"], disabled=True, key=f"txt_resp_enc_dis_{r_id}_{seq}")
                                justificativa_enc = st.text_area("Justificativa e Parecer Final*", placeholder="Descreva os motivos...", key=f"txt_just_enc_{r_id}_{seq}")
                
                                if st.form_submit_button("🏁 Confirmar Encerramento Formal"):
                                    if not justificativa_enc.strip():
                                        st.warning("Preencha a justificativa para encerrar.")
                                    else:
                                        try:
                                            dt_agora_iso = datetime.now().isoformat()
                                            resp_enc_efetivo = usr_atual["nome"]

                                            supabase.table("riscos").update({
                                                "situacao_status": "Encerrado",
                                                "data_encerramento": dt_agora_iso,
                                                "usuario_encerramento": resp_enc_efetivo,
                                                "justificativa_encerramento": justificativa_enc.strip()
                                            }).eq("id", r_id).execute()
                            
                                            dados_tram_enc = {
                                                "risco_id": r_id,
                                                "unidade_origem": unidade_ativa,
                                                "unidade_destino": unidade_ativa,
                                                "usuario_remetente": resp_enc_efetivo,
                                                "parecer_observacao": f"🔒 ENCERRAMENTO FORMAL DO RISCO: {justificativa_enc.strip()}"
                                            }
                                            supabase.table("tramitacoes").insert(dados_tram_enc).execute()

                                            st.success("✅ Risco encerrado formalmente com justificativa e responsável registrados!")
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
# PÁGINA: GESTÃO DE RISCOS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Gestão de Riscos":
    sub_gr = st.session_state.sub_pagina_atual or "Riscos"

    # 1. TELA: RISCOS
    if sub_gr == "Riscos" and is_gestor:
        st.title("📋 Riscos")
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
                        st_risco = r_item.get('situacao_status', 'Identificado')
                        
                        with st.expander(f"🛡️ Risco #{r_item['id']} ({st_risco}) | {r_item['unidade']} | Nível {nivel} {cor_nivel}"):
                            st.markdown(f"**Risco:** {r_item.get('evento', '')}")
                            st.markdown(f"**Causa:** {r_item.get('causa', '')} | **Consequência:** {r_item.get('consequencia', '')}")
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
                                        e_prob = st.slider("Probabilidade", 1, 5, value=r_item.get('probabilidade', 1))
                                        e_imp = st.slider("Impacto", 1, 5, value=r_item.get('impacto', 1))
                                        e_resp = st.text_input("Gestor do Risco", value=r_item.get('gestor_risco', ''))
                                        
                                        options_status = ['Identificado', 'Em análise', 'Em tratamento', 'Monitorado', 'Encerrado', 'Cancelado']
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
    
                                            dados_avaliac = {
                                                "risco_id": r_item['id'],
                                                "probabilidade": e_prob,
                                                "impacto": e_imp,
                                                "nivel_risco": novo_nivel,
                                                "data_avaliacao": datetime.now().isoformat(),
                                                "usuario_avaliador": usr_atual["nome"],
                                                "tipo_avaliacao": "Reavaliação Periódica",
                                                "justificativa": "Reavaliação de probabilidade e impacto gravada via painel gerencial."
                                            }
                                            supabase.table("avaliacoes_risco").insert(dados_avaliac).execute()
    
                                            st.success("✅ Risco reavaliado e novo ponto registrado!")
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
                                                if not justificativa_enc_cad.strip() or not resp_enc_cad.strip():
                                                    st.warning("Preencha todos os campos obrigatórios.")
                                                else:
                                                    try:
                                                        dt_agora_iso = datetime.now().isoformat()
                                                        supabase.table("riscos").update({
                                                            "situacao_status": "Encerrado",
                                                            "data_encerramento": dt_agora_iso,
                                                            "usuario_encerramento": resp_enc_cad.strip(),
                                                            "justificativa_encerramento": justificativa_enc_cad.strip()
                                                        }).eq("id", r_item['id']).execute()
                            
                                                        dados_tram_enc = {
                                                            "risco_id": r_item['id'],
                                                            "unidade_origem": r_item.get('unidade', 'S/U'),
                                                            "unidade_destino": r_item.get('unidade', 'S/U'),
                                                            "usuario_remetente": resp_enc_cad.strip(),
                                                            "parecer_observacao": f"🔒 ENCERRAMENTO FORMAL DO RISCO: {justificativa_enc_cad.strip()}"
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

                st.markdown("##### 4. Governança e Prazos")
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    resp_input = st.text_input("Gestor do Risco*", value=usr_atual["nome"])
                with col_g2:
                    dt_identificacao = st.date_input("Data de Identificação*", datetime.now(), format="DD/MM/YYYY")
                with col_g3:
                    periodicidade_sel = st.selectbox("Periodicidade de Revisão", ["Mensal", "Trimestral", "Semestral", "Anual"])

                submitted_risco = st.form_submit_button("💾 Salvar Risco")
                
                if submitted_risco:
                    if not evento_input or not resp_input:
                        st.warning("Preencha os campos obrigatórios.")
                    else:
                        nivel_calc = prob_val * imp_val
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
                                    "parecer_observacao": "Registro inicial e identificação do risco no sistema."
                                }
                                supabase.table("tramitacoes").insert(dados_tramitacao_inicial).execute()

                            st.success("✅ Risco registrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar o risco no banco de dados: {e}")

    # 2. TELA: REAVALIAÇÃO DO NÍVEL DE RISCO
    elif sub_gr == "Reavaliação do Nível de Risco" and is_gestor:
        st.title("🎯 Reavaliação do Nível de Risco")
        st.caption("Atualize a probabilidade e o impacto do risco com base na efetividade das ações executadas.")

        try:
            res_riscos = supabase.table("riscos").select("*").order("id", desc=True).execute()
            lista_riscos = res_riscos.data or []
        except Exception as e:
            st.error(f"Erro ao carregar lista de riscos: {e}")
            lista_riscos = []

        if not lista_riscos:
            st.info("Nenhum risco cadastrado para reavaliação.")
        else:
            mapa_riscos_reav = {f"Risco #{r['id']} | {r['unidade']} - {r['evento'][:60]}...": r for r in lista_riscos}
            risco_sel_label = st.selectbox("🎯 Selecione o Risco para Reavaliar:", list(mapa_riscos_reav.keys()))
            risco_obj = mapa_riscos_reav[risco_sel_label]
            r_id = risco_obj["id"]

            st.divider()

            col_inf1, col_inf2 = st.columns([2, 1])
            with col_inf1:
                st.markdown(f"### 🛡️ Risco #{r_id}: {risco_obj.get('evento')}")
                st.markdown(f"**Unidade:** `{risco_obj.get('unidade')}` | **Gestor:** `{risco_obj.get('gestor_risco', '-')}`")
                st.markdown(f"**Causa:** {risco_obj.get('causa', '-')}")
                st.markdown(f"**Consequência:** {risco_obj.get('consequencia', '-')}")

            with col_inf2:
                p_at = int(risco_obj.get("probabilidade") or 1)
                i_at = int(risco_obj.get("impacto") or 1)
                n_at = int(risco_obj.get("nivel_risco") or (p_at * i_at))
                cor_n = "🔴 Crítico" if n_at >= 15 else "🟡 Médio" if n_at >= 8 else "🟢 Baixo"

                st.info(f"""
                📊 **Situação Atual do Risco:**
                * **Probabilidade:** {p_at} / 5
                * **Impacto:** {i_at} / 5
                * **Nível de Risco:** **{n_at}** ({cor_n})
                """)

            st.divider()

            st.markdown("### 📝 Formulário de Reavaliação")
            with st.form(f"form_reavaliar_dedicado_{r_id}"):
                col_sl1, col_sl2 = st.columns(2)
                with col_sl1:
                    p_nova = st.slider("Nova Probabilidade (1 a 5)*", 1, 5, value=p_at)
                with col_sl2:
                    i_novo = st.slider("Novo Impacto (1 a 5)*", 1, 5, value=i_at)

                just_reav = st.text_area(
                    "Justificativa da Reavaliação*", 
                    placeholder="Descreva as razões técnicas, ações implementadas ou evidências que justificam a alteração da nota..."
                )

                novo_nivel_calc = p_nova * i_novo
                cor_novo_n = "🔴 Crítico" if novo_nivel_calc >= 15 else "🟡 Médio" if novo_nivel_calc >= 8 else "🟢 Baixo"
                st.caption(f"⚡ **Novo Nível do Risco Calculado:** `{novo_nivel_calc}` ({cor_novo_n})")

                btn_sub_reav = st.form_submit_button("💾 Confirmar e Gravar Nova Avaliação")

            if btn_sub_reav:
                if not just_reav.strip():
                    st.warning("Preencha a justificativa da reavaliação.")
                else:
                    try:
                        novo_nivel_calc = p_nova * i_novo

                        supabase.table("riscos").update({
                            "probabilidade": p_nova,
                            "impacto": i_novo
                        }).eq("id", r_id).execute()

                        supabase.table("avaliacoes_risco").insert({
                            "risco_id": r_id,
                            "probabilidade": p_nova,
                            "impacto": i_novo,
                            "data_avaliacao": datetime.now().isoformat(),
                            "usuario_avaliador": usr_atual["nome"],
                            "tipo_avaliacao": "Reavaliação Periódica",
                            "justificativa": just_reav.strip()
                        }).execute()

                        st.toast(f"✅ Risco #{r_id} reavaliado com sucesso para Nível {novo_nivel_calc}!", icon="🎉")
                        st.success(f"✅ Risco #{r_id} reavaliado com sucesso para Nível {novo_nivel_calc}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar reavaliação: {e}")

    # 3. TELA: AÇÕES DE TRATAMENTO
    else:
        st.title("📋 Ações de Tratamento")
        
        tab_list_acoes, tab_nova_acao = st.tabs(["🔍 Ações Cadastradas", "➕ Cadastrar Nova Ação de Tratamento"])
        
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
                                    pop_edit_ac = st.popover("✏ Edit Ação")
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
                                        st.warning("Deseja remover esta ação de tratamento?")
                                        if st.button("Confirmar Exclusão", key=f"btn_del_ac_{r_id}_{seq}"):
                                            try:
                                                supabase.table("acoes_tratamento").delete().eq("risco_id", r_id).eq("numero_sequencial", seq).execute()
                                                recalcular_e_atualizar_status_risco(r_id)
                                                st.success("Ação removida e status do risco atualizado!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao excluir ação: {e}")
                else:
                    st.info("Nenhuma ação de tratamento cadastrada até o momento.")
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
                            acao_input = st.text_input("Ação de Tratamento*", placeholder="Ex: Implantar rotina diária de backup automatizado")
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

                                    emails_dest = obter_emails_unidade_ou_usuario(unidade_sigla=unidade_resp_sel, nome_usuario=nome_resp_input)
                                    if emails_dest:
                                        assunto_e = f"🛡️ [SIGER] Nova Ação de Tratamento Atribuída - Risco #{id_risco_sel} (Ação {prox_seq})"
                                        corpo_html = f"""
                                        <h3>Nova Ação de Tratamento Atribuída</h3>
                                        <p>Olá,</p>
                                        <p>Uma nova ação foi vinculada ao Risco <b>#{id_risco_sel}</b> e atribuída para a sua unidade (<b>{unidade_resp_sel}</b>).</p>
                                        <ul>
                                            <li><b>Ação:</b> {acao_input}</li>
                                            <li><b>Responsável:</b> {nome_resp_input}</li>
                                            <li><b>Prazo Conclusão:</b> {dt_conclusao.strftime('%d/%m/%Y')}</li>
                                        </ul>
                                        <p>Acesse o SIGER para acompanhar a demanda.</p>
                                        """
                                        enviar_email_notificacao_siger(emails_dest, assunto_e, corpo_html)

                                    st.success(f"✅ Ação nº {prox_seq} cadastrada e notificação por e-mail enviada!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao salvar ação no banco de dados: {e}")

# ---------------------------------------------------------
# PÁGINA: CADASTROS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Cadastros":
    sub = st.session_state.sub_pagina_atual or "Unidades"

    # 1. SUBPÁGINA: UNIDADES
    if sub == "Unidades":
        st.title("🏢 Unidades")
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
                        email_item = item.get('email_unidade', '')
                        
                        with st.expander(f"📍 **{sigla_item}** | {nome_item} ({tipo_exibicao})"):
                            col_info, col_acoes = st.columns([3, 1])
                            with col_info:
                                st.write(f"**Sigla:** {sigla_item}")
                                st.write(f"**Nome por Extenso:** {nome_item}")
                                st.write(f"**Tipo da Unidade:** {tipo_exibicao}")
                                st.write(f"**E-mail da Unidade:** `{email_item or 'Não informado'}`")
                            
                            with col_acoes:
                                if is_admin:
                                    modal_edit = st.popover("✏️ Editar")
                                    with modal_edit:
                                        st.markdown("### Editar Unidade")
                                        with st.form(f"form_edit_unid_{sigla_item}"):
                                            edit_nome = st.text_input("Nome Extenso", value=nome_item)
                                            val_atual = item.get('tipo_unidade')
                                            idx_tipo = TIPOS_UNIDADE_OPCOES.index(val_atual) if val_atual in TIPOS_UNIDADE_OPCOES else 0
                                            edit_tipo = st.selectbox("Tipo da Unidade*", options=TIPOS_UNIDADE_OPCOES, index=idx_tipo)
                                            edit_email = st.text_input("E-mail Institucional da Unidade", value=email_item, placeholder="setor@instituicao.edu.br")
                                            
                                            if st.form_submit_button("💾 Salvar Alterações"):
                                                try:
                                                    supabase.table("unidades").update({
                                                        "nome_extenso": edit_nome,
                                                        "tipo_unidade": edit_tipo,
                                                        "email_unidade": edit_email.strip().lower() if edit_email else None
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
                    email_unid_input = st.text_input("E-mail Institucional da Unidade", placeholder="Ex: prae@instituicao.edu.br")
                
                submitted_unid = st.form_submit_button("💾 Salvar Unidade")
                
                if submitted_unid:
                    if not sigla or not nome_extenso:
                        st.warning("Por favor, preencha a Sigla e o Nome por Extenso.")
                    else:
                        try:
                            supabase.table("unidades").insert({
                                "sigla": sigla,
                                "nome_extenso": nome_extenso,
                                "tipo_unidade": tipo_unidade_sel,
                                "email_unidade": email_unid_input.strip().lower() if email_unid_input else None
                            }).execute()
                            st.toast(f"✅ Unidade '{sigla}' registrada!", icon="🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar unidade: {e}")

    # 2. SUBPÁGINA: OBJETIVOS ESTRATÉGICOS
    elif sub == "Objetivos Estratégicos":
        st.title("🎯 Objetivos Estratégicos")
        tab_oe_list, tab_oe_novo = st.tabs(["🔍 Objetivos Cadastrados", "➕ Novo Objetivo Estratégico"])
        
        with tab_oe_list:
            try:
                res_oe = supabase.table("objetivos_estrategicos").select("*").order("codigo").execute()
                dados_oe = res_oe.data or []
                
                if dados_oe:
                    st.write(f"Total de objetivos estratégicos cadastrados: **{len(dados_oe)}**")
                    for item in dados_oe:
                        cod_item = str(item['codigo']).strip()
                        desc_item = item.get('descricao', '')
                        desafio_item = item.get('desafio', '')
                        dimensao_item = item.get('dimensao', '')
                        
                        with st.expander(f"🎯 **{cod_item}** | {desc_item[:80]}..."):
                            st.write(f"**Código:** {cod_item}")
                            st.write(f"**Descrição:** {desc_item}")
                            st.write(f"**Desafio:** {desafio_item}")
                            st.write(f"**Dimensão:** {dimensao_item}")
                            
                            if is_admin:
                                col_info, col_acoes = st.columns([1, 1])
                                with col_info:
                                    pop_edit = st.popover("✏️ Editar")
                                    with pop_edit:
                                        st.markdown("### Editar Objetivo Estratégico")
                                        with st.form(f"form_edit_oe_{cod_item}"):
                                            e_desc = st.text_area("Descrição", value=desc_item)
                                            e_desafio = st.text_area("Desafio", value=desafio_item)
                                            e_dimensao = st.text_input("Dimensão", value=dimensao_item)
                                            
                                            if st.form_submit_button("💾 Salvar Alterações"):
                                                try:
                                                    supabase.table("objetivos_estrategicos").update({
                                                        "descricao": e_desc,
                                                        "desafio": e_desafio,
                                                        "dimensao": e_dimensao
                                                    }).eq("codigo", cod_item).execute()
                                                    st.success("Objetivo Estratégico atualizado!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro ao atualizar objetivo estratégico: {e}")

                                with col_acoes:
                                    pop_del = st.popover("🗑️ Excluir")
                                    with pop_del:
                                        st.warning(f"Deseja excluir o objetivo '{cod_item}'?")
                                        if st.button("Confirmar Exclusão", key=f"btn_del_oe_{cod_item}"):
                                            try:
                                                res_vinc = supabase.table("riscos").select("id").eq("objetivo_estrategico", cod_item).execute()
                                                if res_vinc.data and len(res_vinc.data) > 0:
                                                    st.error(f"❌ Impossível excluir. Existem {len(res_vinc.data)} risco(s) vinculados a este objetivo.")
                                                else:
                                                    supabase.table("objetivos_estrategicos").delete().eq("codigo", cod_item).execute()
                                                    st.success(f"Objetivo '{cod_item}' excluído com sucesso!")
                                                    st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao excluir objetivo estratégico: {e}")
                else:
                    st.info("Nenhum objetivo estratégico cadastrado no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao carregar objetivos estratégicos: {e}")

        with tab_oe_novo:
            with st.form("form_cadastrar_oe", clear_on_submit=True):
                col_oe1, col_oe2 = st.columns([1, 2])
                with col_oe1:
                    new_codigo = st.text_input("Código*", placeholder="Ex: OE01, OE-02").upper().strip()
                    new_dimensao = st.text_input("Dimensão*", placeholder="Ex: Governança, Ensino, Infraestrutura")
                with col_oe2:
                    new_descricao = st.text_area("Descrição*", placeholder="Descreva o Objetivo Estratégico...")
                
                new_desafio = st.text_area("Desafio*", placeholder="Descreva o Desafio associado...")
                
                submitted_oe = st.form_submit_button("💾 Salvar Objetivo Estratégico")
                
                if submitted_oe:
                    if not new_codigo or not new_descricao or not new_desafio or not new_dimensao:
                        st.warning("Por favor, preencha todos os campos do formulário.")
                    else:
                        try:
                            supabase.table("objetivos_estrategicos").insert({
                                "codigo": new_codigo,
                                "descricao": new_descricao,
                                "desafio": new_desafio,
                                "dimensao": new_dimensao
                            }).execute()
                            st.success(f"✅ Objetivo Estratégico '{new_codigo}' cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar objetivo estratégico: {e}")

    # 3. SUBPÁGINA: CATEGORIAS DE RISCO
    elif sub == "Categorias de Risco":
        st.title("🏷️ Categorias de Risco")
        tab_cat_list, tab_cat_nova = st.tabs(["🔍 Categorias Cadastradas", "➕ Nova Categoria"])
        
        with tab_cat_list:
            try:
                res_cat = supabase.table("categorias_riscos").select("*").order("tipo").execute()
                dados_cat = res_cat.data or []
                
                if dados_cat:
                    st.write(f"Total de categorias registradas: **{len(dados_cat)}**")
                    for c_item in dados_cat:
                        cid = c_item["id"]
                        ctipo = c_item.get("tipo", "")
                        csub = c_item.get("sub_tipo", "")
                        cdet = c_item.get("detalhamento", "")
                        
                        with st.expander(f"🏷️ **{ctipo}** / {csub}"):
                            st.write(f"**Tipo:** {ctipo}")
                            st.write(f"**Subtipo:** {csub}")
                            st.write(f"**Detalhamento:** {cdet or '-'}")
                            st.caption(f"Criado em: {formatar_data_hora_br(c_item.get('criado_em'))}")
                            
                            if is_admin:
                                col_c_edit, col_c_del = st.columns([1, 1])
                                with col_c_edit:
                                    pop_edit_cat = st.popover("✏️ Editar")
                                    with pop_edit_cat:
                                        with st.form(f"form_edit_cat_{cid}"):
                                            e_tipo = st.text_input("Tipo", value=ctipo)
                                            e_sub = st.text_input("Subtipo", value=csub)
                                            e_det = st.text_area("Detalhamento", value=cdet)
                                            
                                            if st.form_submit_button("💾 Salvar Alterações"):
                                                try:
                                                    supabase.table("categorias_riscos").update({
                                                        "tipo": e_tipo,
                                                        "sub_tipo": e_sub,
                                                        "detalhamento": e_det
                                                    }).eq("id", cid).execute()
                                                    st.success("Categoria atualizada!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro ao atualizar categoria: {e}")

                                with col_c_del:
                                    pop_del_cat = st.popover("🗑️ Excluir")
                                    with pop_del_cat:
                                        st.warning(f"Deseja excluir a categoria '{ctipo} / {csub}'?")
                                        if st.button("Confirmar Exclusão", key=f"btn_del_cat_{cid}"):
                                            try:
                                                res_vinc_c = supabase.table("riscos").select("id").eq("categoria_risco", cid).execute()
                                                if res_vinc_c.data and len(res_vinc_c.data) > 0:
                                                    st.error(f"❌ Impossível excluir. Existem {len(res_vinc_c.data)} risco(s) vinculados a esta categoria.")
                                                else:
                                                    supabase.table("categorias_riscos").delete().eq("id", cid).execute()
                                                    st.success("Categoria excluída com sucesso!")
                                                    st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao excluir categoria: {e}")
                else:
                    st.info("Nenhuma categoria cadastrada.")
            except Exception as e:
                st.error(f"Erro ao carregar categorias de risco: {e}")
                
        with tab_cat_nova:
            with st.form("form_nova_categoria", clear_on_submit=True):
                col_cat1, col_cat2 = st.columns(2)
                with col_cat1:
                    new_tipo = st.text_input("Tipo*", placeholder="Ex: Operacional, Financeiro, Estratégico")
                with col_cat2:
                    new_sub_tipo = st.text_input("Subtipo*", placeholder="Ex: Gestão Orçamentária, Recursos Humanos")
                
                new_detalhamento = st.text_area("Detalhamento", placeholder="Descrição detalhada dos riscos abrangidos nesta categoria...")
                
                if st.form_submit_button("💾 Salvar Categoria"):
                    if not new_tipo or not new_sub_tipo:
                        st.warning("Preencha o Tipo e o Subtipo da categoria.")
                    else:
                        try:
                            supabase.table("categorias_riscos").insert({
                                "tipo": new_tipo,
                                "sub_tipo": new_sub_tipo,
                                "detalhamento": new_detalhamento
                            }).execute()
                            st.success("✅ Categoria de risco registrada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao cadastrar categoria: {e}")

    # 4. SUBPÁGINA: DOCUMENTOS DA BIBLIOTECA
    elif sub == "Documentos da Biblioteca":
        st.title("📚 Documentos da Biblioteca")
        tab_b_list, tab_b_novo = st.tabs(["🔍 Documentos Cadastrados", "➕ Enviar Novo Documento PDF"])
        
        with tab_b_list:
            try:
                res_docs = supabase.table("biblioteca").select("*").order("id", desc=True).execute()
                list_docs = res_docs.data or []
                
                if list_docs:
                    st.write(f"Total de documentos na biblioteca: **{len(list_docs)}**")
                    for d in list_docs:
                        doc_id = d["id"]
                        d_titulo = d.get("titulo", "Sem título")
                        d_desc = d.get("descricao", "")
                        d_url = d.get("url_publica", "#")
                        d_arq = d.get("nome_arquivo", "")
                        
                        with st.expander(f"📄 **{d_titulo}**"):
                            st.write(f"**Descrição:** {d_desc or 'Sem descrição'}")
                            st.write(f"**Nome do Arquivo:** {d_arq}")
                            st.caption(f"Data do Upload: {formatar_data_hora_br(d.get('data_upload'))}")
                            
                            col_b_act1, col_b_act2 = st.columns([1, 1])
                            with col_b_act1:
                                st.link_button("📥 Abrir / Download PDF", d_url)
                            with col_b_act2:
                                if is_admin:
                                    pop_del_doc = st.popover("🗑 Excluir Documento")
                                    with pop_del_doc:
                                        st.warning(f"Deseja remover o documento '{d_titulo}'?")
                                        if st.button("Confirmar Exclusão", key=f"btn_del_doc_{doc_id}"):
                                            try:
                                                if d_arq:
                                                    try:
                                                        supabase.storage.from_("biblioteca_documentos").remove([d_arq])
                                                    except Exception:
                                                        pass
                                                supabase.table("biblioteca").delete().eq("id", doc_id).execute()
                                                st.success("Documento excluído com sucesso!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao excluir documento: {e}")
                else:
                    st.info("Nenhum documento cadastrado na biblioteca.")
            except Exception as e:
                st.error(f"Erro ao carregar biblioteca de documentos: {e}")

        with tab_b_novo:
            with st.form("form_upload_doc_biblioteca", clear_on_submit=True):
                doc_titulo = st.text_input("Título do Documento / Normativa*")
                doc_desc = st.text_area("Descrição do Conteúdo")
                doc_file = st.file_uploader("Selecione o arquivo PDF*", type=["pdf"])
                
                if st.form_submit_button("📤 Salvar e Publicar Documento"):
                    if not doc_titulo or not doc_file:
                        st.warning("Preencha o título e selecione um arquivo PDF.")
                    else:
                        try:
                            nome_arquivo_saneado = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{doc_file.name.replace(' ', '_')}"
                            bytes_pdf = doc_file.getvalue()
                            
                            bucket_bib = supabase.storage.from_("biblioteca_documentos")
                            bucket_bib.upload(nome_arquivo_saneado, bytes_pdf, {"content-type": "application/pdf"})
                            public_url_pdf = bucket_bib.get_public_url(nome_arquivo_saneado)
                            
                            supabase.table("biblioteca").insert({
                                "titulo": doc_titulo,
                                "descricao": doc_desc,
                                "nome_arquivo": nome_arquivo_saneado,
                                "url_publica": public_url_pdf,
                                "data_upload": datetime.now().isoformat()
                            }).execute()
                            
                            st.success("✅ Documento publicado com sucesso na biblioteca!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao enviar documento para a biblioteca: {e}")

# ---------------------------------------------------------
# PÁGINA: DASHBOARDS
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Dashboards":
    sub_dash = st.session_state.sub_pagina_atual or "Acompanhamento de Riscos"

    # 1. TELA: ACOMPANHAMENTO DE RISCOS
    if sub_dash == "Acompanhamento de Riscos":
        st.title("📌 Acompanhamento de Riscos")
        st.caption("Painel gerencial do risco selecionado com métricas, matriz 5x5, evolução histórica e ações de mitigação.")
        
        try:
            res_riscos = supabase.table("riscos").select("*").order("id", desc=True).execute()
            lista_riscos = res_riscos.data or []
        except Exception as e:
            st.error(f"Erro ao carregar lista de riscos: {e}")
            lista_riscos = []

        if not lista_riscos:
            st.info("Nenhum risco cadastrado para acompanhamento.")
        else:
            mapa_riscos_mon = {f"Risco #{r['id']} | {r['unidade']} - {r['evento'][:55]}...": r for r in lista_riscos}
            risco_sel_label = st.selectbox("🎯 Selecione o Risco para Análise Painel 360°:", list(mapa_riscos_mon.keys()))
            risco_obj = mapa_riscos_mon[risco_sel_label]
            r_id = risco_obj["id"]

            try:
                res_ac_mon = supabase.table("acoes_tratamento").select("*").eq("risco_id", r_id).order("numero_sequencial").execute()
                df_ac_mon = pd.DataFrame(res_ac_mon.data or [])
            except Exception:
                df_ac_mon = pd.DataFrame()

            try:
                res_hist = supabase.table("avaliacoes_risco").select("*").eq("risco_id", r_id).order("created_at", desc=False).execute()
                df_hist_eval = pd.DataFrame(res_hist.data or [])
            except Exception:
                df_hist_eval = pd.DataFrame()

            data_prox_rev = risco_obj.get("proxima_revisao") or risco_obj.get("data_proxima_revisao")
            sit_revisao = calcular_situacao_revisao_risco(data_prox_rev)
            
            tot_acoes_r = len(df_ac_mon)
            if not df_ac_mon.empty:
                acoes_concluidas_r = sum(1 for _, row in df_ac_mon.iterrows() if row.get("status_status") == "Concluída" or row.get("status_acao") == "Concluída")
                acoes_atrasadas_r = sum(
                    1 for _, row in df_ac_mon.iterrows()
                    if calcular_situacao_prazo_acao(row.get("status_acao"), row.get("previsao_data_conclusao")) == "⚠️ Atrasada"
                )
                iet_r = calcular_iet(df_ac_mon)
                icp_r = calcular_icp(df_ac_mon)
                pct_conc_r = round(float((acoes_concluidas_r / tot_acoes_r) * 100), 2) if tot_acoes_r > 0 else 0.0
                itr_r = calcular_itr(iet_r, pct_conc_r, icp_r)
            else:
                acoes_concluidas_r = 0
                acoes_atrasadas_r = 0
                iet_r = 0.0
                icp_r = 100.0
                pct_conc_r = 0.0
                itr_r = 0.0

            iar_info = calcular_iar_risco(
                nivel_risco=risco_obj.get("nivel_risco", 1),
                acoes_atrasadas=acoes_atrasadas_r,
                total_acoes=tot_acoes_r,
                situacao_revisao=sit_revisao
            )

            st.divider()

            col_hdr1, col_hdr2 = st.columns([2.5, 1.5])
            with col_hdr1:
                st.markdown(f"### 🛡️ Risco #{r_id}: {risco_obj.get('evento')}")
                st.markdown(f"**Unidade Responsável:** `{risco_obj.get('unidade')}` | **Gestor:** `{risco_obj.get('gestor_risco', '-')}`")
                st.markdown(f"**Causa:** {risco_obj.get('causa', '-')}")
                st.markdown(f"**Consequência:** {risco_obj.get('consequencia', '-')}")
                
            with col_hdr2:
                st.info(f"""
                📅 **Data de Identificação:** {formatar_data_br(risco_obj.get('data_identificacao'))}  
                🔄 **Periodicidade:** {risco_obj.get('periodicidade_revisao', 'Não informada')}  
                📆 **Próxima Revisão:** {formatar_data_br(data_prox_rev)} (`{sit_revisao}`)
                """)

            st.markdown("#### 📊 Grid de Indicadores Gerenciais")
            
            nivel_val = risco_obj.get('nivel_risco', 1)
            cor_nivel_str = "🔴 Crítico" if nivel_val >= 15 else "🟡 Médio" if nivel_val >= 8 else "🟢 Baixo"

            kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6, kpi_c7 = st.columns(7)
            kpi_c1.metric("Nível do Risco", f"{nivel_val}", cor_nivel_str)
            kpi_c2.metric("Total Ações", tot_acoes_r)
            kpi_c3.metric("Concluídas", acoes_concluidas_r)
            kpi_c4.metric("Atrasadas", acoes_atrasadas_r)
            kpi_c5.metric("Execução do Tratamento", f"{iet_r}%")
            kpi_c6.metric("Cumprimento de Prazos", f"{icp_r}%")
            kpi_c7.metric("Tratamento do Risco", f"{itr_r}%")

            st.divider()

            col_sec1, col_sec2 = st.columns([1.2, 1.3])

            with col_sec1:
                st.markdown("### 🎲 Matriz de Risco 5x5 Individual")
                st.caption("Destaque dinâmico na célula ocupada pelo risco (Probabilidade x Impacto).")
                prob_atual = int(risco_obj.get("probabilidade") or 1)
                imp_atual = int(risco_obj.get("impacto") or 1)
                
                renderizar_matriz_risco_5x5(prob_atual, imp_atual, r_id)

            with col_sec2:
                st.markdown("### 📈 Evolução Histórica das Avaliações")
                
                if not df_hist_eval.empty:
                    df_chart = df_hist_eval.copy()
                    col_dt = 'created_at' if 'created_at' in df_chart.columns else 'data_avaliacao'
                    df_chart['Data'] = pd.to_datetime(df_chart[col_dt]).dt.strftime('%d/%m %H:%M')
                    df_chart_display = df_chart[['Data', 'nivel_risco', 'probabilidade', 'impacto']].rename(
                        columns={'nivel_risco': 'Nível de Risco'}
                    ).set_index('Data')
                    
                    st.line_chart(df_chart_display['Nível de Risco'])
                else:
                    st.caption("Nenhum histórico de reavaliações gravado na tabela `avaliacoes_risco`. Exibindo ponto atual:")
                    data_ident_str = formatar_data_br(risco_obj.get('data_identificacao'))
                    df_ponto_unico = pd.DataFrame({
                        "Data": [data_ident_str],
                        "Nível de Risco": [nivel_val]
                    }).set_index("Data")
                    st.line_chart(df_ponto_unico)

                st.markdown("### ⚠️ Pontos de Atenção e Alertas Automáticos")
                
                alertas = []
                if nivel_val >= 15 and tot_acoes_r == 0:
                    alertas.append("🔴 **Risco Crítico sem Ações:** O risco possui nível crítico (≥ 15) mas nenhuma ação de mitigação cadastrada.")
                if sit_revisao == "Atrasada":
                    alertas.append("⏰ **Revisão Temporal Atrasada:** A data da próxima revisão do risco expirou.")
                if acoes_atrasadas_r > 0:
                    alertas.append(f"⚠️ **Ações de Mitigação Atrasadas:** Existem {acoes_atrasadas_r} ação(ões) com prazo de conclusão vencido.")
                if iet_r < 50.0 and tot_acoes_r > 0:
                    alertas.append(f"📉 **Baixa Execução do Tratamento:** O Índice de Execução do Tratamento está em apenas {iet_r}%.")

                if alertas:
                    for alt in alertas:
                        st.warning(alt)
                else:
                    st.success("✅ **Nenhum ponto de atenção crítico detectado.** O acompanhamento do risco está em conformidade com as metas.")

            st.divider()

            st.markdown("### 🛡️ Planos de Ação e Progresso das Mitigações")
            
            if not df_ac_mon.empty:
                df_tabela_exib = []
                for _, ac in df_ac_mon.iterrows():
                    seq = ac.get("numero_sequencial")
                    nome_ac = ac.get("acao")
                    carater_ac = ac.get("carater_acao", "Preventivo")
                    resp_ac = ac.get("nome_responsavel_implementacao", "-")
                    st_ac = ac.get("status_acao", "Pendente")
                    pct_exec = ac.get("percentual_execucao") or ac.get("percentual_conclusao") or 0
                    dt_fim = formatar_data_br(ac.get("previsao_data_conclusao"))
                    
                    txt_badge, _ = obter_badge_prazo(ac.get("previsao_data_conclusao"), st_ac)
                    barra_ascii = gerar_barra_progresso_ascii(pct_exec)

                    df_tabela_exib.append({
                        "Ação nº": seq,
                        "Descrição da Ação": nome_ac,
                        "Caráter": carater_ac,
                        "Responsável": resp_ac,
                        "Status": st_ac,
                        "Previsão Conclusão": dt_fim,
                        "Situação Prazo": txt_badge,
                        "Barra de Progresso": barra_ascii
                    })

                df_exib_final = pd.DataFrame(df_tabela_exib)
                st.dataframe(df_exib_final, use_container_width=True)

                with st.expander("🕒 Linha do Tempo Visual e Tramitações Históricas"):
                    renderizar_timeline_risco(r_id)
            else:
                st.info("Nenhuma ação de mitigação cadastrada para este risco até o momento.")

    # 2. TELA: PAINEL GERAL
    elif sub_dash == "Painel Geral":
        st.title("📈 Painel Geral")
        st.caption("Visão estratégica de governança e monitoramento integrado de exposição a riscos.")

        try:
            res_r = supabase.table("riscos").select("*").execute()
            df_riscos_base = pd.DataFrame(res_r.data or [])
            
            res_a = supabase.table("acoes_tratamento").select("*").execute()
            df_acoes_base = pd.DataFrame(res_a.data or [])

            res_cat_db = supabase.table("categorias_riscos").select("id, tipo, sub_tipo").execute().data or []
            mapa_cat_nomes = {c["id"]: f"{c['tipo']} / {c['sub_tipo']}" for c in res_cat_db}
        except Exception as e:
            st.error(f"Erro ao carregar dados do banco de dados: {e}")
            df_riscos_base = pd.DataFrame()
            df_acoes_base = pd.DataFrame()
            mapa_cat_nomes = {}

        if not df_riscos_base.empty and "categoria_risco" in df_riscos_base.columns:
            df_riscos_base["nome_categoria"] = df_riscos_base["categoria_risco"].map(mapa_cat_nomes).fillna("Não Categorizado")

        with st.expander("🔍 Filtros Globais do Painel Executivo", expanded=True):
            f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)

            with f_col1:
                opts_unid = ["Todas"] + sorted(list(df_riscos_base["unidade"].dropna().unique())) if not df_riscos_base.empty else ["Todas"]
                filtro_unid = st.selectbox("🏢 Unidade", opts_unid)

            with f_col2:
                opts_oe = ["Todos"] + sorted(list(df_riscos_base["objetivo_estrategico"].dropna().unique())) if not df_riscos_base.empty else ["Todos"]
                filtro_oe = st.selectbox("🎯 Obj. Estratégico", opts_oe)

            with f_col3:
                opts_cat = ["Todas"] + sorted(list(df_riscos_base["nome_categoria"].dropna().unique())) if not df_riscos_base.empty else ["Todas"]
                filtro_cat = st.selectbox("🏷️ Categoria", opts_cat)

            with f_col4:
                opts_nivel = ["Todos", "🔴 Crítico (≥ 15)", "🟡 Médio (8 - 14)", "🟢 Baixo (1 - 7)"]
                filtro_nivel = st.selectbox("⚡ Nível de Risco", opts_nivel)

            with f_col5:
                opts_st = ["Todos"] + sorted(list(df_riscos_base["situacao_status"].dropna().unique())) if not df_riscos_base.empty else ["Todos"]
                filtro_st = st.selectbox("📌 Status Risco", opts_st)

            with f_col6:
                st.write("")
                st.write("")
                if st.button("🧹 Limpar Filtros", use_container_width=True):
                    st.rerun()

            f_dt1, f_dt2 = st.columns(2)
            with f_dt1:
                dt_inicio_filtro = st.date_input("Data Inicial", value=date(2020, 1, 1), format="DD/MM/YYYY")
            with f_dt2:
                dt_fim_filtro = st.date_input("Data Final", value=date.today(), format="DD/MM/YYYY")

        df_r_filtrado = df_riscos_base.copy()

        if not df_r_filtrado.empty:
            if filtro_unid != "Todas":
                df_r_filtrado = df_r_filtrado[df_r_filtrado["unidade"] == filtro_unid]
            if filtro_oe != "Todos":
                df_r_filtrado = df_r_filtrado[df_r_filtrado["objetivo_estrategico"] == filtro_oe]
            if filtro_cat != "Todas":
                df_r_filtrado = df_r_filtrado[df_r_filtrado["nome_categoria"] == filtro_cat]
            if filtro_st != "Todos":
                df_r_filtrado = df_r_filtrado[df_r_filtrado["situacao_status"] == filtro_st]
            
            if filtro_nivel == "🔴 Crítico (≥ 15)":
                df_r_filtrado = df_r_filtrado[df_r_filtrado["nivel_risco"] >= 15]
            elif filtro_nivel == "🟡 Médio (8 - 14)":
                df_r_filtrado = df_r_filtrado[(df_r_filtrado["nivel_risco"] >= 8) & (df_r_filtrado["nivel_risco"] < 15)]
            elif filtro_nivel == "🟢 Baixo (1 - 7)":
                df_r_filtrado = df_r_filtrado[df_r_filtrado["nivel_risco"] < 8]

            if "data_identificacao" in df_r_filtrado.columns:
                df_r_filtrado["dt_ident_conv"] = pd.to_datetime(df_r_filtrado["data_identificacao"], errors='coerce').dt.date
                df_r_filtrado = df_r_filtrado[
                    (df_r_filtrado["dt_ident_conv"].isna()) | 
                    ((df_r_filtrado["dt_ident_conv"] >= dt_inicio_filtro) & (df_r_filtrado["dt_ident_conv"] <= dt_fim_filtro))
                ]

        ids_riscos_filtrados = df_r_filtrado["id"].tolist() if not df_r_filtrado.empty else []
        df_a_filtrado = df_acoes_base[df_acoes_base["risco_id"].isin(ids_riscos_filtrados)].copy() if not df_acoes_base.empty else pd.DataFrame()

        st.divider()

        tot_riscos_f = len(df_r_filtrado)
        criticos_f = sum(1 for _, r in df_r_filtrado.iterrows() if r.get("nivel_risco", 0) >= 15) if not df_r_filtrado.empty else 0
        exposicao_agregada_tot = df_r_filtrado["nivel_risco"].sum() if not df_r_filtrado.empty else 0

        riscos_com_acao = df_a_filtrado["risco_id"].unique() if not df_a_filtrado.empty else []
        riscos_sem_tratamento = sum(1 for r_id in ids_riscos_filtrados if r_id not in riscos_com_acao)

        if not df_a_filtrado.empty:
            total_acoes_f = len(df_a_filtrado)
            acoes_atrasadas_f = sum(
                1 for _, row in df_a_filtrado.iterrows()
                if calcular_situacao_prazo_acao(row.get("status_acao"), row.get("previsao_data_conclusao")) == "⚠️ Atrasada"
            )
            pct_acoes_atrasadas = round((acoes_atrasadas_f / total_acoes_f) * 100, 1) if total_acoes_f > 0 else 0.0
        else:
            pct_acoes_atrasadas = 0.0

        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
        kpi_col1.metric("Total de Riscos", tot_riscos_f)
        kpi_col2.metric("Riscos Críticos (≥ 15)", criticos_f, delta_color="inverse")
        kpi_col3.metric("Exposição Agregada (∑ Nível)", exposicao_agregada_tot)
        kpi_col4.metric("Riscos sem Tratamento", riscos_sem_tratamento)
        kpi_col5.metric("% Ações Atrasadas", f"{pct_acoes_atrasadas}%")

        st.divider()

        col_matriz, col_graficos = st.columns([1.2, 1.8])

        with col_matriz:
            st.markdown("### 🎲 Matriz de Riscos 5x5 Consolidada")
            st.caption("Distribuição volumétrica de riscos na matriz institucional.")
            renderizar_matriz_risco_5x5_consolidada(df_r_filtrado)

        with col_graficos:
            st.markdown("### 📊 Distribuição Estratégica dos Riscos")
            
            tab_g_cat, tab_g_oe, tab_g_unid = st.tabs(["🏷️ Por Categoria", "🎯 Por Objetivo Estratégico", "🏢 Por Unidade"])

            with tab_g_cat:
                if not df_r_filtrado.empty:
                    df_cat_chart = df_r_filtrado["nome_categoria"].value_counts().reset_index()
                    df_cat_chart.columns = ["Categoria", "Quantidade"]
                    st.bar_chart(df_cat_chart.set_index("Categoria"))
                else:
                    st.info("Sem dados para exibir gráficos.")

            with tab_g_oe:
                if not df_r_filtrado.empty:
                    df_oe_chart = df_r_filtrado["objetivo_estrategico"].fillna("Não Informado").value_counts().reset_index()
                    df_oe_chart.columns = ["Objetivo Estratégico", "Quantidade"]
                    st.bar_chart(df_oe_chart.set_index("Objetivo Estratégico"))
                else:
                    st.info("Sem dados para exibir gráficos.")

            with tab_g_unid:
                if not df_r_filtrado.empty:
                    df_unid_chart = df_r_filtrado["unidade"].value_counts().reset_index()
                    df_unid_chart.columns = ["Unidade", "Quantidade"]
                    st.bar_chart(df_unid_chart.set_index("Unidade"))
                else:
                    st.info("Sem dados para exibir gráficos.")

        st.divider()

        col_top, col_alertas_gl = st.columns([1.8, 1.2])

        with col_top:
            st.markdown("### 🔝 Ranking de Riscos Prioritários")
            st.caption("Ordenado pela Pontuação de Priorização do Risco (nível de exposição, pendências e revisão temporal).")

            if not df_r_filtrado.empty:
                top_riscos_lista = []
        
                for _, r_item in df_r_filtrado.iterrows():
                    r_id_f = r_item["id"]
                    n_val = r_item.get("nivel_risco", 1)
            
                    df_ac_r = df_a_filtrado[df_a_filtrado["risco_id"] == r_id_f] if not df_a_filtrado.empty else pd.DataFrame()
                    tot_ac_r = len(df_ac_r)
                    atrasadas_ac_r = sum(
                        1 for _, row in df_ac_r.iterrows()
                        if calcular_situacao_prazo_acao(row.get("status_acao"), row.get("previsao_data_conclusao")) == "⚠️ Atrasada"
                    ) if not df_a_filtrado.empty else 0

                    sit_rev_r = calcular_situacao_revisao_risco(r_item.get("proxima_revisao"))

                    iar_dados = calcular_iar_risco(
                        nivel_risco=n_val,
                        acoes_atrasadas=atrasadas_ac_r,
                        total_acoes=tot_ac_r,
                        situacao_revisao=sit_rev_r
                    )

                    iar_valor = iar_dados.get("iar") or iar_dados.get("iar_score") or iar_dados.get("score") or 0.0
                    prioridade_txt = iar_dados.get("prioridade") or iar_dados.get("nivel_prioridade") or "Normal"

                    top_riscos_lista.append({
                        "ID": r_id_f,
                        "Risco": r_item.get("evento", "Sem evento"),
                        "Unidade": r_item.get("unidade"),
                        "Nível": n_val,
                        "Ações (Tot/Atr)": f"{tot_ac_r} / {atrasadas_ac_r}",
                        "Pontuação de Prioridade": iar_valor,
                        "Prioridade": prioridade_txt,
                        "Status": r_item.get("situacao_status")
                    })

                df_top_final = pd.DataFrame(top_riscos_lista).sort_values(by="Pontuação de Prioridade", ascending=False)
                st.dataframe(df_top_final, use_container_width=True, hide_index=True)
            else:
                st.info("Nenum risco encontrado para exibição no ranking.")

        with col_alertas_gl:
            st.markdown("### 🚨 Alertas Institucionais")
            
            if not df_r_filtrado.empty:
                df_exp_unidades = calcular_exposicao_agregada(df_r_filtrado, agrupar_por="unidade")
                df_exp_unidades.columns = ["Unidade", "Total Riscos", "Soma Nível Risco", "Média Nível Risco", "Riscos Críticos"]
                
                unidades_criticas = df_exp_unidades[df_exp_unidades["Riscos Críticos"] > 0]
                unidades_alta_exp = df_exp_unidades[df_exp_unidades["Soma Nível Risco"] >= 30]

                if not unidades_criticas.empty:
                    for _, u_row in unidades_criticas.iterrows():
                        st.error(f"🔴 **{u_row['Unidade']}**: Concentra {u_row['Riscos Críticos']} risco(s) crítico(s) (Nível ≥ 15).")
                
                if not unidades_alta_exp.empty:
                    for _, u_row in unidades_alta_exp.iterrows():
                        st.warning(f"⚠️ **{u_row['Unidade']}**: Alta Exposição Agregada totalizando ∑ {u_row['Soma Nível Risco']} pontos.")

                if pct_acoes_atrasadas > 25.0:
                    st.error(f"⏰ **Alerta Global de Prazos**: {pct_acoes_atrasadas}% do plano de tratamento global está atrasado.")

                if unidades_criticas.empty and unidades_alta_exp.empty and pct_acoes_atrasadas <= 25.0:
                    st.success("✅ **Governança Estável**: Nenhuma alta concentração crítica de risco detectada no momento.")
            else:
                st.info("Sem dados suficientes para gerar alertas institucionais.")

# ---------------------------------------------------------
# PÁGINA: BIBLIOTECA
# ---------------------------------------------------------
elif st.session_state.pagina_atual == "Biblioteca":
    st.title("📄 Documentos e Normativas")
    st.caption("Acervo de normativas, manuais, diretrizes e documentos institucionais de gestão de riscos.")
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
