import uuid
from pathlib import Path
from PIL import Image as PILImage
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario, Imovel, Interesse, TipoUsuario
from app.auth import hash_senha, verificar_senha, criar_token_jwt, obter_usuario_logado
from app.config import UPLOAD_DIR

router = APIRouter(tags=["autenticação"])
templates = Jinja2Templates(directory="templates")


def formatar_telefone_filter(val):
    if not val:
        return ""
    nums = "".join([c for c in str(val) if c.isdigit()])
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2]} {nums[3:7]}-{nums[7:]}"
    elif len(nums) == 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return val


def formatar_documento_filter(val):
    if not val:
        return ""
    nums = "".join([c for c in str(val) if c.isdigit()])
    if len(nums) == 11:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"
    elif len(nums) == 14:
        return f"{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:]}"
    return val


templates.env.filters["formatar_telefone"] = formatar_telefone_filter
templates.env.filters["formatar_documento"] = formatar_documento_filter


def _salvar_foto_perfil(arquivo: UploadFile) -> str:
    """Salva a foto de perfil recortada em 300x300px em static/uploads/perfil/."""
    dir_perfil = UPLOAD_DIR / "perfil"
    dir_perfil.mkdir(parents=True, exist_ok=True)

    extensao = Path(arquivo.filename).suffix.lower() if arquivo.filename else ".jpg"
    if extensao not in (".jpg", ".jpeg", ".png", ".webp"):
        extensao = ".jpg"
    nome_arquivo = f"perfil_{uuid.uuid4().hex[:10]}{extensao}"
    caminho_completo = dir_perfil / nome_arquivo

    img = PILImage.open(arquivo.file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Crop quadrado centralizado
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) / 2
    top = (h - min_dim) / 2
    right = (w + min_dim) / 2
    bottom = (h + min_dim) / 2

    img = img.crop((left, top, right, bottom))
    img = img.resize((300, 300), PILImage.LANCZOS)
    img.save(caminho_completo, quality=90)

    return f"perfil/{nome_arquivo}"


@router.post("/perfil/foto")
async def atualizar_foto_perfil(
    request: Request,
    foto: UploadFile = File(...),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Upload instantâneo de foto de perfil via AJAX (ao passar o mouse / clicar no avatar)."""
    if not usuario:
        return JSONResponse(status_code=401, content={"erro": "Não autorizado", "redirect": "/login"})

    if not foto or not foto.filename or not foto.filename.strip() or foto.size == 0:
        return JSONResponse(status_code=400, content={"erro": "Nenhuma imagem selecionada."})

    caminho_rel = _salvar_foto_perfil(foto)
    usuario.foto_perfil = caminho_rel
    db.commit()

    return JSONResponse(content={
        "sucesso": True,
        "foto_url": f"/static/uploads/{caminho_rel}"
    })


@router.post("/perfil/editar")
async def editar_perfil(
    request: Request,
    nome: str = Form(...),
    telefone: str = Form(...),
    documento: str = Form(None),
    foto: UploadFile = File(default=None),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Atualiza dados do perfil e foto de avatar do usuário."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    usuario.nome = nome.strip()
    usuario.telefone = telefone.strip() if telefone else None
    usuario.documento = documento.strip() if documento else None

    # Salva foto se enviada
    if foto and foto.filename and foto.filename.strip() and foto.size > 0:
        caminho_rel = _salvar_foto_perfil(foto)
        usuario.foto_perfil = caminho_rel

    db.commit()

    return RedirectResponse(url="/perfil?salvo=ok", status_code=303)


@router.get("/perfil")
@router.get("/dashboard")
async def pagina_perfil(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Página de perfil / dashboard do usuário com métricas e histórico."""
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    # Imóveis anunciados pelo usuário
    imoveis = db.query(Imovel).filter(
        Imovel.usuario_id == usuario.id
    ).order_by(Imovel.criado_em.desc()).all()

    # Métricas agregadas
    total_imoveis = len(imoveis)
    total_visualizacoes = sum(im.visualizacoes or 0 for im in imoveis)

    # Interesses recebidos nos imóveis pertencentes ao usuário
    imoveis_ids = [im.id for im in imoveis]
    interesses_recebidos = []
    if imoveis_ids:
        interesses_recebidos = db.query(Interesse).filter(
            Interesse.imovel_id.in_(imoveis_ids)
        ).order_by(Interesse.criado_em.desc()).all()

    # Interesses demonstrados pelo próprio usuário (enviados)
    meus_interesses = db.query(Interesse).filter(
        Interesse.usuario_id == usuario.id
    ).order_by(Interesse.criado_em.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="perfil.html",
        context={
            "usuario": usuario,
            "imoveis": imoveis,
            "total_imoveis": total_imoveis,
            "total_visualizacoes": total_visualizacoes,
            "interesses_recebidos": interesses_recebidos,
            "meus_interesses": meus_interesses,
        },
    )


@router.get("/cadastro")
async def pagina_cadastro(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Renderiza formulário de cadastro de usuário."""
    if usuario:
        return RedirectResponse(url="/", status_code=303)

    tipos_usuario = db.query(TipoUsuario).order_by(TipoUsuario.nome.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="cadastro.html",
        context={
            "usuario": usuario,
            "tipos_usuario": tipos_usuario,
        },
    )


@router.post("/cadastro")
async def criar_conta(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    telefone: str = Form(...),
    documento: str = Form(None),
    tipo_usuario: str = Form("proprietario"),
    db: Session = Depends(get_db),
):
    """Cria nova conta de usuário."""
    # Validação do Telefone/WhatsApp (Obrigatório)
    if not telefone or not telefone.strip():
        return templates.TemplateResponse(
            request=request,
            name="cadastro.html",
            context={
                "usuario": None,
                "erro": "O campo Telefone (WhatsApp) é obrigatório.",
            },
        )

    # Verifica se email já existe
    existente = db.query(Usuario).filter(Usuario.email == email).first()
    if existente:
        return templates.TemplateResponse(
            request=request,
            name="cadastro.html",
            context={
                "usuario": None,
                "erro": "Este email já está cadastrado.",
            },
        )

    # Validação simples da senha
    if len(senha) < 6:
        return templates.TemplateResponse(
            request=request,
            name="cadastro.html",
            context={
                "usuario": None,
                "erro": "A senha deve ter pelo menos 6 caracteres.",
            },
        )

    # Cria usuário
    novo_usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_senha(senha),
        telefone=telefone.strip() if telefone else None,
        documento=documento.strip() if documento else None,
        tipo_usuario=tipo_usuario,
    )
    db.add(novo_usuario)
    db.commit()

    return RedirectResponse(url="/login?cadastro=ok", status_code=303)



@router.get("/login")
async def pagina_login(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Renderiza formulário de login."""
    if usuario:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "usuario": usuario,
            "cadastro_ok": request.query_params.get("cadastro") == "ok",
        },
    )


@router.post("/login")
async def fazer_login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    """Autentica usuário e define cookie JWT."""
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "usuario": None,
                "erro": "Email ou senha incorretos.",
            },
        )

    # Cria token JWT
    token = criar_token_jwt({"sub": str(usuario.id)})

    # Redireciona com cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,  # 24 horas
        samesite="lax",
    )
    return response


@router.get("/logout")
async def fazer_logout():
    """Remove cookie de autenticação e redireciona para home."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response
