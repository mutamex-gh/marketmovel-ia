"""
Rotas de autenticação — login, cadastro e logout.
"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.auth import hash_senha, verificar_senha, criar_token_jwt, obter_usuario_logado

router = APIRouter(tags=["autenticação"])
templates = Jinja2Templates(directory="templates")


@router.get("/cadastro")
async def pagina_cadastro(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Renderiza formulário de cadastro de usuário."""
    if usuario:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="cadastro.html",
        context={
            "usuario": usuario,
        },
    )


@router.post("/cadastro")
async def criar_conta(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    tipo_usuario: str = Form("proprietario"),
    db: Session = Depends(get_db),
):
    """Cria nova conta de usuário."""
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
