from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timezone, timedelta

# =============================================================================
# 1. CALCULADORAS OPERACIONAIS DE PRAZOS E ALERTAS
# =============================================================================

def calcular_situacao_revisao_risco(data_proxima_revisao, dias_alerta: int = 30) -> str:
    """
    Verifica a situação da revisão temporal do risco.
    Retorna: 'Atrasada', 'Próxima do Vencimento', 'Em dia' ou 'Não definida'
    """
    if pd.isna(data_proxima_revisao) or data_proxima_revisao is None:
        return 'Não definida'
    
    if isinstance(data_proxima_revisao, str):
        data_proxima_revisao = datetime.strptime(data_proxima_revisao, '%Y-%m-%d').date()
    elif isinstance(data_proxima_revisao, datetime):
        data_proxima_revisao = data_proxima_revisao.date()

    hoje = date.today()
    if data_proxima_revisao < hoje:
        return 'Atrasada'
    elif hoje <= data_proxima_revisao <= hoje + timedelta(days=dias_alerta):
        return 'Próxima do Vencimento'
    else:
        return 'Em dia'


def calcular_situacao_prazo_acao(
    status_acao: str, 
    previsao_data_conclusao, 
    dias_alerta: int = 15
) -> str:
    """
    Verifica a situação do prazo de uma ação de tratamento.
    Retorna: 'Concluída', '⚠️ Atrasada', 'Próxima do Vencimento', 'No Prazo' ou 'Cancelada/Devolvida'
    """
    if status_acao == 'Concluída':
        return 'Concluída'
    if status_acao in ['Cancelada', 'Devolvida']:
        return status_acao

    if pd.isna(previsao_data_conclusao) or previsao_data_conclusao is None:
        return 'No Prazo'

    if isinstance(previsao_data_conclusao, str):
        previsao_data_conclusao = datetime.strptime(previsao_data_conclusao, '%Y-%m-%d').date()
    elif isinstance(previsao_data_conclusao, datetime):
        previsao_data_conclusao = previsao_data_conclusao.date()

    hoje = date.today()
    if previsao_data_conclusao < hoje:
        return '⚠️ Atrasada'
    elif hoje <= previsao_data_conclusao <= hoje + timedelta(days=dias_alerta):
        return 'Próxima do Vencimento'
    else:
        return 'No Prazo'


# =============================================================================
# 2. CÁLCULO DOS INDICADORES GERENCIAIS
# =============================================================================

def calcular_iet(df_acoes: pd.DataFrame) -> float:
    """
    IET - Índice de Execução do Tratamento
    Média aritmética do percentual de execução das ações ativas.
    """
    if df_acoes.empty:
        return 0.0

    # Ajustado 'status' -> 'status_acao'
    col_status = 'status_acao' if 'status_acao' in df_acoes.columns else 'status'
    df_validas = df_acoes[df_acoes[col_status] != 'Cancelada'] if col_status in df_acoes.columns else df_acoes
    
    if df_validas.empty:
        return 0.0

    # Ajustado 'percentual_execucao' -> 'percentual_conclusao'
    col_exec = 'percentual_conclusao' if 'percentual_conclusao' in df_validas.columns else 'percentual_execucao'
    
    if col_exec not in df_validas.columns:
        return 0.0

    return round(float(df_validas[col_exec].fillna(0).mean()), 2)

def calcular_icp(df_acoes: pd.DataFrame) -> float:
    """
    ICP - Índice de Cumprimento de Prazo
    Fórmula: (Concluídas no Prazo / Total Concluídas) * 100
    """
    if df_acoes.empty:
        return 100.0  # Sem ações concluídas assume 100% de conformidade padrão

    df_concluidas = df_acoes[df_acoes['status'] == 'Concluída'] if 'status' in df_acoes.columns else df_acoes
    
    total_concluidas = len(df_concluidas)
    if total_concluidas == 0:
        return 100.0  # Evita divisão por zero se nenhuma ação foi concluída ainda

    if 'concluida_no_prazo' in df_concluidas.columns:
        concluidas_no_prazo = df_concluidas['concluida_no_prazo'].sum()
    else:
        # Fallback de verificação comparando data_conclusao_efetiva vs previsao_conclusao
        def no_prazo(row):
            efetiva = row.get('data_conclusao_efetiva')
            prevista = row.get('previsao_conclusao')
            if pd.isna(efetiva) or efetiva is None:
                return True
            return efetiva <= prevista

        concluidas_no_prazo = df_concluidas.apply(no_prazo, axis=1).sum()

    return round(float((concluidas_no_prazo / total_concluidas) * 100), 2)


def calcular_itr(iet: float, percentual_concluidas: float, icp: float) -> float:
    """
    ITR - Índice de Tratamento do Risco
    Composição ponderada: (IET * 0.40) + (% Concluídas * 0.30) + (ICP * 0.30)
    """
    itr = (iet * 0.40) + (percentual_concluidas * 0.30) + (icp * 0.30)
    return round(float(itr), 2)


def calcular_iar_risco(
    nivel_risco: int,
    acoes_atrasadas: int,
    total_acoes: int,
    situacao_revisao: str
) -> dict:
    """
    IAR - Índice de Atenção ao Risco (0 a 100)
    A pontuação de prioridade gerencial avalia:
    - Criticidade intrínseca (nível do risco: 1 a 25) -> Peso de até 40 pts
    - Ações atrasadas -> Peso de até 40 pts
    - Revisão de risco atrasada -> Peso de até 20 pts
    """
    # 1. Componente Nível de Risco (0 - 40 pts)
    # Nível de risco varia de 1 a 25 -> Proporcional para até 40
    score_nivel = (min(max(nivel_risco, 1), 25) / 25) * 40

    # 2. Componente Ações Atrasadas (0 - 40 pts)
    if total_acoes > 0:
        prop_atraso = min(acoes_atrasadas / total_acoes, 1.0)
        score_atraso = prop_atraso * 40
    else:
        score_atraso = 0.0

    # 3. Componente Revisão PENDENTE/ATRASADA (0 - 20 pts)
    if situacao_revisao == 'Atrasada':
        score_revisao = 20.0
    elif situacao_revisao == 'Próxima do Vencimento':
        score_revisao = 10.0
    else:
        score_revisao = 0.0

    iar_total = round(score_nivel + score_atraso + score_revisao, 2)

    # Nível de Alerta
    if iar_total >= 70:
        classificacao = '🔴 CRÍTICO'
    elif iar_total >= 40:
        classificacao = '🟠 ALTO'
    elif iar_total >= 20:
        classificacao = '🟡 MÉDIO'
    else:
        classificacao = '🟢 BAIXO'

    return {
        'iar_score': iar_total,
        'classificacao': classificacao
    }


# =============================================================================
# 3. EXPOSIÇÃO OPERACIONAL AGREGADA
# =============================================================================

def calcular_exposicao_agregada(
    df_riscos: pd.DataFrame, 
    agrupar_por: str = 'unidade'
) -> pd.DataFrame:
    """
    Calcula a Exposição Operacional Agregada agrupada por Unidade ou Objetivo Estratégico.
    """
    if df_riscos.empty:
        return pd.DataFrame()

    campo_agrupador = agrupar_por if agrupar_por in df_riscos.columns else 'unidade'
    id_col = 'id' if 'id' in df_riscos.columns else 'risco_id'

    df_agrupado = df_riscos.groupby(campo_agrupador).agg(
        total_riscos=(id_col, 'count'),
        soma_nivel_risco=('nivel_risco', 'sum'),
        media_nivel_risco=('nivel_risco', 'mean'),
        riscos_criticos=('nivel_risco', lambda x: (x >= 15).sum())
    ).reset_index()

    df_agrupado['media_nivel_risco'] = df_agrupado['media_nivel_risco'].round(2)
    df_agrupado = df_agrupado.sort_values(by='soma_nivel_risco', ascending=False)

    return df_agrupado


# ============================================================
# 4. DIAGNÓSTICO DE CONTRATOS DO PNCP - UFSM
#    Análise de continuidade contratual por fornecedor
# ============================================================

def buscar_dados_contratos_ufsm_comprasgov():

    import requests
    import streamlit as st
    import time
    import re
    from datetime import datetime, timedelta

    URL = "https://pncp.gov.br/api/consulta/v1/contratos"
    CNPJ_UFSM = "95591764000105"

    DATA_INICIAL = datetime(2020, 1, 1).date()
    DATA_FINAL = datetime.now().date()

    TAMANHO_PAGINA = 500

    todos_registros = []
    todos_contratos = []

    total_paginas_consultadas = 0

    # --------------------------------------------------------
    # Funções auxiliares
    # --------------------------------------------------------

    def normalizar_cnpj(valor):
        if valor is None:
            return ""
        return re.sub(r"\D", "", str(valor))

    def converter_data(valor):
        if not valor:
            return None

        try:
            return datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def formatar_data(valor):
        if not valor:
            return "Não informado"

        data = converter_data(valor)

        if data:
            return data.strftime("%d/%m/%Y")

        return str(valor)

    def formatar_valor(valor):
        try:
            valor = float(valor or 0)
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "Não informado"

    def consultar_pagina(parametros, periodo, pagina):

        max_tentativas = 5

        for tentativa in range(1, max_tentativas + 1):

            try:
                resposta = requests.get(
                    URL,
                    params=parametros,
                    timeout=120
                )

                # Sem registros para o período
                if resposta.status_code == 204:
                    return None

                # Sucesso
                if resposta.status_code == 200:
                    time.sleep(2)
                    return resposta.json()

                # Erros temporários: limite de requisições ou falha interna
                if resposta.status_code in [429, 500, 502, 503, 504]:

                    espera = tentativa * 10

                    st.warning(
                        f"Instabilidade no PNCP: HTTP {resposta.status_code}. "
                        f"Período {periodo}, página {pagina}. "
                        f"Tentativa {tentativa}/{max_tentativas}. "
                        f"Nova tentativa em {espera} segundos."
                    )

                    if tentativa < max_tentativas:
                        time.sleep(espera)
                        continue

                resposta.raise_for_status()

            except requests.exceptions.RequestException as erro:

                if tentativa < max_tentativas:
                    time.sleep(tentativa * 10)
                    continue

                raise Exception(
                    f"Falha na consulta do período {periodo}, "
                    f"página {pagina}: {erro}"
                )

        raise Exception(
            f"Não foi possível consultar o período {periodo}, "
            f"página {pagina}, após {max_tentativas} tentativas."
        )

    # --------------------------------------------------------
    # 1. Consulta ao PNCP em períodos de até 365 dias
    # --------------------------------------------------------

    data_inicio = DATA_INICIAL

    while data_inicio <= DATA_FINAL:

        data_fim = min(
            data_inicio + timedelta(days=364),
            DATA_FINAL
        )

        periodo = (
            f"{data_inicio.strftime('%d/%m/%Y')} a "
            f"{data_fim.strftime('%d/%m/%Y')}"
        )

        st.write(f"Consultando período: {periodo}")

        pagina = 1

        while True:

            parametros = {
                "dataInicial": data_inicio.strftime("%Y%m%d"),
                "dataFinal": data_fim.strftime("%Y%m%d"),
                "cnpjOrgao": CNPJ_UFSM,
                "pagina": pagina,
                "tamanhoPagina": TAMANHO_PAGINA
            }

            resultado = consultar_pagina(
                parametros,
                periodo,
                pagina
            )

            if resultado is None:
                break

            registros = resultado.get("data", [])

            if not registros:
                break

            todos_registros.extend(registros)
            total_paginas_consultadas += 1

            # Guarda somente os registros classificados como contrato
            for registro in registros:

                tipo_contrato = (
                    registro.get("tipoContrato", {}).get("nome", "")
                )

                if "contrato" in tipo_contrato.lower():

                    todos_contratos.append(registro)

            total_paginas = resultado.get("totalPaginas", 1)

            if pagina >= total_paginas:
                break

            pagina += 1

        data_inicio = data_fim + timedelta(days=1)

    # --------------------------------------------------------
    # 2. Diagnóstico geral dos registros
    # --------------------------------------------------------

    st.divider()

    st.subheader("Diagnóstico dos registros do PNCP - UFSM")

    st.write(
        f"**Período consultado:** "
        f"{DATA_INICIAL.strftime('%d/%m/%Y')} a "
        f"{DATA_FINAL.strftime('%d/%m/%Y')}"
    )

    st.write(
        f"**Total de registros consultados:** "
        f"{len(todos_registros)}"
    )

    st.write(
        f"**Total de páginas percorridas:** "
        f"{total_paginas_consultadas}"
    )

    # Quantidade por tipo de instrumento
    contagem_tipos = {}

    for registro in todos_registros:

        tipo = (
            registro.get("tipoContrato", {}).get("nome")
            or "Não informado"
        )

        contagem_tipos[tipo] = contagem_tipos.get(tipo, 0) + 1

    st.markdown("### Quantidade por tipo de instrumento")

    for tipo, quantidade in sorted(contagem_tipos.items()):

        st.write(f"**{tipo}:** {quantidade} registros")

    st.write(
        f"**Total de registros classificados como contrato:** "
        f"{len(todos_contratos)}"
    )

    # --------------------------------------------------------
    # 3. Preparação dos contratos para análise
    # --------------------------------------------------------

    contratos_por_fornecedor = {}

    for contrato in todos_contratos:

        cnpj = normalizar_cnpj(
            contrato.get("niFornecedor")
        )

        if not cnpj:
            continue

        inicio = converter_data(
            contrato.get("dataVigenciaInicio")
        )

        fim = converter_data(
            contrato.get("dataVigenciaFim")
        )

        if not inicio or not fim:
            continue

        contrato_tratado = {
            "cnpj": cnpj,
            "fornecedor": contrato.get(
                "nomeRazaoSocialFornecedor",
                "Não informado"
            ),
            "numero_contrato": contrato.get(
                "numeroContratoEmpenho",
                "Não informado"
            ),
            "numero_controle_pncp": contrato.get(
                "numeroControlePNCP",
                "Não informado"
            ),
            "numero_controle_compra": contrato.get(
                "numeroControlePncpCompra",
                "Não informado"
            ),
            "processo": contrato.get(
                "processo",
                "Não informado"
            ),
            "objeto": contrato.get(
                "objetoContrato",
                "Não informado"
            ),
            "inicio": inicio,
            "fim": fim,
            "valor_inicial": contrato.get("valorInicial"),
            "valor_global": contrato.get("valorGlobal"),
            "tipo": contrato.get(
                "tipoContrato", {}
            ).get("nome", "Não informado"),
            "registro_original": contrato
        }

        contratos_por_fornecedor.setdefault(
            cnpj, []
        ).append(contrato_tratado)

    # --------------------------------------------------------
    # 4. Análise de continuidade entre contratos
    # --------------------------------------------------------

    pares_continuidade = []

    for cnpj, contratos in contratos_por_fornecedor.items():

        # Ordena os contratos pela data de início da vigência
        contratos.sort(key=lambda x: x["inicio"])

        # Compara cada contrato com os posteriores do mesmo fornecedor
        for i, contrato_anterior in enumerate(contratos):

            for contrato_posterior in contratos[i + 1:]:

                intervalo = (
                    contrato_posterior["inicio"]
                    - contrato_anterior["fim"]
                ).days

                # Como os contratos estão ordenados por início,
                # se o intervalo superar 5 dias, os seguintes
                # também não serão considerados.
                if intervalo > 5:
                    break

                # Considera continuidade de 0 a 5 dias
                if 0 <= intervalo <= 5:

                    pares_continuidade.append({
                        "intervalo": intervalo,
                        "cnpj": cnpj,
                        "fornecedor": contrato_anterior["fornecedor"],

                        "anterior_numero": contrato_anterior["numero_contrato"],
                        "anterior_processo": contrato_anterior["processo"],
                        "anterior_objeto": contrato_anterior["objeto"],
                        "anterior_inicio": contrato_anterior["inicio"],
                        "anterior_fim": contrato_anterior["fim"],
                        "anterior_valor_global": contrato_anterior["valor_global"],
                        "anterior_controle_pncp": contrato_anterior["numero_controle_pncp"],

                        "posterior_numero": contrato_posterior["numero_contrato"],
                        "posterior_processo": contrato_posterior["processo"],
                        "posterior_objeto": contrato_posterior["objeto"],
                        "posterior_inicio": contrato_posterior["inicio"],
                        "posterior_fim": contrato_posterior["fim"],
                        "posterior_valor_global": contrato_posterior["valor_global"],
                        "posterior_controle_pncp": contrato_posterior["numero_controle_pncp"],

                        "contrato_anterior": contrato_anterior,
                        "contrato_posterior": contrato_posterior
                    })

    # Ordena os pares pelo intervalo de continuidade
    pares_continuidade.sort(
        key=lambda x: (
            x["intervalo"],
            x["cnpj"],
            x["anterior_inicio"]
        )
    )

    # --------------------------------------------------------
    # 5. Apresentação dos resultados da continuidade
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "Investigação de continuidade contratual por fornecedor"
    )

    st.write(
        "Foram comparados os contratos de um mesmo fornecedor, "
        "considerando a diferença entre a data final da vigência "
        "de um contrato e a data inicial da vigência do contrato seguinte."
    )

    st.write(
        "**Critério utilizado:** mesmo CNPJ de fornecedor e intervalo "
        "entre 0 e 5 dias entre o encerramento e o início das vigências."
    )

    st.markdown("### Resumo dos intervalos encontrados")

    contagem_intervalos = {
        intervalo: 0 for intervalo in range(6)
    }

    for par in pares_continuidade:
        contagem_intervalos[par["intervalo"]] += 1

    colunas = st.columns(6)

    for i, intervalo in enumerate(range(6)):

        with colunas[i]:
            st.metric(
                label=f"{intervalo} dia(s)",
                value=contagem_intervalos[intervalo]
            )

    st.metric(
        "Total de pares com continuidade identificada",
        len(pares_continuidade)
    )

    # --------------------------------------------------------
    # 6. Exibição detalhada dos pares encontrados
    # --------------------------------------------------------

    st.markdown("### Detalhamento dos contratos identificados")

    if not pares_continuidade:

        st.info(
            "Nenhum par de contratos do mesmo fornecedor foi encontrado "
            "com intervalo entre 0 e 5 dias entre as vigências."
        )

    else:

        for numero, par in enumerate(pares_continuidade, start=1):

            st.markdown(
                f"#### Ocorrência {numero} — "
                f"Intervalo de {par['intervalo']} dia(s)"
            )

            st.write(
                f"**Fornecedor:** {par['fornecedor']}"
            )

            st.write(
                f"**CNPJ:** {par['cnpj']}"
            )

            col_anterior, col_posterior = st.columns(2)

            with col_anterior:

                st.markdown("**CONTRATO ANTERIOR**")

                st.write(
                    f"**Número:** {par['anterior_numero']}"
                )

                st.write(
                    f"**Processo:** {par['anterior_processo']}"
                )

                st.write(
                    f"**Início:** {formatar_data(par['anterior_inicio'])}"
                )

                st.write(
                    f"**Fim:** {formatar_data(par['anterior_fim'])}"
                )

                st.write(
                    f"**Valor global:** "
                    f"{formatar_valor(par['anterior_valor_global'])}"
                )

                st.write(
                    f"**Objeto:** {par['anterior_objeto']}"
                )

                st.caption(
                    f"Controle PNCP: {par['anterior_controle_pncp']}"
                )

            with col_posterior:

                st.markdown("**CONTRATO SEGUINTE**")

                st.write(
                    f"**Número:** {par['posterior_numero']}"
                )

                st.write(
                    f"**Processo:** {par['posterior_processo']}"
                )

                st.write(
                    f"**Início:** {formatar_data(par['posterior_inicio'])}"
                )

                st.write(
                    f"**Fim:** {formatar_data(par['posterior_fim'])}"
                )

                st.write(
                    f"**Valor global:** "
                    f"{formatar_valor(par['posterior_valor_global'])}"
                )

                st.write(
                    f"**Objeto:** {par['posterior_objeto']}"
                )

                st.caption(
                    f"Controle PNCP: {par['posterior_controle_pncp']}"
                )

            # Exibe os registros originais para permitir conferência
            with st.expander(
                f"Consultar dados originais do PNCP — Ocorrência {numero}"
            ):

                st.markdown("**Registro original do contrato anterior**")

                st.json(
                    par["contrato_anterior"]["registro_original"]
                )

                st.markdown("**Registro original do contrato seguinte**")

                st.json(
                    par["contrato_posterior"]["registro_original"]
                )

            st.divider()

    # --------------------------------------------------------
    # 7. Tabela consolidada para facilitar a análise
    # --------------------------------------------------------

    if pares_continuidade:

        st.markdown("### Tabela consolidada dos pares encontrados")

        import pandas as pd

        dados_tabela = []

        for par in pares_continuidade:

            dados_tabela.append({
                "Intervalo (dias)": par["intervalo"],
                "CNPJ": par["cnpj"],
                "Fornecedor": par["fornecedor"],
                "Contrato anterior": par["anterior_numero"],
                "Processo anterior": par["anterior_processo"],
                "Início anterior": formatar_data(par["anterior_inicio"]),
                "Fim anterior": formatar_data(par["anterior_fim"]),
                "Contrato seguinte": par["posterior_numero"],
                "Processo seguinte": par["posterior_processo"],
                "Início seguinte": formatar_data(par["posterior_inicio"]),
                "Fim seguinte": formatar_data(par["posterior_fim"]),
                "Objeto anterior": par["anterior_objeto"],
                "Objeto seguinte": par["posterior_objeto"],
                "Valor global anterior": formatar_valor(
                    par["anterior_valor_global"]
                ),
                "Valor global seguinte": formatar_valor(
                    par["posterior_valor_global"]
                )
            })

        df_continuidade = pd.DataFrame(dados_tabela)

        st.dataframe(
            df_continuidade,
            use_container_width=True,
            hide_index=True
        )

        # Permite baixar os resultados para análise posterior
        csv = df_continuidade.to_csv(
            index=False,
            sep=";",
            encoding="utf-8-sig"
        )

        st.download_button(
            label="Baixar análise de continuidade em CSV",
            data=csv,
            file_name="analise_continuidade_contratos_pncp_ufsm.csv",
            mime="text/csv"
        )

    # --------------------------------------------------------
    # 8. Conclusão do diagnóstico
    # --------------------------------------------------------

    mensagem = (
        f"Diagnóstico concluído. Foram consultados "
        f"{len(todos_registros)} registros do PNCP, dos quais "
        f"{len(todos_contratos)} foram classificados como contratos. "
        f"Foram identificados {len(pares_continuidade)} pares de contratos "
        f"do mesmo fornecedor com intervalo de 0 a 5 dias entre as vigências."
    )

    st.success(mensagem)

    return True, "TESTE", mensagem, []
