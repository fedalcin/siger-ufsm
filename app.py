# ---------------------------------------------------------
# MENU LATERAL - SUB-EXPANDER CADASTROS
# ---------------------------------------------------------
with st.sidebar.expander("📝 Cadastros", expanded=False):
    if st.button("🏢 Unidades", key="btn_cad_unid", use_container_width=True):
        navegar_para("Cadastros", "Unidades")
    if st.button("🎯 Objetivos Estratégicos", key="btn_cad_oe", use_container_width=True):
        navegar_para("Cadastros", "Objetivos Estratégicos")
    if st.button("🏷️ Categorias de Risco", key="btn_cad_cat", use_container_width=True):
        navegar_para("Cadastros", "Categorias de Risco")
    if st.button("📋 Riscos", key="btn_cad_risco", use_container_width=True):
        navegar_para("Cadastros", "Riscos")
    if st.button("💥 Eventos de Risco", key="btn_cad_evento", use_container_width=True):
        navegar_para("Cadastros", "Evento")
    if st.button("📝 Descrições de Risco", key="btn_cad_desc", use_container_width=True):
        navegar_para("Cadastros", "Descrição do Risco")
    if st.button("🔍 Causas", key="btn_cad_causa", use_container_width=True):
        navegar_para("Cadastros", "Causa")
    if st.button("⚠️ Consequências", key="btn_cad_cons", use_container_width=True):
        navegar_para("Cadastros", "Consequência")
    if st.button("🎲 Probabilidade", key="btn_cad_prob", use_container_width=True):
        navegar_para("Cadastros", "Probabilidade")
    if st.button("💥 Impacto", key="btn_cad_imp", use_container_width=True):
        navegar_para("Cadastros", "Impacto")
    if st.button("🖼️ Identidade Visual", key="btn_cad_id_vis", use_container_width=True):
        navegar_para("Cadastros", "Identidade Visual")
    if st.button("📚 Documentos da Biblioteca", key="btn_cad_doc_bib", use_container_width=True):
        navegar_para("Cadastros", "Documentos da Biblioteca")
    if st.button("✍️ Texto da Tela Inicial", key="btn_cad_txt", use_container_width=True):
        navegar_para("Cadastros", "Texto da Tela Inicial")
