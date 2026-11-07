from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.auth.esquemas import UsuarioResumo
from app.chamados.modelos import Prioridade, StatusChamado


class ChamadoCriar(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=1)
    prioridade: Prioridade = Prioridade.MEDIA


class ChamadoAtualizar(BaseModel):
    # Todos opcionais: o PATCH só altera o que foi enviado.
    titulo: str | None = Field(default=None, min_length=3, max_length=120)
    descricao: str | None = Field(default=None, min_length=1)
    prioridade: Prioridade | None = None


class StatusAlterar(BaseModel):
    status: StatusChamado


class ChamadoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str
    solicitante: UsuarioResumo
    tecnico: UsuarioResumo | None
    prioridade: Prioridade
    status: StatusChamado
    prazo_em: datetime
    resolvido_em: datetime | None
    sla_estourado: bool
    criado_em: datetime
    atualizado_em: datetime


class PaginaChamados(BaseModel):
    itens: list[ChamadoResposta]
    total: int
    pagina: int
    limite: int


class ComentarioCriar(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)


class ComentarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    autor: UsuarioResumo
    criado_em: datetime
