import pandas as pd

# Mapeamento de métricas e constantes
IET_METRICAS = {
    "Atingido": 100,
    "Em andamento": 50,
    "Atrasado": 25,
    "Não iniciado": 0
}

def obter_cor_indicador(valor):
    """Retorna a cor baseada na faixa de pontuação."""
    if valor >= 80:
        return "green"
    elif valor >= 50:
        return "orange"
    return "red"

def calcular_iet(df_planos):
    """Calcula o Índice de Execução Temporal (IET)."""
    if df_planos.empty or "status" not in df_planos.columns:
        return 0.0, "Sem dados suficientes"
    
    # Cálculo baseado nas pontuações do status
    pontos = df_planos["status"].map(lambda s: IET_METRICAS.get(s, 0)).sum()
    total_possivel = len(df_planos) * 100
    
    if total_possivel == 0:
        return 0.0, "Sem planos para calcular"
        
    iet = (pontos / total_possivel) * 100
    
    if iet >= 80:
        desc = "Execução Satisfatória 🟢"
    elif iet >= 50:
        desc = "Execução Regular 🟡"
    else:
        desc = "Execução Crítica 🔴"
        
    return iet, desc

def calcular_icp(df_planos):
    """Calcula o Índice de Cumprimento de Prazos (ICP)."""
    if df_planos.empty or "status" not in df_planos.columns:
        return 0.0, "Sem dados suficientes"
        
    total = len(df_planos)
    em_dia = len(df_planos[df_planos["status"].isin(["Atingido", "Em andamento"])])
    
    if total == 0:
        return 0.0, "Sem planos para calcular"
        
    icp = (em_dia / total) * 100
    
    if icp >= 80:
        desc = "Prazos em Dia 🟢"
    elif icp >= 50:
        desc = "Atenção Moderada 🟡"
    else:
        desc = "Alto Índice de Atraso 🔴"
        
    return icp, desc

def calcular_itr(df_riscos):
    """Calcula o Índice de Tratamento de Riscos (ITR)."""
    if df_riscos.empty or "situacao_status" not in df_riscos.columns:
        return 0.0, "Sem dados suficientes"
        
    total = len(df_riscos)
    tratados = len(df_riscos[df_riscos["situacao_status"].str.lower().isin(["mitigado", "concluído", "concluido", "em monitoramento"])])
    
    if total == 0:
        return 0.0, "Sem riscos para calcular"
        
    itr = (tratados / total) * 100
    
    if itr >= 80:
        desc = "Tratamento Adequado 🟢"
    elif itr >= 50:
        desc = "Tratamento Parcial 🟡"
    else:
        desc = "Tratamento Deficiente 🔴"
        
    return itr, desc

def classificar_iar(iet, icp, itr):
    """Calcula e classifica o Índice de Atenção Rápida (IAR)."""
    iar_val = round((iet + icp + itr) / 3, 1)
    
    if iar_val >= 80:
        cat = "Baixa Atenção 🟢"
        desc = "Operação dentro da normalidade"
    elif iar_val >= 50:
        cat = "Média Atenção 🟡"
        desc = "Requer acompanhamento periódico"
    else:
        cat = "Alta Atenção 🔴"
        desc = "Intervenção imediata necessária"
        
    return iar_val, cat, desc
