from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import configuracoes

ALGORITMO = "HS256"

hasher = PasswordHash.recommended()


def gerar_hash(senha: str) -> str:
    return hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return hasher.verify(senha, senha_hash)


def criar_token(usuario_id: int) -> str:
    expira_em = datetime.now(UTC) + timedelta(minutes=configuracoes.jwt_expira_minutos)
    return jwt.encode({"sub": str(usuario_id), "exp": expira_em}, configuracoes.jwt_secret, algorithm=ALGORITMO)


def ler_usuario_do_token(token: str) -> int | None:
    """Devolve o id do usuário, ou None se o token for inválido ou estiver vencido."""
    try:
        conteudo = jwt.decode(token, configuracoes.jwt_secret, algorithms=[ALGORITMO])
        return int(conteudo["sub"])
    except jwt.InvalidTokenError, KeyError, ValueError:
        return None
