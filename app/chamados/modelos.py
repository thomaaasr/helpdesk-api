from datetime import UTC, datetime
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
    tecnico_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", name="fk_chamados_tecnico_id"))
    prioridade: Mapped[Prioridade] = mapped_column(
        Enum(Prioridade, name="prioridade", values_callable=_valores), default=Prioridade.MEDIA
    )
    status: Mapped[StatusChamado] = mapped_column(
        Enum(StatusChamado, name="status_chamado", values_callable=_valores), default=StatusChamado.ABERTO
    )
    prazo_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # lazy="joined": traz os usuários na mesma consulta do chamado.
    # foreign_keys: a tabela tem duas ligações com usuarios, então é preciso dizer qual é qual.
    solicitante: Mapped[Usuario] = relationship(foreign_keys=[solicitante_id], lazy="joined")
    tecnico: Mapped[Usuario | None] = relationship(foreign_keys=[tecnico_id], lazy="joined")

    @property
    def sla_estourado(self) -> bool:
        """Compara o prazo com a data da resolução ou, se ainda não resolveu, com agora."""
        return (self.resolvido_em or datetime.now(UTC)) > self.prazo_em


class Comentario(Base):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    chamado_id: Mapped[int] = mapped_column(ForeignKey("chamados.id", name="fk_comentarios_chamado_id"))
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", name="fk_comentarios_autor_id"))
    texto: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    autor: Mapped[Usuario] = relationship(lazy="joined")
