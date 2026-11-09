"""
Resource: IMAGENS de um imóvel — listar, enviar (upload) e excluir.

Autorização:
- GET ............... público
- POST / DELETE ..... dono do imóvel ou ADMIN
"""
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import Imagem, Imovel, Usuario
from app.routes.imovel_routes import _salvar_imagem
from app.api.deps import usuario_autenticado, verificar_dono_ou_admin
from app.api.schemas_api import ImagemOut

router = APIRouter(prefix="/imoveis/{imovel_id}/imagens", tags=["Imagens"])

EXTENSOES_PERMITIDAS = (".jpg", ".jpeg", ".png", ".webp")


def _buscar_imovel(db: Session, imovel_id: int) -> Imovel:
    imovel = db.get(Imovel, imovel_id)
    if not imovel:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imóvel não encontrado.")
    return imovel


@router.get("", response_model=List[ImagemOut])
def listar_imagens(imovel_id: int, db: Session = Depends(get_db)):
    """Lista as imagens do imóvel (público)."""
    _buscar_imovel(db, imovel_id)
    return db.query(Imagem).filter(Imagem.imovel_id == imovel_id).order_by(Imagem.ordem).all()


@router.post("", response_model=List[ImagemOut], status_code=status.HTTP_201_CREATED)
def enviar_imagens(
    imovel_id: int,
    arquivos: List[UploadFile] = File(..., description="Uma ou mais imagens (jpg, png, webp)"),
    usuario: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Upload de imagens (multipart/form-data, campo 'arquivos') — dono ou ADMIN."""
    imovel = _buscar_imovel(db, imovel_id)
    verificar_dono_ou_admin(usuario, imovel.usuario_id)

    ordem = db.query(Imagem).filter(Imagem.imovel_id == imovel_id).count()
    criadas = []
    for arquivo in arquivos:
        if not arquivo.filename or not arquivo.filename.lower().endswith(EXTENSOES_PERMITIDAS):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Arquivo inválido: {arquivo.filename}")
        try:
            nome = _salvar_imagem(arquivo)
        except Exception:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Não foi possível ler a imagem {arquivo.filename}")
        img = Imagem(imovel_id=imovel_id, caminho=nome, ordem=ordem)
        ordem += 1
        db.add(img)
        criadas.append(img)

    db.commit()
    for img in criadas:
        db.refresh(img)
    return criadas


@router.delete("/{imagem_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_imagem(
    imovel_id: int,
    imagem_id: int,
    usuario: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Exclui uma imagem do imóvel (registro + arquivo) — dono ou ADMIN."""
    imovel = _buscar_imovel(db, imovel_id)
    verificar_dono_ou_admin(usuario, imovel.usuario_id)

    img = db.query(Imagem).filter(Imagem.id == imagem_id, Imagem.imovel_id == imovel_id).first()
    if not img:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagem não encontrada neste imóvel.")

    caminho = UPLOAD_DIR / img.caminho
    db.delete(img)
    db.commit()
    try:
        if caminho.is_file():
            caminho.unlink()
    except OSError:
        pass

