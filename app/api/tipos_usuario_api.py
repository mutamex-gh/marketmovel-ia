"""
Resource: TIPOS DE USUÁRIO — CRUD.

Autorização:
- GET (listar / detalhar) ...... público
- POST / PUT / DELETE .......... somente ADMIN
"""
import re
import unicodedata
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TipoUsuario, Usuario
from app.api.deps import exigir_admin
from app.api.schemas_api import TipoUsuarioIn, TipoUsuarioOut

router = APIRouter(prefix="/tipos-usuario", tags=["Tipos de Usuário"])


def _slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def _buscar(db: Session, tipo_id: int) -> TipoUsuario:
    tipo = db.get(TipoUsuario, tipo_id)
    if not tipo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tipo de usuário não encontrado.")
    return tipo


@router.get("", response_model=List[TipoUsuarioOut])
def listar_tipos(db: Session = Depends(get_db)):
    """Lista os tipos de usuário (público)."""
    return db.query(TipoUsuario).order_by(TipoUsuario.id).all()


@router.get("/{tipo_id}", response_model=TipoUsuarioOut)
def obter_tipo(tipo_id: int, db: Session = Depends(get_db)):
    return _buscar(db, tipo_id)


@router.post("", response_model=TipoUsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_tipo(dados: TipoUsuarioIn, _: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)):
    """Cria um novo tipo de usuário (ADMIN)."""
    slug = _slugify(dados.slug or dados.nome)
    if db.query(TipoUsuario).filter((TipoUsuario.slug == slug) | (TipoUsuario.nome == dados.nome)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um tipo com este nome/slug.")
    tipo = TipoUsuario(nome=dados.nome.strip(), slug=slug)
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


@router.put("/{tipo_id}", response_model=TipoUsuarioOut)
def atualizar_tipo(
    tipo_id: int, dados: TipoUsuarioIn, _: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)
):
    """Atualiza nome/slug de um tipo (ADMIN)."""
    tipo = _buscar(db, tipo_id)
    slug = _slugify(dados.slug or dados.nome)
    conflito = (
        db.query(TipoUsuario)
        .filter(TipoUsuario.id != tipo_id)
        .filter((TipoUsuario.slug == slug) | (TipoUsuario.nome == dados.nome))
        .first()
    )
    if conflito:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um tipo com este nome/slug.")
    tipo.nome = dados.nome.strip()
    tipo.slug = slug
    db.commit()
    db.refresh(tipo)
    return tipo


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_tipo(tipo_id: int, _: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)):
    """Exclui um tipo (ADMIN). Bloqueado se houver usuários usando o tipo."""
    tipo = _buscar(db, tipo_id)
    em_uso = db.query(Usuario).filter(Usuario.tipo_usuario == tipo.slug).count()
    if em_uso:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Não é possível excluir: {em_uso} usuário(s) usam este tipo."
        )
    db.delete(tipo)
    db.commit()

