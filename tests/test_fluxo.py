from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth.modelos import Perfil
from app.chamados.modelos import Chamado
from tests.conftest import SessaoTeste

CHAMADO = {"titulo": "Sem acesso à VPN", "descricao": "A VPN não conecta desde ontem."}


@pytest.fixture
def ana(entrar) -> dict[str, str]:
    return entrar("ana@exemplo.com")


@pytest.fixture
def tecnico(entrar) -> dict[str, str]:
    return entrar("tecnico@exemplo.com", Perfil.TECNICO)


@pytest.fixture
def chamado(cliente: TestClient, ana) -> dict:
    return cliente.post("/chamados", json=CHAMADO, headers=ana).json()


def mudar_status(cliente: TestClient, chamado: dict, novo: str, cabecalho: dict[str, str]):
    return cliente.patch(f"/chamados/{chamado['id']}/status", json={"status": novo}, headers=cabecalho)


def test_fluxo_completo_ate_fechar(cliente: TestClient, ana, tecnico, chamado):
    assumido = cliente.post(f"/chamados/{chamado['id']}/assumir", headers=tecnico)
    resolvido = mudar_status(cliente, chamado, "resolvido", tecnico)
    fechado = mudar_status(cliente, chamado, "fechado", ana)

    assert assumido.json()["status"] == "em_atendimento"
    assert assumido.json()["tecnico"]["nome"] == "tecnico"
    assert resolvido.json()["resolvido_em"] is not None
    assert fechado.json()["status"] == "fechado"


def test_solicitante_nao_assume_chamado(cliente: TestClient, ana, chamado):
    resposta = cliente.post(f"/chamados/{chamado['id']}/assumir", headers=ana)

    assert resposta.status_code == 403


def test_chamado_ja_assumido_nao_pode_ser_assumido_de_novo(cliente: TestClient, entrar, tecnico, chamado):
    outro = entrar("outro@exemplo.com", Perfil.TECNICO)
    cliente.post(f"/chamados/{chamado['id']}/assumir", headers=tecnico)

    resposta = cliente.post(f"/chamados/{chamado['id']}/assumir", headers=outro)

    assert resposta.status_code == 409


def test_nao_pula_etapas_do_fluxo(cliente: TestClient, tecnico, chamado):
    resposta = mudar_status(cliente, chamado, "resolvido", tecnico)

    assert resposta.status_code == 409


def test_somente_o_tecnico_responsavel_resolve(cliente: TestClient, entrar, tecnico, chamado):
    outro = entrar("outro@exemplo.com", Perfil.TECNICO)
    cliente.post(f"/chamados/{chamado['id']}/assumir", headers=tecnico)

    resposta = mudar_status(cliente, chamado, "resolvido", outro)

    assert resposta.status_code == 403


def test_solicitante_reabre_e_a_resolucao_e_apagada(cliente: TestClient, ana, tecnico, chamado):
    cliente.post(f"/chamados/{chamado['id']}/assumir", headers=tecnico)
    mudar_status(cliente, chamado, "resolvido", tecnico)

    resposta = mudar_status(cliente, chamado, "em_atendimento", ana)

    assert resposta.json()["status"] == "em_atendimento"
    assert resposta.json()["resolvido_em"] is None


def test_chamado_fechado_nao_aceita_edicao_nem_comentario(cliente: TestClient, ana, tecnico, chamado):
    cliente.post(f"/chamados/{chamado['id']}/assumir", headers=tecnico)
    mudar_status(cliente, chamado, "resolvido", tecnico)
    mudar_status(cliente, chamado, "fechado", ana)

    edicao = cliente.patch(f"/chamados/{chamado['id']}", json={"titulo": "Novo título"}, headers=ana)
    comentario = cliente.post(f"/chamados/{chamado['id']}/comentarios", json={"texto": "Oi"}, headers=ana)

    assert edicao.status_code == 409
    assert comentario.status_code == 409


def test_mudar_a_prioridade_recalcula_o_prazo(cliente: TestClient, tecnico, chamado):
    resposta = cliente.patch(f"/chamados/{chamado['id']}", json={"prioridade": "critica"}, headers=tecnico)

    corpo = resposta.json()
    prazo = datetime.fromisoformat(corpo["prazo_em"])
    criado = datetime.fromisoformat(corpo["criado_em"])
    assert prazo - criado == timedelta(hours=4)


def test_filtro_de_atrasados(cliente: TestClient, ana, tecnico, chamado):
    cliente.post("/chamados", json=CHAMADO, headers=ana)
    with SessaoTeste() as sessao:
        atrasado = sessao.get(Chamado, chamado["id"])
        atrasado.prazo_em = datetime.now(UTC) - timedelta(hours=1)
        sessao.commit()

    corpo = cliente.get("/chamados", params={"atrasados": True}, headers=tecnico).json()

    assert corpo["total"] == 1
    assert corpo["itens"][0]["id"] == chamado["id"]
    assert corpo["itens"][0]["sla_estourado"] is True


def test_comentarios_do_solicitante_e_do_tecnico(cliente: TestClient, ana, tecnico, chamado):
    cliente.post(f"/chamados/{chamado['id']}/comentarios", json={"texto": "Continua sem conectar."}, headers=ana)
    cliente.post(f"/chamados/{chamado['id']}/comentarios", json={"texto": "Vou verificar."}, headers=tecnico)

    comentarios = cliente.get(f"/chamados/{chamado['id']}/comentarios", headers=ana).json()

    assert [item["autor"]["nome"] for item in comentarios] == ["ana", "tecnico"]


def test_nao_comenta_no_chamado_de_outra_pessoa(cliente: TestClient, entrar, chamado):
    bruno = entrar("bruno@exemplo.com")

    resposta = cliente.post(f"/chamados/{chamado['id']}/comentarios", json={"texto": "Oi"}, headers=bruno)

    assert resposta.status_code == 404
