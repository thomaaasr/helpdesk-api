from fastapi.testclient import TestClient

CHAMADO = {
    "titulo": "Impressora não imprime",
    "descricao": "A impressora do financeiro parou depois da atualização.",
    "solicitante": "Ana Souza",
}


def test_cria_chamado_aberto_com_prioridade_media(cliente: TestClient):
    resposta = cliente.post("/chamados", json=CHAMADO)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aberto"
    assert corpo["prioridade"] == "media"


def test_recusa_titulo_curto(cliente: TestClient):
    resposta = cliente.post("/chamados", json={**CHAMADO, "titulo": "ab"})

    assert resposta.status_code == 422


def test_lista_com_filtro_e_paginacao(cliente: TestClient):
    cliente.post("/chamados", json=CHAMADO)
    cliente.post("/chamados", json={**CHAMADO, "prioridade": "alta"})
    cliente.post("/chamados", json={**CHAMADO, "prioridade": "alta"})

    resposta = cliente.get("/chamados", params={"prioridade": "alta", "limite": 1})

    corpo = resposta.json()
    assert corpo["total"] == 2
    assert len(corpo["itens"]) == 1


def test_detalha_chamado_inexistente_retorna_404(cliente: TestClient):
    resposta = cliente.get("/chamados/999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Chamado não encontrado."


def test_atualiza_somente_o_que_foi_enviado(cliente: TestClient):
    chamado = cliente.post("/chamados", json=CHAMADO).json()

    resposta = cliente.patch(f"/chamados/{chamado['id']}", json={"prioridade": "critica"})

    corpo = resposta.json()
    assert corpo["prioridade"] == "critica"
    assert corpo["titulo"] == CHAMADO["titulo"]
