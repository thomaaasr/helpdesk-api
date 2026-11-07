from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencias import SessaoDep, UsuarioDep
from app.auth.modelos import Perfil, Usuario
from app.chamados.esquemas import (
    ChamadoAtualizar,
    ChamadoCriar,
    ChamadoResposta,
    ComentarioCriar,
    ComentarioResposta,
    PaginaChamados,
    StatusAlterar,
)
from app.chamados.modelos import Chamado, Comentario, Prioridade, StatusChamado
from app.chamados.regras import calcular_prazo, pode_mudar_status

rotas = APIRouter(prefix="/chamados", tags=["Chamados"])


def buscar_chamado(sessao: Session, chamado_id: int, usuario: Usuario) -> Chamado:
    chamado = sessao.get(Chamado, chamado_id)
    # Chamado de outra pessoa também responde 404: o solicitante nem fica sabendo que ele existe.
    if chamado is None or (usuario.perfil != Perfil.TECNICO and chamado.solicitante_id != usuario.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chamado não encontrado.")
    return chamado


def recusar_se_fechado(chamado: Chamado) -> None:
    if chamado.status == StatusChamado.FECHADO:
        raise HTTPException(status.HTTP_409_CONFLICT, "Chamado fechado não pode ser alterado.")


@rotas.post("", response_model=ChamadoResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: ChamadoCriar, sessao: SessaoDep, usuario: UsuarioDep) -> Chamado:
    prazo = calcular_prazo(dados.prioridade, datetime.now(UTC))
    chamado = Chamado(**dados.model_dump(), solicitante_id=usuario.id, prazo_em=prazo)
    sessao.add(chamado)
    sessao.commit()
    sessao.refresh(chamado)
    return chamado


@rotas.get("", response_model=PaginaChamados)
def listar(
    sessao: SessaoDep,
    usuario: UsuarioDep,
    status_chamado: Annotated[StatusChamado | None, Query(alias="status")] = None,
    prioridade: Prioridade | None = None,
    atrasados: bool = False,
    pagina: Annotated[int, Query(ge=1)] = 1,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
) -> PaginaChamados:
    filtros = []
    if usuario.perfil != Perfil.TECNICO:
        filtros.append(Chamado.solicitante_id == usuario.id)
    if status_chamado is not None:
        filtros.append(Chamado.status == status_chamado)
    if prioridade is not None:
        filtros.append(Chamado.prioridade == prioridade)
    if atrasados:
        filtros.append(Chamado.status.in_([StatusChamado.ABERTO, StatusChamado.EM_ATENDIMENTO]))
        filtros.append(Chamado.prazo_em < func.now())

    total = sessao.scalar(select(func.count()).select_from(Chamado).where(*filtros)) or 0
    consulta = select(Chamado).where(*filtros).order_by(Chamado.id.desc()).offset((pagina - 1) * limite).limit(limite)
    itens = sessao.scalars(consulta).all()
    return PaginaChamados(
        itens=[ChamadoResposta.model_validate(item) for item in itens], total=total, pagina=pagina, limite=limite
    )


@rotas.get("/{chamado_id}", response_model=ChamadoResposta)
def detalhar(chamado_id: int, sessao: SessaoDep, usuario: UsuarioDep) -> Chamado:
    return buscar_chamado(sessao, chamado_id, usuario)


@rotas.patch("/{chamado_id}", response_model=ChamadoResposta)
def atualizar(chamado_id: int, dados: ChamadoAtualizar, sessao: SessaoDep, usuario: UsuarioDep) -> Chamado:
    chamado = buscar_chamado(sessao, chamado_id, usuario)
    recusar_se_fechado(chamado)
    alteracoes = dados.model_dump(exclude_unset=True)
    if "prioridade" in alteracoes:
        if usuario.perfil != Perfil.TECNICO:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente técnicos alteram a prioridade.")
        chamado.prazo_em = calcular_prazo(alteracoes["prioridade"], chamado.criado_em)
    for campo, valor in alteracoes.items():
        setattr(chamado, campo, valor)
    sessao.commit()
    sessao.refresh(chamado)
    return chamado


@rotas.post("/{chamado_id}/assumir", response_model=ChamadoResposta)
def assumir(chamado_id: int, sessao: SessaoDep, usuario: UsuarioDep) -> Chamado:
    if usuario.perfil != Perfil.TECNICO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente técnicos assumem chamados.")
    chamado = buscar_chamado(sessao, chamado_id, usuario)
    if chamado.status != StatusChamado.ABERTO:
        raise HTTPException(status.HTTP_409_CONFLICT, "Somente chamados abertos podem ser assumidos.")
    chamado.tecnico_id = usuario.id
    chamado.status = StatusChamado.EM_ATENDIMENTO
    sessao.commit()
    sessao.refresh(chamado)
    return chamado


@rotas.patch("/{chamado_id}/status", response_model=ChamadoResposta)
def mudar_status(chamado_id: int, dados: StatusAlterar, sessao: SessaoDep, usuario: UsuarioDep) -> Chamado:
    chamado = buscar_chamado(sessao, chamado_id, usuario)
    if not pode_mudar_status(chamado.status, dados.status):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Não é possível mudar de {chamado.status} para {dados.status}.")
    if dados.status == StatusChamado.RESOLVIDO:
        if usuario.id != chamado.tecnico_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente o técnico responsável resolve o chamado.")
        chamado.resolvido_em = datetime.now(UTC)
    elif dados.status == StatusChamado.EM_ATENDIMENTO:
        # Reabertura: o chamado volta a contar como não resolvido.
        chamado.resolvido_em = None
    chamado.status = dados.status
    sessao.commit()
    sessao.refresh(chamado)
    return chamado


@rotas.post("/{chamado_id}/comentarios", response_model=ComentarioResposta, status_code=status.HTTP_201_CREATED)
def comentar(chamado_id: int, dados: ComentarioCriar, sessao: SessaoDep, usuario: UsuarioDep) -> Comentario:
    chamado = buscar_chamado(sessao, chamado_id, usuario)
    recusar_se_fechado(chamado)
    comentario = Comentario(chamado_id=chamado.id, autor_id=usuario.id, texto=dados.texto)
    sessao.add(comentario)
    sessao.commit()
    sessao.refresh(comentario)
    return comentario


@rotas.get("/{chamado_id}/comentarios", response_model=list[ComentarioResposta])
def listar_comentarios(chamado_id: int, sessao: SessaoDep, usuario: UsuarioDep) -> Sequence[Comentario]:
    chamado = buscar_chamado(sessao, chamado_id, usuario)
    consulta = select(Comentario).where(Comentario.chamado_id == chamado.id).order_by(Comentario.id)
    return sessao.scalars(consulta).all()
