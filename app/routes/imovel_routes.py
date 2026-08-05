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
from app.models import Usuario, Imovel, Imagem, Interesse, Favorito
from app.auth import obter_usuario_logado
from app.config import UPLOAD_DIR, MAX_IMAGE_WIDTH
from app.embeddings import montar_texto_imovel, gerar_embedding, embedding_para_json, buscar_imoveis_similares_por_imovel


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
    localizacao: str = Form(None),
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

    # Validação OBRIGATÓRIA: Envio de pelo menos 1 foto para publicar o imóvel
    imagens_validas = [img for img in imagens if img and img.filename and img.filename.strip() and img.size > 0]
    if not imagens_validas:
        return templates.TemplateResponse(
            request=request,
            name="novo_imovel.html",
            context={
                "usuario": usuario,
                "erro": "É obrigatório enviar pelo menos 1 foto para publicar o anúncio.",
                "titulo": titulo,
                "descricao": descricao,
                "preco": preco,
                "cidade": cidade,
                "bairro": bairro,
                "localizacao": localizacao,
                "quartos": quartos,
                "area": area,
                "tipo_imovel": tipo_imovel,
            },
        )

    # Cria imóvel
    novo_imovel = Imovel(
        usuario_id=usuario.id,
        titulo=titulo,
        descricao=descricao,
        preco=preco,
        cidade=cidade,
        bairro=bairro,
        localizacao=localizacao.strip() if localizacao else None,
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

    # Gera embedding vetorial para busca semântica instantânea por IA
    vetor = gerar_embedding(montar_texto_imovel(novo_imovel))
    if vetor:
        novo_imovel.embedding = embedding_para_json(vetor)

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

    # Incrementar contador de visualizações
    imovel.visualizacoes = (imovel.visualizacoes or 0) + 1
    db.commit()

    # Verifica status de favorito e interesse do usuário
    eh_favorito = False
    ja_interessado = False
    dados_completos = False
    if usuario:
        eh_favorito = db.query(Favorito).filter(
            Favorito.imovel_id == imovel_id,
            Favorito.usuario_id == usuario.id,
        ).first() is not None

        ja_interessado = db.query(Interesse).filter(
            Interesse.imovel_id == imovel_id,
            Interesse.usuario_id == usuario.id,
        ).first() is not None

        dados_completos = bool(usuario.telefone and usuario.documento)

    # Busca imóveis similares recomendados por IA
    todos_imoveis = db.query(Imovel).all()
    similares = buscar_imoveis_similares_por_imovel(imovel, todos_imoveis, top_k=4)

    return templates.TemplateResponse(
        request=request,
        name="detalhe_imovel.html",
        context={
            "usuario": usuario,
            "imovel": imovel,
            "ja_interessado": ja_interessado,
            "eh_favorito": eh_favorito,
            "dados_completos": dados_completos,
            "erro_dados": request.query_params.get("erro_dados") == "1",
            "similares": similares,
        },
    )


# ---------------------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------------------

@router.post("/imoveis/{imovel_id}/favoritar")
async def favoritar_imovel(
    imovel_id: int,
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Alterna o status de favorito de um imóvel."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    fav = db.query(Favorito).filter(
        Favorito.imovel_id == imovel_id,
        Favorito.usuario_id == usuario.id
    ).first()

    if fav:
        db.delete(fav)
        db.commit()
    else:
        novo_fav = Favorito(imovel_id=imovel_id, usuario_id=usuario.id)
        db.add(novo_fav)
        db.commit()

    referer = request.headers.get("referer")
    if referer:
        return RedirectResponse(url=referer, status_code=303)
    return RedirectResponse(url=f"/imoveis/{imovel_id}", status_code=303)


@router.get("/favoritos")
async def listar_favoritos(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Lista todos os imóveis favoritados pelo usuário logado."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    favs = db.query(Favorito).filter(Favorito.usuario_id == usuario.id).order_by(Favorito.criado_em.desc()).all()
    imoveis = [f.imovel for f in favs if f.imovel]

    return templates.TemplateResponse(
        request=request,
        name="favoritos.html",
        context={
            "usuario": usuario,
            "imoveis": imoveis,
        },
    )


# ---------------------------------------------------------------------------
# Interesse
# ---------------------------------------------------------------------------

@router.post("/imoveis/{imovel_id}/interesse")
async def registrar_interesse(
    imovel_id: int,
    request: Request,
    mensagem: str = Form(...),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Registra interesse do usuário em um imóvel com mensagem obrigatória."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Requisito OBRIGATÓRIO: Para registrar interesse, precisa ter Telefone (WhatsApp) e Documento (CPF/CNPJ)!
    if not usuario.telefone or not usuario.documento:
        return RedirectResponse(url=f"/imoveis/{imovel_id}?erro_dados=1", status_code=303)

    # Verifica se imóvel existe
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    msg_texto = mensagem.strip() if mensagem else ""
    if not msg_texto:
        msg_texto = "Olá! Demonstrei interesse no seu imóvel e gostaria de entrar em contato."

    # Evita duplicidade
    existente = db.query(Interesse).filter(
        Interesse.imovel_id == imovel_id,
        Interesse.usuario_id == usuario.id,
    ).first()
    if not existente:
        interesse = Interesse(
            imovel_id=imovel_id,
            usuario_id=usuario.id,
            mensagem=msg_texto,
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
    localizacao: str = Form(None),
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
    imovel.localizacao = localizacao.strip() if localizacao else None
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

    # Regenera o embedding vetorial do imóvel atualizado
    vetor = gerar_embedding(montar_texto_imovel(imovel))
    if vetor:
        imovel.embedding = embedding_para_json(vetor)

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


@router.post("/imoveis/{imovel_id}/imagens/{imagem_id}/excluir")
async def excluir_imagem(
    imovel_id: int,
    imagem_id: int,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Remove uma imagem específica de um imóvel (somente dono)."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel or imovel.usuario_id != usuario.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    imagem = db.query(Imagem).filter(
        Imagem.id == imagem_id,
        Imagem.imovel_id == imovel_id
    ).first()

    if imagem:
        caminho = UPLOAD_DIR / imagem.caminho
        if caminho.exists():
            try:
                os.remove(caminho)
            except Exception:
                pass
        db.delete(imagem)
        db.commit()

    return RedirectResponse(url=f"/imoveis/{imovel_id}/editar", status_code=303)

