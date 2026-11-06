from fastapi.testclient import TestClient

from app.auth.modelos import Perfil

CHAMADO = {
    "titulo": "Impressora não imprime",
    "descricao": "A impressora do financeiro parou depois da atualização.",
}


def test_sem_login_retorna_401(cliente: TestClient):
    resposta = cliente.get("/chamados")

    assert resposta.status_code == 401


def test_cria_chamado_em_nome_do_usuario_logado(cliente: TestClient, entrar):
    ana = entrar("ana@exemplo.com")

    resposta = cliente.post("/chamados", json=CHAMADO, headers=ana)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aberto"
    assert corpo["prioridade"] == "media"
    assert corpo["solicitante"]["nome"] == "ana"


def test_recusa_titulo_curto(cliente: TestClient, entrar):
    resposta = cliente.post("/chamados", json={**CHAMADO, "titulo": "ab"}, headers=entrar("ana@exemplo.com"))

    assert resposta.status_code == 422


def test_solicitante_ve_so_os_proprios_chamados(cliente: TestClient, entrar):
    ana = entrar("ana@exemplo.com")
    bruno = entrar("bruno@exemplo.com")
    cliente.post("/chamados", json=CHAMADO, headers=ana)
    do_bruno = cliente.post("/chamados", json=CHAMADO, headers=bruno).json()

    lista = cliente.get("/chamados", headers=ana).json()
    detalhe = cliente.get(f"/chamados/{do_bruno['id']}", headers=ana)

    assert lista["total"] == 1
    assert detalhe.status_code == 404


def test_tecnico_ve_todos_com_filtro_e_paginacao(cliente: TestClient, entrar):
    ana = entrar("ana@exemplo.com")
    tecnico = entrar("tecnico@exemplo.com", Perfil.TECNICO)
    cliente.post("/chamados", json=CHAMADO, headers=ana)
    cliente.post("/chamados", json={**CHAMADO, "prioridade": "alta"}, headers=ana)
    cliente.post("/chamados", json={**CHAMADO, "prioridade": "alta"}, headers=ana)

    corpo = cliente.get("/chamados", params={"prioridade": "alta", "limite": 1}, headers=tecnico).json()

    assert corpo["total"] == 2
    assert len(corpo["itens"]) == 1


def test_detalha_chamado_inexistente_retorna_404(cliente: TestClient, entrar):
    resposta = cliente.get("/chamados/999", headers=entrar("ana@exemplo.com"))

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Chamado não encontrado."


def test_solicitante_edita_o_texto_mas_nao_a_prioridade(cliente: TestClient, entrar):
    ana = entrar("ana@exemplo.com")
    chamado = cliente.post("/chamados", json=CHAMADO, headers=ana).json()

    texto = cliente.patch(f"/chamados/{chamado['id']}", json={"titulo": "Impressora parada"}, headers=ana)
    prioridade = cliente.patch(f"/chamados/{chamado['id']}", json={"prioridade": "critica"}, headers=ana)

    assert texto.json()["titulo"] == "Impressora parada"
    assert prioridade.status_code == 403


def test_tecnico_altera_a_prioridade(cliente: TestClient, entrar):
    ana = entrar("ana@exemplo.com")
    tecnico = entrar("tecnico@exemplo.com", Perfil.TECNICO)
    chamado = cliente.post("/chamados", json=CHAMADO, headers=ana).json()

    resposta = cliente.patch(f"/chamados/{chamado['id']}", json={"prioridade": "critica"}, headers=tecnico)

    assert resposta.json()["prioridade"] == "critica"
    assert resposta.json()["titulo"] == CHAMADO["titulo"]
