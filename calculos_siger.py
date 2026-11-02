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
    Consulta contratos da UFSM no PNCP.
    Retorna:
    (sucesso, valor_kri_formatado, mensagem, lista_contratos)
    """
    from datetime import datetime, timedelta, timezone
    import requests

    fuso_br = timezone(timedelta(hours=-3))
    hoje = datetime.now(fuso_br).date()

    # Período inicial: últimos 365 dias
    data_inicial = (hoje - timedelta(days=365)).strftime("%Y%m%d")
    data_final = hoje.strftime("%Y%m%d")

    cnpj_ufsm = "95591764000105"
    url = "https://pncp.gov.br/api/consulta/v1/contratos"

    headers = {
        "accept": "application/json",
        "User-Agent": "SIGER-UFSM/1.0"
    }

    lista_contratos = []
    pagina = 1
    total_paginas = 1

    try:
        while pagina <= total_paginas:
            parametros = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "cnpjOrgao": cnpj_ufsm,
                "pagina": pagina,
                "tamanhoPagina": 500
            }

            response = requests.get(
                url,
                params=parametros,
                headers=headers,
                timeout=60
            )

            if response.status_code != 200:
                return (
                    False, "", 
                    f"Erro HTTP {response.status_code} na página {pagina}: "
                    f"{response.text[:1000]}",
                    []
                )

            dados = response.json()
            itens = dados.get("data", [])

            if not isinstance(itens, list):
                return False, "", "Formato inesperado de resposta do PNCP.", []

            total_paginas = int(dados.get("totalPaginas", 1) or 1)

            for item in itens:
                tipo = item.get("tipoContrato") or {}
                nome_tipo = tipo.get("nome", "").strip().lower()

                # Considera somente contratos, excluindo empenhos
                if nome_tipo != "contrato":
                    continue

                valor = item.get("valorGlobal") or item.get("valorInicial") or 0

                lista_contratos.append({
                    "Número Contrato / Empenho": item.get(
                        "numeroContratoEmpenho", "Não informado"
                    ),
                    "Objeto / Categoria": item.get("objetoContrato", ""),
                    "Valor Global": float(valor or 0),
                    "Data Inicial": item.get("dataVigenciaInicio"),
                    "Data Final": item.get("dataVigenciaFim"),
                    "Número Controle PNCP": item.get("numeroControlePNCP"),
                    "Tipo de Instrumento": tipo.get("nome", ""),
                    "Fornecedor": item.get("nomeRazaoSocialFornecedor", ""),
                    "Processo": item.get("processo", ""),
                    "Dados Originais": str(item)
                })

            pagina += 1

        # Remove duplicidades pelo número de controle PNCP
        contratos_unicos = {}
        for contrato in lista_contratos:
            chave = contrato.get("Número Controle PNCP")
            if chave:
                contratos_unicos[chave] = contrato

        lista_contratos = list(contratos_unicos.values())

        mensagem = (
            f"Consulta concluída! Foram percorridas {total_paginas} páginas. "
            f"Contratos encontrados: {len(lista_contratos)}."
        )

        return True, "TESTE", mensagem, lista_contratos

    except requests.exceptions.Timeout:
        return False, "", "Tempo limite excedido na conexão com o PNCP.", []

    except requests.exceptions.ConnectionError as e:
        return False, "", f"Erro de conexão com o PNCP: {str(e)}", []

    except Exception as e:
        return False, "", f"Erro inesperado: {str(e)}", []

