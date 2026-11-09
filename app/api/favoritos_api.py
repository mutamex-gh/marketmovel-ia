"""
Resource: FAVORITOS — imóveis salvos pelo usuário autenticado.

Autorização: todas as rotas exigem token; cada usuário só enxerga
e remove os próprios favoritos (ADMIN pode remover qualquer um).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Favorito, Imovel, Usuario
from app.api.deps import usuario_autenticado, verificar_dono_ou_admin
from app.api.schemas_api import FavoritoIn, FavoritoOut

router = APIRouter(prefix="/favoritos", tags=["Favoritos"])


@router.get("", response_model=List[FavoritoOut])
def listar_favoritos(usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Lista os favoritos do usuário autenticado."""
    return db.query(Favorito).filter(Favorito.usuario_id == usuario.id).order_by(Favorito.criado_em.desc()).all()


@router.post("", response_model=FavoritoOut, status_code=status.HTTP_201_CREATED)
def adicionar_favorito(dados: FavoritoIn, usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Adiciona um imóvel aos favoritos (409 se já estiver favoritado)."""
    if not db.get(Imovel, dados.imovel_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imóvel não encontrado.")
    existente = (
        db.query(Favorito)
        .filter(Favorito.usuario_id == usuario.id, Favorito.imovel_id == dados.imovel_id)
        .first()
    )
    if existente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este imóvel já está nos seus favoritos.")
    fav = Favorito(usuario_id=usuario.id, imovel_id=dados.imovel_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/{favorito_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_favorito(favorito_id: int, usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Remove um favorito (dono do favorito ou ADMIN)."""
    fav = db.get(Favorito, favorito_id)
    if not fav:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito não encontrado.")
    verificar_dono_ou_admin(usuario, fav.usuario_id)
    db.delete(fav)
    db.commit()

