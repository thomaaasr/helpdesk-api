from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencias import SessaoDep, UsuarioDep
from app.auth.esquemas import Token, UsuarioCriar, UsuarioResposta
from app.auth.modelos import Usuario
from app.auth.seguranca import criar_token, gerar_hash, verificar_senha

rotas = APIRouter(prefix="/auth", tags=["Autenticação"])


@rotas.post("/cadastro", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioCriar, sessao: SessaoDep) -> Usuario:
    usuario = Usuario(nome=dados.nome, email=dados.email.lower(), senha_hash=gerar_hash(dados.senha))
    sessao.add(usuario)
    try:
        sessao.commit()
    except IntegrityError as erro:
        sessao.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado.") from erro
    sessao.refresh(usuario)
    return usuario


@rotas.post("/login", response_model=Token)
def entrar(formulario: Annotated[OAuth2PasswordRequestForm, Depends()], sessao: SessaoDep) -> Token:
    # O padrão OAuth2 chama o campo de "username"; aqui ele recebe o e-mail.
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == formulario.username.lower()))
    if usuario is None or not verificar_senha(formulario.password, usuario.senha_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos.", headers={"WWW-Authenticate": "Bearer"}
        )
    return Token(access_token=criar_token(usuario.id))


@rotas.get("/eu", response_model=UsuarioResposta)
def quem_sou_eu(usuario: UsuarioDep) -> Usuario:
    return usuario
