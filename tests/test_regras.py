from datetime import UTC, datetime, timedelta

import pytest

from app.chamados.modelos import Chamado, Prioridade, StatusChamado
from app.chamados.regras import calcular_prazo, pode_mudar_status

AGORA = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("prioridade", "horas"),
    [(Prioridade.CRITICA, 4), (Prioridade.ALTA, 8), (Prioridade.MEDIA, 24), (Prioridade.BAIXA, 72)],
)
def test_prazo_depende_da_prioridade(prioridade: Prioridade, horas: int):
    assert calcular_prazo(prioridade, AGORA) == AGORA + timedelta(hours=horas)


@pytest.mark.parametrize(
    ("atual", "novo", "esperado"),
    [
        (StatusChamado.EM_ATENDIMENTO, StatusChamado.RESOLVIDO, True),
        (StatusChamado.RESOLVIDO, StatusChamado.FECHADO, True),
        (StatusChamado.RESOLVIDO, StatusChamado.EM_ATENDIMENTO, True),
        (StatusChamado.ABERTO, StatusChamado.RESOLVIDO, False),
        (StatusChamado.ABERTO, StatusChamado.EM_ATENDIMENTO, False),
        (StatusChamado.FECHADO, StatusChamado.EM_ATENDIMENTO, False),
    ],
)
def test_transicoes_de_status(atual: StatusChamado, novo: StatusChamado, esperado: bool):
    assert pode_mudar_status(atual, novo) is esperado


def test_sla_usa_a_data_da_resolucao_quando_existe():
    dentro_do_prazo = Chamado(prazo_em=AGORA, resolvido_em=AGORA - timedelta(minutes=1))
    fora_do_prazo = Chamado(prazo_em=AGORA, resolvido_em=AGORA + timedelta(minutes=1))

    assert dentro_do_prazo.sla_estourado is False
    assert fora_do_prazo.sla_estourado is True


def test_sla_sem_resolucao_compara_com_agora():
    assert Chamado(prazo_em=datetime.now(UTC) - timedelta(minutes=1)).sla_estourado is True
    assert Chamado(prazo_em=datetime.now(UTC) + timedelta(hours=1)).sla_estourado is False
