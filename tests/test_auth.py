from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.modelos import Usuario
from app.auth.seguranca import ALGORITMO
from app.config import configuracoes
from tests.conftest import SENHA, SessaoTeste

NOVO_USUARIO = {"nome": "Ana Souza", "email": "ana@exemplo.com", "senha": SENHA}


def test_cadastro_guarda_senha_com_hash_e_nao_devolve_a_senha(cliente: TestClient):
    resposta = cliente.post("/auth/cadastro", json=NOVO_USUARIO)

    assert resposta.status_code == 201
    assert "senha" not in resposta.text
    with SessaoTeste() as sessao:
        usuario = sessao.scalars(select(Usuario)).one()
    assert usuario.senha_hash != SENHA


def test_cadastro_ignora_tentativa_de_virar_tecnico(cliente: TestClient):
    resposta = cliente.post("/auth/cadastro", json={**NOVO_USUARIO, "perfil": "tecnico"})

    assert resposta.json()["perfil"] == "solicitante"


def test_cadastro_recusa_email_repetido_mesmo_com_maiusculas(cliente: TestClient):
    cliente.post("/auth/cadastro", json=NOVO_USUARIO)

    resposta = cliente.post("/auth/cadastro", json={**NOVO_USUARIO, "email": "ANA@exemplo.com"})

    assert resposta.status_code == 409


def test_login_com_senha_errada_retorna_401(cliente: TestClient):
    cliente.post("/auth/cadastro", json=NOVO_USUARIO)

    resposta = cliente.post("/auth/login", data={"username": NOVO_USUARIO["email"], "password": "errada-123"})

    assert resposta.status_code == 401


def test_eu_devolve_o_usuario_do_token(cliente: TestClient, entrar):
    cabecalho = entrar("ana@exemplo.com")

    resposta = cliente.get("/auth/eu", headers=cabecalho)

    assert resposta.json()["email"] == "ana@exemplo.com"


def test_token_vencido_retorna_401(cliente: TestClient):
    vencido = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode({"sub": "1", "exp": vencido}, configuracoes.jwt_secret, algorithm=ALGORITMO)

    resposta = cliente.get("/auth/eu", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 401
