from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.chamados.modelos import Prioridade, StatusChamado


class ChamadoCriar(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=1)
    solicitante: str = Field(min_length=1, max_length=120)
    prioridade: Prioridade = Prioridade.MEDIA


class ChamadoAtualizar(BaseModel):
    # Todos opcionais: o PATCH só altera o que foi enviado.
    titulo: str | None = Field(default=None, min_length=3, max_length=120)
    descricao: str | None = Field(default=None, min_length=1)
    prioridade: Prioridade | None = None


class ChamadoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str
    solicitante: str
    prioridade: Prioridade
    status: StatusChamado
    criado_em: datetime
    atualizado_em: datetime


class PaginaChamados(BaseModel):
    itens: list[ChamadoResposta]
    total: int
    pagina: int
    limite: int
