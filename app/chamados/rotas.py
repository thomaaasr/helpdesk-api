from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencias import SessaoDep, UsuarioDep
from app.auth.modelos import Perfil, Usuario
from app.chamados.esquemas import ChamadoAtualizar, ChamadoCriar, ChamadoResposta, PaginaChamados
from app.chamados.modelos import Chamado, Prioridade, StatusChamado

rotas = APIRouter(prefix="/chamados", tags=["Chamados"])


def buscar_chamado(sessao: Session, chamado_id: int, usuario: Usuario) -> Chamado:
    chamado = sessao.get(Chamado, chamado_id)
    # Chamado de outra pessoa também responde 404: o solicitante nem fica sabendo que ele existe.
    if chamado is None or (usuario.perfil != Perfil.TECNICO and chamado.solicitante_id != usuario.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chamado não encontrado.")
    return chamado


@rotas.post("", response_model=ChamadoResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: ChamadoCriar, sessao: SessaoDep, usuario: UsuarioDep) -> Chamado:
    chamado = Chamado(**dados.model_dump(), solicitante_id=usuario.id)
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
    alteracoes = dados.model_dump(exclude_unset=True)
    if "prioridade" in alteracoes and usuario.perfil != Perfil.TECNICO:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente técnicos alteram a prioridade.")
    for campo, valor in alteracoes.items():
        setattr(chamado, campo, valor)
    sessao.commit()
    sessao.refresh(chamado)
    return chamado
