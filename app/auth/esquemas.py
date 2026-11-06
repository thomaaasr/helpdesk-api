from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.modelos import Perfil


class UsuarioCriar(BaseModel):
    # Não existe campo "perfil" aqui de propósito: ninguém se cadastra como técnico sozinho.
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    perfil: Perfil


class UsuarioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
