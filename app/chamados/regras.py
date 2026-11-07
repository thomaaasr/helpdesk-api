from datetime import datetime, timedelta

from app.chamados.modelos import Prioridade, StatusChamado

# Horas corridas para resolver, a partir da abertura do chamado.
PRAZOS_EM_HORAS = {
    Prioridade.CRITICA: 4,
    Prioridade.ALTA: 8,
    Prioridade.MEDIA: 24,
    Prioridade.BAIXA: 72,
}

# Para onde cada status pode ir. "aberto" só muda pela rota de assumir, que também define o técnico.
TRANSICOES = {
    StatusChamado.ABERTO: set(),
    StatusChamado.EM_ATENDIMENTO: {StatusChamado.RESOLVIDO},
    StatusChamado.RESOLVIDO: {StatusChamado.FECHADO, StatusChamado.EM_ATENDIMENTO},
    StatusChamado.FECHADO: set(),
}


def calcular_prazo(prioridade: Prioridade, aberto_em: datetime) -> datetime:
    return aberto_em + timedelta(hours=PRAZOS_EM_HORAS[prioridade])


def pode_mudar_status(atual: StatusChamado, novo: StatusChamado) -> bool:
    return novo in TRANSICOES[atual]
