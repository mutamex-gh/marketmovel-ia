"""
Resource: IMÓVEIS — CRUD + busca inteligente com IA.

Autorização:
- GET (listar / detalhar / buscar) .... público
- POST (criar) ........................ usuário autenticado (vira o dono)
- PUT / DELETE ........................ dono do imóvel ou ADMIN
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Imovel, Usuario
from app.embeddings import montar_texto_imovel, gerar_embedding, embedding_para_json, buscar_similares
from app.api.deps import usuario_autenticado, verificar_dono_ou_admin
from app.api.schemas_api import ImovelCreate, ImovelUpdate, ImovelOut, PaginaImoveis, ImovelBuscaOut

router = APIRouter(prefix="/imoveis", tags=["Imóveis"])


def _buscar_imovel(db: Session, imovel_id: int) -> Imovel:
    imovel = db.get(Imovel, imovel_id)
    if not imovel:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imóvel não encontrado.")
    return imovel


def _atualizar_embedding(imovel: Imovel) -> None:
    """Gera o vetor semântico (IA) usado na busca em linguagem natural."""
    try:
        vetor = gerar_embedding(montar_texto_imovel(imovel))
        if vetor:
            imovel.embedding = embedding_para_json(vetor)
    except Exception as e:  # a IA nunca deve derrubar o CRUD
        print(f"Aviso: falha ao gerar embedding: {e}")


@router.get("", response_model=PaginaImoveis)
def listar_imoveis(
    cidade: Optional[str] = None,
    bairro: Optional[str] = None,
    tipo_imovel: Optional[str] = None,
    finalidade: Optional[str] = Query(None, pattern="^(venda|aluguel)$"),
    quartos_min: Optional[int] = Query(None, ge=0),
    preco_min: Optional[float] = Query(None, ge=0),
    preco_max: Optional[float] = Query(None, ge=0),
    usuario_id: Optional[int] = Query(None, description="Imóveis de um anunciante específico"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista imóveis com filtros e paginação (público)."""
    q = db.query(Imovel)
    if cidade:
        q = q.filter(Imovel.cidade.ilike(f"%{cidade}%"))
    if bairro:
        q = q.filter(Imovel.bairro.ilike(f"%{bairro}%"))
    if tipo_imovel:
        q = q.filter(Imovel.tipo_imovel == tipo_imovel)
    if finalidade:
        q = q.filter(Imovel.finalidade == finalidade)
    if quartos_min is not None:
        q = q.filter(Imovel.quartos >= quartos_min)
    if preco_min is not None:
        q = q.filter(Imovel.preco >= preco_min)
    if preco_max is not None:
        q = q.filter(Imovel.preco <= preco_max)
    if usuario_id is not None:
        q = q.filter(Imovel.usuario_id == usuario_id)

    total = q.count()
    itens = q.order_by(Imovel.criado_em.desc()).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    return PaginaImoveis(total=total, pagina=pagina, por_pagina=por_pagina, itens=itens)


@router.get("/busca", response_model=List[ImovelBuscaOut])
def busca_inteligente(
    q: str = Query(..., min_length=2, description="Texto livre, ex: 'casa com 3 quartos e piscina em Chapecó'"),
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Busca semântica em linguagem natural usando IA (embeddings) — público."""
    imoveis = db.query(Imovel).all()
    resultados = buscar_similares(q, imoveis, top_k=limite)
    return [ImovelBuscaOut(score=round(float(s), 4), imovel=im) for im, s in resultados]


@router.get("/meus", response_model=List[ImovelOut])
def meus_imoveis(usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Imóveis do usuário autenticado."""
    return db.query(Imovel).filter(Imovel.usuario_id == usuario.id).order_by(Imovel.criado_em.desc()).all()


@router.get("/{imovel_id}", response_model=ImovelOut)
def obter_imovel(imovel_id: int, db: Session = Depends(get_db)):
    """Detalhe de um imóvel (público). Incrementa o contador de visualizações."""
    imovel = _buscar_imovel(db, imovel_id)
    imovel.visualizacoes = (imovel.visualizacoes or 0) + 1
    db.commit()
    db.refresh(imovel)
    return imovel


@router.post("", response_model=ImovelOut, status_code=status.HTTP_201_CREATED)
def criar_imovel(
    dados: ImovelCreate,
    usuario: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Cadastra um imóvel. O dono será o usuário do token."""
    imovel = Imovel(usuario_id=usuario.id, **dados.model_dump())
    db.add(imovel)
    db.flush()
    _atualizar_embedding(imovel)
    db.commit()
    db.refresh(imovel)
    return imovel


@router.put("/{imovel_id}", response_model=ImovelOut)
def atualizar_imovel(
    imovel_id: int,
    dados: ImovelUpdate,
    usuario: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Atualiza um imóvel (dono ou ADMIN). Envie apenas os campos a alterar."""
    imovel = _buscar_imovel(db, imovel_id)
    verificar_dono_ou_admin(usuario, imovel.usuario_id)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(imovel, campo, valor)
    _atualizar_embedding(imovel)
    db.commit()
    db.refresh(imovel)
    return imovel


@router.delete("/{imovel_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_imovel(
    imovel_id: int,
    usuario: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Exclui um imóvel e suas imagens/favoritos/interesses (dono ou ADMIN)."""
    imovel = _buscar_imovel(db, imovel_id)
    verificar_dono_ou_admin(usuario, imovel.usuario_id)
    db.delete(imovel)
    db.commit()

