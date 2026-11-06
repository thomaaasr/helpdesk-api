from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.modelos import Usuario
from app.banco import Base


class Prioridade(StrEnum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class StatusChamado(StrEnum):
    ABERTO = "aberto"
    EM_ATENDIMENTO = "em_atendimento"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"


def _valores(enum: type[StrEnum]) -> list[str]:
    return [item.value for item in enum]


class Chamado(Base):
    __tablename__ = "chamados"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(Text)
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", name="fk_chamados_solicitante_id"))
    prioridade: Mapped[Prioridade] = mapped_column(
        Enum(Prioridade, name="prioridade", values_callable=_valores), default=Prioridade.MEDIA
    )
    status: Mapped[StatusChamado] = mapped_column(
        Enum(StatusChamado, name="status_chamado", values_callable=_valores), default=StatusChamado.ABERTO
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # lazy="joined": traz o solicitante na mesma consulta do chamado.
    solicitante: Mapped[Usuario] = relationship(lazy="joined")
