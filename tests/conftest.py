from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.banco import Base, obter_sessao
from app.config import configuracoes
from app.main import app

url_teste = configuracoes.database_url_teste
if not url_teste or "teste" not in url_teste:
    raise RuntimeError("Defina DATABASE_URL_TESTE apontando para um banco com 'teste' no nome.")

engine_teste = create_engine(url_teste)
SessaoTeste = sessionmaker(bind=engine_teste)


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
