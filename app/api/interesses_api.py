"""
Resource: INTERESSES — usuário demonstra interesse (contato) em um imóvel.

Autorização:
- POST ......................... usuário autenticado
- GET /interesses .............. ADMIN vê todos; usuário comum vê os que enviou
- GET /interesses/recebidos .... interesses nos imóveis do usuário (anunciante)
- GET /{id} .................... autor, dono do imóvel ou ADMIN
- PUT .......................... somente o autor
- DELETE ....................... autor ou ADMIN
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Imovel, Interesse, Usuario
from app.api.deps import usuario_autenticado, eh_admin
from app.api.schemas_api import InteresseIn, InteresseOut, InteresseUpdate

router = APIRouter(prefix="/interesses", tags=["Interesses"])


def _buscar(db: Session, interesse_id: int) -> Interesse:
    item = db.get(Interesse, interesse_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interesse não encontrado.")
    return item


@router.get("", response_model=List[InteresseOut])
def listar_interesses(usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """ADMIN: todos os interesses. Usuário comum: apenas os que ele enviou."""
    q = db.query(Interesse)
    if not eh_admin(usuario):
        q = q.filter(Interesse.usuario_id == usuario.id)
    return q.order_by(Interesse.criado_em.desc()).all()


@router.get("/recebidos", response_model=List[InteresseOut])
def interesses_recebidos(usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Interesses recebidos nos imóveis anunciados pelo usuário autenticado."""
    return (
        db.query(Interesse)
        .join(Imovel, Interesse.imovel_id == Imovel.id)
        .filter(Imovel.usuario_id == usuario.id)
        .order_by(Interesse.criado_em.desc())
        .all()
    )


@router.get("/{interesse_id}", response_model=InteresseOut)
def obter_interesse(interesse_id: int, usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    item = _buscar(db, interesse_id)
    if not (eh_admin(usuario) or item.usuario_id == usuario.id or item.imovel.usuario_id == usuario.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado a este interesse.")
    return item


@router.post("", response_model=InteresseOut, status_code=status.HTTP_201_CREATED)
def registrar_interesse(dados: InteresseIn, usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Registra interesse em um imóvel (não é permitido no próprio imóvel)."""
    imovel = db.get(Imovel, dados.imovel_id)
    if not imovel:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imóvel não encontrado.")
    if imovel.usuario_id == usuario.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Você não pode demonstrar interesse no seu próprio imóvel.")
    item = Interesse(imovel_id=imovel.id, usuario_id=usuario.id, mensagem=dados.mensagem)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{interesse_id}", response_model=InteresseOut)
def atualizar_interesse(
    interesse_id: int, dados: InteresseUpdate, usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)
):
    """Edita a mensagem do interesse (somente o autor)."""
    item = _buscar(db, interesse_id)
    if item.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente o autor pode editar este interesse.")
    item.mensagem = dados.mensagem
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{interesse_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_interesse(interesse_id: int, usuario: Usuario = Depends(usuario_autenticado), db: Session = Depends(get_db)):
    """Remove o interesse (autor ou ADMIN)."""
    item = _buscar(db, interesse_id)
    if item.usuario_id != usuario.id and not eh_admin(usuario):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Somente o autor ou um administrador pode excluir.")
    db.delete(item)
    db.commit()

