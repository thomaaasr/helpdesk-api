from fastapi.testclient import TestClient


def test_saude_responde_ok(cliente: TestClient):
    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
