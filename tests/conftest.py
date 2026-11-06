from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.auth.modelos import Perfil, Usuario
from app.banco import Base, obter_sessao
from app.config import configuracoes
from app.main import app

url_teste = configuracoes.database_url_teste
if not url_teste or "teste" not in url_teste:
    raise RuntimeError("Defina DATABASE_URL_TESTE apontando para um banco com 'teste' no nome.")

engine_teste = create_engine(url_teste)
SessaoTeste = sessionmaker(bind=engine_teste)

SENHA = "senha-de-teste"


def obter_sessao_teste() -> Iterator[Session]:
    with SessaoTeste() as sessao:
        yield sessao


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    # Cada teste começa com as tabelas vazias.
    Base.metadata.drop_all(engine_teste)
    Base.metadata.create_all(engine_teste)
    app.dependency_overrides[obter_sessao] = obter_sessao_teste
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def entrar(cliente: TestClient) -> Callable[..., dict[str, str]]:
    """Cadastra um usuário, faz login e devolve o cabeçalho com o token."""

    def _entrar(email: str, perfil: Perfil = Perfil.SOLICITANTE) -> dict[str, str]:
        cliente.post("/auth/cadastro", json={"nome": email.split("@")[0], "email": email, "senha": SENHA})
        if perfil == Perfil.TECNICO:
            with SessaoTeste() as sessao:
                usuario = sessao.scalars(select(Usuario).where(Usuario.email == email)).one()
                usuario.perfil = Perfil.TECNICO
                sessao.commit()
        resposta = cliente.post("/auth/login", data={"username": email, "password": SENHA})
        return {"Authorization": f"Bearer {resposta.json()['access_token']}"}

    return _entrar
