from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.modelos import Usuario
from app.auth.seguranca import ler_usuario_do_token
from app.banco import obter_sessao

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")

SessaoDep = Annotated[Session, Depends(obter_sessao)]


def obter_usuario_atual(token: Annotated[str, Depends(esquema_oauth2)], sessao: SessaoDep) -> Usuario:
    usuario_id = ler_usuario_do_token(token)
    usuario = sessao.get(Usuario, usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado.", headers={"WWW-Authenticate": "Bearer"}
        )
    return usuario


UsuarioDep = Annotated[Usuario, Depends(obter_usuario_atual)]
