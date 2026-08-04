"""
Rotas de imóveis — CRUD, upload de imagens e registro de interesse.
"""
import uuid
import os
from pathlib import Path

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from PIL import Image as PILImage

from app.database import get_db
from app.models import Usuario, Imovel, Imagem, Interesse
from app.auth import obter_usuario_logado
from app.config import UPLOAD_DIR, MAX_IMAGE_WIDTH


router = APIRouter(tags=["imóveis"])
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _salvar_imagem(arquivo: UploadFile) -> str:
    """
    Salva imagem no disco, redimensiona se necessário.
    Retorna o caminho relativo (para servir via /static/uploads/).
    """
    # Gera nome único
    extensao = Path(arquivo.filename).suffix.lower()
    if extensao not in (".jpg", ".jpeg", ".png", ".webp"):
        extensao = ".jpg"
    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    caminho_completo = UPLOAD_DIR / nome_arquivo

    # Salva e redimensiona
    img = PILImage.open(arquivo.file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if img.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / img.width
        novo_tamanho = (MAX_IMAGE_WIDTH, int(img.height * ratio))
        img = img.resize(novo_tamanho, PILImage.LANCZOS)
    img.save(caminho_completo, quality=85)

    return nome_arquivo


# ---------------------------------------------------------------------------
# Cadastro de imóvel
# ---------------------------------------------------------------------------

@router.get("/imoveis/novo")
async def pagina_novo_imovel(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Formulário para cadastrar novo imóvel."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="novo_imovel.html",
        context={
            "usuario": usuario,
        },
    )


@router.post("/imoveis/novo")
async def criar_imovel(
    request: Request,
    titulo: str = Form(...),
    descricao: str = Form(...),
    preco: float = Form(...),
    cidade: str = Form(...),
    bairro: str = Form(...),
    quartos: int = Form(1),
    area: float = Form(None),
    tipo_imovel: str = Form("apartamento"),
    imagens: list[UploadFile] = File(default=[]),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Cria novo imóvel com imagens e gera embedding."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Cria imóvel
    novo_imovel = Imovel(
        usuario_id=usuario.id,
        titulo=titulo,
        descricao=descricao,
        preco=preco,
        cidade=cidade,
        bairro=bairro,
        quartos=quartos,
        area=area if area and area > 0 else None,
        tipo_imovel=tipo_imovel,
    )
    db.add(novo_imovel)
    db.flush()  # Gera o ID sem commitar

    # Salva imagens
    for i, arquivo in enumerate(imagens):
        if arquivo.filename and arquivo.size > 0:
            nome_arquivo = _salvar_imagem(arquivo)
            img_db = Imagem(
                imovel_id=novo_imovel.id,
                caminho=nome_arquivo,
                ordem=i,
            )
            db.add(img_db)

    # Nota: No modelo TF-IDF, os vetores são calculados no momento da busca
    # a partir do corpus completo, então não pré-computamos embeddings aqui.

    db.commit()

    return RedirectResponse(url=f"/imoveis/{novo_imovel.id}", status_code=303)


# ---------------------------------------------------------------------------
# Detalhe do imóvel
# ---------------------------------------------------------------------------

@router.get("/imoveis/{imovel_id}")
async def detalhe_imovel(
    imovel_id: int,
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Página de detalhe de um imóvel."""
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    # Verifica se o usuário já demonstrou interesse
    ja_interessado = False
    if usuario:
        ja_interessado = db.query(Interesse).filter(
            Interesse.imovel_id == imovel_id,
            Interesse.usuario_id == usuario.id,
        ).first() is not None

    return templates.TemplateResponse(
        request=request,
        name="detalhe_imovel.html",
        context={
            "usuario": usuario,
            "imovel": imovel,
            "ja_interessado": ja_interessado,
        },
    )


# ---------------------------------------------------------------------------
# Interesse
# ---------------------------------------------------------------------------

@router.post("/imoveis/{imovel_id}/interesse")
async def registrar_interesse(
    imovel_id: int,
    request: Request,
    mensagem: str = Form(""),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Registra interesse do usuário em um imóvel."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Verifica se imóvel existe
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    # Evita duplicidade
    existente = db.query(Interesse).filter(
        Interesse.imovel_id == imovel_id,
        Interesse.usuario_id == usuario.id,
    ).first()
    if not existente:
        interesse = Interesse(
            imovel_id=imovel_id,
            usuario_id=usuario.id,
            mensagem=mensagem if mensagem else None,
        )
        db.add(interesse)
        db.commit()

    return RedirectResponse(url=f"/imoveis/{imovel_id}", status_code=303)


# ---------------------------------------------------------------------------
# Meus imóveis
# ---------------------------------------------------------------------------

@router.get("/meus-imoveis")
async def meus_imoveis(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Painel do anunciante — lista seus imóveis e interesses recebidos."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    imoveis = db.query(Imovel).filter(
        Imovel.usuario_id == usuario.id
    ).order_by(Imovel.criado_em.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="meus_imoveis.html",
        context={
            "usuario": usuario,
            "imoveis": imoveis,
        },
    )


# ---------------------------------------------------------------------------
# Editar imóvel
# ---------------------------------------------------------------------------

@router.get("/imoveis/{imovel_id}/editar")
async def pagina_editar_imovel(
    imovel_id: int,
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Formulário de edição de imóvel (somente dono)."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel or imovel.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    return templates.TemplateResponse(
        request=request,
        name="editar_imovel.html",
        context={
            "usuario": usuario,
            "imovel": imovel,
        },
    )


@router.post("/imoveis/{imovel_id}/editar")
async def atualizar_imovel(
    imovel_id: int,
    request: Request,
    titulo: str = Form(...),
    descricao: str = Form(...),
    preco: float = Form(...),
    cidade: str = Form(...),
    bairro: str = Form(...),
    quartos: int = Form(1),
    area: float = Form(None),
    tipo_imovel: str = Form("apartamento"),
    imagens: list[UploadFile] = File(default=[]),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Atualiza imóvel existente e regenera embedding."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel or imovel.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Atualiza campos
    imovel.titulo = titulo
    imovel.descricao = descricao
    imovel.preco = preco
    imovel.cidade = cidade
    imovel.bairro = bairro
    imovel.quartos = quartos
    imovel.area = area if area and area > 0 else None
    imovel.tipo_imovel = tipo_imovel

    # Salva novas imagens (adiciona às existentes)
    ordem_atual = len(imovel.imagens)
    for i, arquivo in enumerate(imagens):
        if arquivo.filename and arquivo.size > 0:
            nome_arquivo = _salvar_imagem(arquivo)
            img_db = Imagem(
                imovel_id=imovel.id,
                caminho=nome_arquivo,
                ordem=ordem_atual + i,
            )
            db.add(img_db)

    # Nota: No modelo TF-IDF, os vetores são recalculados na busca.

    db.commit()

    return RedirectResponse(url=f"/imoveis/{imovel_id}", status_code=303)


# ---------------------------------------------------------------------------
# Excluir imóvel
# ---------------------------------------------------------------------------

@router.post("/imoveis/{imovel_id}/excluir")
async def excluir_imovel(
    imovel_id: int,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Exclui imóvel (somente dono). Remove imagens do disco."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel or imovel.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Remove imagens do disco
    for img in imovel.imagens:
        caminho = UPLOAD_DIR / img.caminho
        if caminho.exists():
            os.remove(caminho)

    db.delete(imovel)
    db.commit()

    return RedirectResponse(url="/meus-imoveis", status_code=303)
