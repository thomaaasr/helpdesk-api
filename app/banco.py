from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import configuracoes

engine = create_engine(configuracoes.database_url)
SessaoLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def obter_sessao() -> Iterator[Session]:
    """Abre uma sessão por requisição e fecha ao terminar, mesmo se der erro."""
    with SessaoLocal() as sessao:
        yield sessao
