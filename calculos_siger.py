from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import pandas as pd
import numpy as np
import requests
import time


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
# 4. CONSULTA DE CONTRATOS VIGENTES DO PNCP - UFSM
# ============================================================

def buscar_dados_contratos_ufsm_comprasgov():

    import streamlit as st

    URL = "https://pncp.gov.br/api/consulta/v1/contratos"
    CNPJ_UFSM = "95591764000105"

    # Período amplo para localizar contratos antigos ainda vigentes
    DATA_INICIAL = datetime(2010, 1, 1).date()
    DATA_MEDICAO = datetime.now().date()

    TAMANHO_PAGINA = 500

    contratos_vigentes = {}
    total_registros_consultados = 0
    total_paginas_consultadas = 0

    # --------------------------------------------------------
    # Funções auxiliares
    # --------------------------------------------------------

    def converter_data(valor):

        if not valor:
            return None

        try:
            return datetime.strptime(
                str(valor)[:10], "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return None

    def converter_valor(valor):

        if valor is None or valor == "":
            return Decimal("0")

        try:
            return Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    def consultar_pagina(parametros, periodo, pagina):

        max_tentativas = 5

        for tentativa in range(1, max_tentativas + 1):

            try:

                resposta = requests.get(
                    URL,
                    params=parametros,
                    timeout=120
                )

                if resposta.status_code == 204:
                    return True, None

                if resposta.status_code == 200:
                    time.sleep(2)
                    return True, resposta.json()

                if resposta.status_code in [429, 500, 502, 503, 504]:

                    espera = tentativa * 5

                    st.warning(
                        f"Instabilidade no PNCP: HTTP "
                        f"{resposta.status_code}. "
                        f"Período {periodo}, página {pagina}. "
                        f"Tentativa {tentativa}/{max_tentativas}."
                    )

                    if tentativa < max_tentativas:
                        time.sleep(espera)
                        continue

            except requests.exceptions.RequestException as erro:

                if tentativa < max_tentativas:
                    time.sleep(tentativa * 5)
                    continue

        # Retorna falha graciosa caso atinja 5 tentativas infrutíferas
        msg_erro = (
            f"A sincronização foi interrompida devido a instabilidades no servidor do PNCP "
            f"no período de {periodo} (página {pagina}) após 5 tentativas sem sucesso."
        )
        return False, msg_erro

    # --------------------------------------------------------
    # 1. Consulta ao PNCP em períodos de até 365 dias
    # --------------------------------------------------------

    data_inicio = DATA_INICIAL

    while data_inicio <= DATA_MEDICAO:

        data_fim = min(
            data_inicio + timedelta(days=364),
            DATA_MEDICAO
        )

        periodo = (
            f"{data_inicio.strftime('%d/%m/%Y')} a "
            f"{data_fim.strftime('%d/%m/%Y')}"
        )

        pagina = 1

        while True:

            parametros = {
                "dataInicial": data_inicio.strftime("%Y%m%d"),
                "dataFinal": data_fim.strftime("%Y%m%d"),
                "cnpjOrgao": CNPJ_UFSM,
                "pagina": pagina,
                "tamanhoPagina": TAMANHO_PAGINA
            }

            sucesso_req, resultado = consultar_pagina(
                parametros,
                periodo,
                pagina
            )

            if not sucesso_req:
                # Interrompe graciosamente o processo e retorna o alerta de erro
                return False, 0, 0.0, resultado

            if resultado is None:
                break

            registros = resultado.get("data", [])

            if not registros:
                break

            total_registros_consultados += len(registros)
            total_paginas_consultadas += 1

            # ------------------------------------------------
            # 2. Filtra contratos vigentes na data da medição
            # ------------------------------------------------

            for registro in registros:

                tipo_contrato = (
                    registro.get("tipoContrato", {}).get("nome", "")
                )

                # Exclui empenhos, comodatos, concessões etc.
                if tipo_contrato != "Contrato (termo inicial)":
                    continue

                inicio_vigencia = converter_data(
                    registro.get("dataVigenciaInicio")
                )

                fim_vigencia = converter_data(
                    registro.get("dataVigenciaFim")
                )

                if not inicio_vigencia or not fim_vigencia:
                    continue

                if not (
                    inicio_vigencia <= DATA_MEDICAO <= fim_vigencia
                ):
                    continue

                # Identificador para evitar duplicidade entre consultas
                identificador = (
                    registro.get("numeroControlePNCP")
                    or registro.get("numeroControlePncpCompra")
                )

                if not identificador:
                    identificador = (
                        str(registro.get("anoContrato", ""))
                        + "-"
                        + str(registro.get("sequencialContrato", ""))
                    )

                contratos_vigentes[identificador] = registro

            total_paginas = resultado.get("totalPaginas", 1)

            if pagina >= total_paginas:
                break

            pagina += 1

        # Exibe o indicador de sucesso com ✅ para cada período finalizado
        st.write(f"✅ Sincronizado PNCP: {periodo}")

        data_inicio = data_fim + timedelta(days=1)

    # --------------------------------------------------------
    # 3. Calcula os indicadores
    # --------------------------------------------------------

    quantidade_contratos = len(contratos_vigentes)

    valor_global_total = sum(
        (
            converter_valor(
                contrato.get("valorGlobal")
            )
            for contrato in contratos_vigentes.values()
        ),
        Decimal("0")
    )

    mensagem = (
        f"Consulta concluída. Foram analisados "
        f"{total_registros_consultados} registros em "
        f"{total_paginas_consultadas} páginas do PNCP. "
        f"Foram identificados {quantidade_contratos} contratos "
        f"vigentes em {DATA_MEDICAO.strftime('%d/%m/%Y')}."
    )

    return (
        True,
        quantidade_contratos,
        float(valor_global_total),
        mensagem
    )
