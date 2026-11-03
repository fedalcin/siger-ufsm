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



# =============================================================================
# 4. INTEGRAÇÕES EXTERNAS E BUSCA DE DADOS (KRI)
# =============================================================================

def buscar_dados_contratos_ufsm_comprasgov():
    """
    Consulta os registros da UFSM no PNCP desde 01/01/2020.
    Divide a consulta em períodos de até 365 dias.
    Identifica todos os tipos de instrumentos.
    Identifica contratos com vigência superior a cinco anos.
    Analisa a continuidade contratual por CNPJ do fornecedor.
    Não grava dados no Supabase.
    """
    from datetime import datetime, timedelta, timezone
    import requests
    import streamlit as st
    import time

    fuso_br = timezone(timedelta(hours=-3))
    hoje = datetime.now(fuso_br).date()

    cnpj_ufsm = "95591764000105"
    url = "https://pncp.gov.br/api/consulta/v1/contratos"

    headers = {
        "accept": "application/json",
        "User-Agent": "SIGER-UFSM/1.0"
    }

    # Armazena a quantidade de registros por tipo
    contagem_tipos = {}

    # Armazena contratos com vigência superior a cinco anos
    contratos_longo_prazo = []

    # Armazena todos os contratos para análise de continuidade
    todos_contratos = []

    total_registros = 0
    total_paginas_consultadas = 0

    # Divide o período em intervalos de até 365 dias
    data_inicio = datetime(2020, 1, 1).date()

    try:
        while data_inicio <= hoje:

            data_fim = min(
                data_inicio + timedelta(days=364),
                hoje
            )

            data_inicial = data_inicio.strftime("%Y%m%d")
            data_final = data_fim.strftime("%Y%m%d")

            pagina = 1
            total_paginas = 1

            st.write(
                f"Consultando período: "
                f"{data_inicio.strftime('%d/%m/%Y')} a "
                f"{data_fim.strftime('%d/%m/%Y')}"
            )

            while pagina <= total_paginas:

                parametros = {
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "cnpjOrgao": cnpj_ufsm,
                    "pagina": pagina,
                    "tamanhoPagina": 500
                }

                # Faz a requisição com tratamento de limite de acesso do PNCP
                response = None

                for tentativa in range(5):

                    response = requests.get(
                        url,
                        params=parametros,
                        headers=headers,
                        timeout=60
                    )

                    if response.status_code != 429:
                        break

                    tempo_espera = 15 * (tentativa + 1)

                    st.warning(
                        f"Limite de requisições do PNCP atingido. "
                        f"Aguardando {tempo_espera} segundos "
                        f"(tentativa {tentativa + 1} de 5)."
                    )

                    time.sleep(tempo_espera)

                if response is not None and response.status_code == 429:
                    return (
                        False,
                        "",
                        f"O PNCP manteve o bloqueio após cinco tentativas. "
                        f"Período: {data_inicial} a {data_final}, "
                        f"página {pagina}. Tente novamente mais tarde.",
                        []
                    )

                # Pequeno intervalo entre consultas
                time.sleep(2)

                # Se não houver registros no período, segue adiante
                if response.status_code == 204:
                    break

                if response.status_code != 200:
                    return (
                        False,
                        "",
                        f"Erro HTTP {response.status_code} no período "
                        f"{data_inicial} a {data_final}, página {pagina}: "
                        f"{response.text[:1000]}",
                        []
                    )

                dados = response.json()
                itens = dados.get("data", [])

                if not isinstance(itens, list):
                    return (
                        False,
                        "",
                        "Formato inesperado de resposta do PNCP.",
                        []
                    )

                total_paginas = int(dados.get("totalPaginas", 1) or 1)
                total_paginas_consultadas += 1

                # Examina todos os registros da página
                for item in itens:

                    tipo = item.get("tipoContrato") or {}

                    if isinstance(tipo, dict):
                        nome_tipo = tipo.get("nome", "Não informado")
                    else:
                        nome_tipo = str(tipo)

                    nome_tipo = nome_tipo.strip() or "Não informado"

                    contagem_tipos[nome_tipo] = (
                        contagem_tipos.get(nome_tipo, 0) + 1
                    )

                    total_registros += 1

                    # Considera registros classificados como contrato
                    if nome_tipo.lower().startswith("contrato"):

                        # Armazena todos os contratos para análise posterior
                        todos_contratos.append(item)

                        data_inicio_contrato = item.get(
                            "dataVigenciaInicio"
                        )
                        data_fim_contrato = item.get(
                            "dataVigenciaFim"
                        )

                        # Identifica contratos com vigência superior a cinco anos
                        if data_inicio_contrato and data_fim_contrato:

                            try:
                                inicio = datetime.strptime(
                                    data_inicio_contrato[:10],
                                    "%Y-%m-%d"
                                ).date()

                                fim = datetime.strptime(
                                    data_fim_contrato[:10],
                                    "%Y-%m-%d"
                                ).date()

                                prazo_dias = (fim - inicio).days

                                if prazo_dias > 1826:

                                    contratos_longo_prazo.append({
                                        "prazo_anos": round(
                                            prazo_dias / 365.25, 2
                                        ),
                                        "dados_completos": item
                                    })

                            except (ValueError, TypeError):
                                pass

                pagina += 1

            # Avança para o próximo período
            data_inicio = data_fim + timedelta(days=1)

        # =============================================================
        # DIAGNÓSTICO GERAL
        # =============================================================

        st.subheader("Diagnóstico dos registros do PNCP - UFSM")

        st.write(
            f"**Período consultado:** 01/01/2020 a "
            f"{hoje.strftime('%d/%m/%Y')}"
        )

        st.write(
            f"**Total de registros consultados:** {total_registros}"
        )

        st.write(
            f"**Total de páginas percorridas:** "
            f"{total_paginas_consultadas}"
        )

        st.divider()

        st.subheader("Quantidade por tipo de instrumento")

        for nome_tipo, quantidade in sorted(
            contagem_tipos.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            st.write(f"**{nome_tipo}:** {quantidade} registros")

        # =============================================================
        # CONTRATOS COM MAIS DE CINCO ANOS
        # =============================================================

        st.divider()

        st.subheader("Contratos com vigência superior a cinco anos")

        contratos_longo_prazo.sort(
            key=lambda x: x["prazo_anos"],
            reverse=True
        )

        st.write(
            f"**Contratos encontrados com vigência superior a cinco anos: "
            f"{len(contratos_longo_prazo)}**"
        )

        if contratos_longo_prazo:

            for contrato in contratos_longo_prazo:

                item = contrato["dados_completos"]

                valor_inicial = item.get("valorInicial")
                valor_global = item.get("valorGlobal")

                with st.expander(
                    f"Contrato "
                    f"{item.get('numeroContratoEmpenho', 'Não informado')} "
                    f"— {contrato['prazo_anos']} anos"
                ):

                    st.write(
                        f"**Fornecedor:** "
                        f"{item.get('nomeRazaoSocialFornecedor')}"
                    )

                    st.write(
                        f"**CNPJ:** {item.get('niFornecedor')}"
                    )

                    st.write(
                        f"**Objeto:** {item.get('objetoContrato')}"
                    )

                    st.write(
                        f"**Processo:** {item.get('processo')}"
                    )

                    st.write(
                        f"**Início da vigência:** "
                        f"{item.get('dataVigenciaInicio')}"
                    )

                    st.write(
                        f"**Fim da vigência:** "
                        f"{item.get('dataVigenciaFim')}"
                    )

                    if valor_inicial is not None:
                        st.write(
                            f"**Valor inicial:** R$ {valor_inicial:,.2f}"
                        )
                    else:
                        st.write("**Valor inicial:** Não informado")

                    if valor_global is not None:
                        st.write(
                            f"**Valor global:** R$ {valor_global:,.2f}"
                        )
                    else:
                        st.write("**Valor global:** Não informado")

                    st.write(
                        f"**Última atualização:** "
                        f"{item.get('dataAtualizacaoGlobal')}"
                    )

                    st.markdown("**Registro completo no PNCP:**")
                    st.json(item)

        else:
            st.info(
                "Nenhum contrato com vigência superior a cinco anos "
                "foi encontrado."
            )

        # =============================================================
        # ANÁLISE DE CONTINUIDADE CONTRATUAL POR FORNECEDOR
        # =============================================================

        st.divider()

        st.subheader(
            "Análise de continuidade contratual por fornecedor"
        )

        # Organiza os contratos por CNPJ do fornecedor
        contratos_por_fornecedor = {}

        for item in todos_contratos:

            cnpj = item.get("niFornecedor")

            data_inicio_contrato = item.get("dataVigenciaInicio")
            data_fim_contrato = item.get("dataVigenciaFim")

            if not cnpj or not data_inicio_contrato or not data_fim_contrato:
                continue

            # Padroniza o CNPJ para evitar diferenças de formatação
            cnpj = "".join(
                caractere for caractere in str(cnpj)
                if caractere.isdigit()
            )

            try:
                inicio = datetime.strptime(
                    data_inicio_contrato[:10],
                    "%Y-%m-%d"
                ).date()

                fim = datetime.strptime(
                    data_fim_contrato[:10],
                    "%Y-%m-%d"
                ).date()

                if cnpj not in contratos_por_fornecedor:
                    contratos_por_fornecedor[cnpj] = []

                contratos_por_fornecedor[cnpj].append({
                    "inicio": inicio,
                    "fim": fim,
                    "dados": item
                })

            except (ValueError, TypeError):
                continue

        # Compara contratos do mesmo fornecedor
        continuidades = []

        for cnpj, contratos in contratos_por_fornecedor.items():

            contratos.sort(key=lambda x: x["inicio"])

            for i in range(len(contratos)):

                anterior = contratos[i]

                for j in range(i + 1, len(contratos)):

                    posterior = contratos[j]

                    intervalo = (
                        posterior["inicio"] - anterior["fim"]
                    ).days

                    # Considera contratos com intervalo de zero a cinco dias
                    if 0 <= intervalo <= 5:

                        continuidades.append({
                            "cnpj": cnpj,
                            "intervalo": intervalo,
                            "contrato_anterior": anterior["dados"],
                            "contrato_posterior": posterior["dados"]
                        })

                    elif intervalo > 5:
                        break

        # Ordena pelos casos de maior proximidade entre contratos
        continuidades.sort(
            key=lambda x: x["intervalo"]
        )

        total_continuidades_exatas = sum(
            1 for caso in continuidades
            if caso["intervalo"] == 1
        )

        total_mesma_data = sum(
            1 for caso in continuidades
            if caso["intervalo"] == 0
        )

        st.write(
            f"**Fornecedores com contratos analisados:** "
            f"{len(contratos_por_fornecedor)}"
        )

        st.write(
            f"**Pares de contratos com intervalo de até cinco dias:** "
            f"{len(continuidades)}"
        )

        st.write(
            f"**Pares em que o novo contrato começa um dia após "
            f"o término do anterior:** {total_continuidades_exatas}"
        )

        st.write(
            f"**Pares em que o novo contrato começa na mesma data "
            f"do término do anterior:** {total_mesma_data}"
        )

        if continuidades:

            for caso in continuidades:

                anterior = caso["contrato_anterior"]
                posterior = caso["contrato_posterior"]

                if caso["intervalo"] == 1:
                    classificacao = "Continuidade exata: 1 dia"
                elif caso["intervalo"] == 0:
                    classificacao = "Mesma data de término e início"
                else:
                    classificacao = (
                        f"Intervalo de {caso['intervalo']} dias"
                    )

                numero_anterior = anterior.get(
                    "numeroContratoEmpenho",
                    "Não informado"
                )

                numero_posterior = posterior.get(
                    "numeroContratoEmpenho",
                    "Não informado"
                )

                with st.expander(
                    f"{classificacao} | "
                    f"CNPJ {caso['cnpj']} | "
                    f"Contratos {numero_anterior} → {numero_posterior}"
                ):

                    st.markdown("**CONTRATO ANTERIOR**")

                    st.write(
                        f"**Fornecedor:** "
                        f"{anterior.get('nomeRazaoSocialFornecedor')}"
                    )

                    st.write(
                        f"**CNPJ:** {anterior.get('niFornecedor')}"
                    )

                    st.write(
                        f"**Objeto:** {anterior.get('objetoContrato')}"
                    )

                    st.write(
                        f"**Processo:** {anterior.get('processo')}"
                    )

                    st.write(
                        f"**Vigência:** "
                        f"{anterior.get('dataVigenciaInicio')} "
                        f"a {anterior.get('dataVigenciaFim')}"
                    )

                    st.write(
                        f"**Valor inicial:** "
                        f"{anterior.get('valorInicial')}"
                    )

                    st.write(
                        f"**Valor global:** "
                        f"{anterior.get('valorGlobal')}"
                    )

                    st.markdown("**CONTRATO POSTERIOR**")

                    st.write(
                        f"**Fornecedor:** "
                        f"{posterior.get('nomeRazaoSocialFornecedor')}"
                    )

                    st.write(
                        f"**CNPJ:** {posterior.get('niFornecedor')}"
                    )

                    st.write(
                        f"**Objeto:** {posterior.get('objetoContrato')}"
                    )

                    st.write(
                        f"**Processo:** {posterior.get('processo')}"
                    )

                    st.write(
                        f"**Vigência:** "
                        f"{posterior.get('dataVigenciaInicio')} "
                        f"a {posterior.get('dataVigenciaFim')}"
                    )

                    st.write(
                        f"**Valor inicial:** "
                        f"{posterior.get('valorInicial')}"
                    )

                    st.write(
                        f"**Valor global:** "
                        f"{posterior.get('valorGlobal')}"
                    )

                    st.markdown("**Registro completo do contrato anterior:**")
                    st.json(anterior)

                    st.markdown("**Registro completo do contrato posterior:**")
                    st.json(posterior)

        else:
            st.info(
                "Não foram encontrados contratos do mesmo fornecedor "
                "com continuidade de até cinco dias."
            )

        # =============================================================
        # FINALIZAÇÃO
        # =============================================================

        mensagem = (
            f"Diagnóstico concluído! Foram consultados "
            f"{total_registros} registros em "
            f"{total_paginas_consultadas} páginas. "
            f"Foram encontrados {len(contratos_longo_prazo)} "
            f"contratos com vigência superior a cinco anos e "
            f"{len(continuidades)} pares de contratos com "
            f"continuidade de até cinco dias."
        )

        return True, "TESTE", mensagem, []

    except requests.exceptions.Timeout:
        return (
            False,
            "",
            "Tempo limite excedido na conexão com o PNCP.",
            []
        )

    except requests.exceptions.ConnectionError as e:
        return (
            False,
            "",
            f"Erro de conexão com o PNCP: {str(e)}",
            []
        )

    except Exception as e:
        return False, "", f"Erro inesperado: {str(e)}", []

