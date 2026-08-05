"""
Rotas do Painel de Administração — exclusivo para o usuário administrador.
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario, Imovel, Interesse, Favorito, TipoUsuario
from app.auth import hash_senha, obter_usuario_logado

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

# Jinja Filters
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


def exigir_admin(usuario: Usuario = Depends(obter_usuario_logado)) -> Usuario:
    """Verifica se o usuário logado é o administrador do sistema."""
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado. Faça login.")
    if usuario.email != "admin@marketmovel.com.br" and usuario.tipo_usuario != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao administrador do sistema.")
    return usuario


# ---------------------------------------------------------------------------
# Dashboard Principal do Admin
# ---------------------------------------------------------------------------

@router.get("")
@router.get("/dashboard")
async def dashboard_admin(
    request: Request,
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Painel de controle com visão geral e estatísticas."""
    total_usuarios = db.query(Usuario).count()
    total_imoveis = db.query(Imovel).count()
    total_interesses = db.query(Interesse).count()
    total_tipos = db.query(TipoUsuario).count()

    ultimos_usuarios = db.query(Usuario).order_by(Usuario.criado_em.desc()).limit(5).all()
    ultimos_imoveis = db.query(Imovel).order_by(Imovel.criado_em.desc()).limit(5).all()
    tipos_usuario = db.query(TipoUsuario).all()

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "usuario": admin,
            "total_usuarios": total_usuarios,
            "total_imoveis": total_imoveis,
            "total_interesses": total_interesses,
            "total_tipos": total_tipos,
            "ultimos_usuarios": ultimos_usuarios,
            "ultimos_imoveis": ultimos_imoveis,
            "tipos_usuario": tipos_usuario,
        },
    )


# ---------------------------------------------------------------------------
# Gestão de Usuários
# ---------------------------------------------------------------------------

@router.get("/usuarios")
async def listar_usuarios_admin(
    request: Request,
    q: Optional[str] = None,
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Lista todos os usuários com busca e formulário de edição."""
    query = db.query(Usuario)
    if q:
        busca = f"%{q.strip()}%"
        query = query.filter(
            (Usuario.nome.ilike(busca)) |
            (Usuario.email.ilike(busca)) |
            (Usuario.telefone.ilike(busca)) |
            (Usuario.documento.ilike(busca))
        )

    usuarios = query.order_by(Usuario.id.desc()).all()
    tipos = db.query(TipoUsuario).all()

    return templates.TemplateResponse(
        request=request,
        name="admin/usuarios.html",
        context={
            "usuario": admin,
            "usuarios_lista": usuarios,
            "tipos_usuario": tipos,
            "q": q or "",
            "sucesso": request.query_params.get("sucesso"),
            "erro": request.query_params.get("erro"),
        },
    )


@router.post("/usuarios/novo")
async def criar_usuario_admin(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    telefone: Optional[str] = Form(None),
    documento: Optional[str] = Form(None),
    tipo_usuario: str = Form(...),
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Cria novo usuário via painel admin."""
    existente = db.query(Usuario).filter(Usuario.email == email.strip()).first()
    if existente:
        return RedirectResponse(url="/admin/usuarios?erro=Email+ja+cadastrado", status_code=303)

    novo_usr = Usuario(
        nome=nome.strip(),
        email=email.strip(),
        senha_hash=hash_senha(senha),
        telefone=telefone.strip() if telefone else None,
        documento=documento.strip() if documento else None,
        tipo_usuario=tipo_usuario.strip(),
    )
    db.add(novo_usr)
    db.commit()

    return RedirectResponse(url="/admin/usuarios?sucesso=Usuario+criado+com+sucesso", status_code=303)


@router.post("/usuarios/{id_usr}/editar")
async def editar_usuario_admin(
    id_usr: int,
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    telefone: Optional[str] = Form(None),
    documento: Optional[str] = Form(None),
    tipo_usuario: str = Form(...),
    nova_senha: Optional[str] = Form(None),
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Atualiza qualquer usuário no sistema."""
    usr = db.query(Usuario).filter(Usuario.id == id_usr).first()
    if not usr:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verifica duplicidade de email
    existente = db.query(Usuario).filter(Usuario.email == email.strip(), Usuario.id != id_usr).first()
    if existente:
        return RedirectResponse(url="/admin/usuarios?erro=Email+ja+em+uso+por+outro+usuario", status_code=303)

    usr.nome = nome.strip()
    usr.email = email.strip()
    usr.telefone = telefone.strip() if telefone else None
    usr.documento = documento.strip() if documento else None
    usr.tipo_usuario = tipo_usuario.strip()

    if nova_senha and len(nova_senha.strip()) >= 4:
        usr.senha_hash = hash_senha(nova_senha.strip())

    db.commit()
    return RedirectResponse(url="/admin/usuarios?sucesso=Usuario+atualizado+com+sucesso", status_code=303)


@router.post("/usuarios/{id_usr}/excluir")
async def excluir_usuario_admin(
    id_usr: int,
    request: Request,
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Exclui um usuário do sistema (protegendo a conta admin)."""
    usr = db.query(Usuario).filter(Usuario.id == id_usr).first()
    if not usr:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usr.email == "admin@marketmovel.com.br" or usr.id == admin.id:
        return RedirectResponse(url="/admin/usuarios?erro=Nao+e+permitido+excluir+o+usuario+administrador+principal", status_code=303)

    db.delete(usr)
    db.commit()
    return RedirectResponse(url="/admin/usuarios?sucesso=Usuario+excluido+com+sucesso", status_code=303)


# ---------------------------------------------------------------------------
# Gestão de Tipos de Usuários (Cadastros dinâmicos do site)
# ---------------------------------------------------------------------------

@router.get("/tipos-usuario")
async def listar_tipos_usuario_admin(
    request: Request,
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Lista todos os tipos de conta/cadastro."""
    tipos = db.query(TipoUsuario).order_by(TipoUsuario.id.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/tipos_usuario.html",
        context={
            "usuario": admin,
            "tipos_usuario": tipos,
            "sucesso": request.query_params.get("sucesso"),
            "erro": request.query_params.get("erro"),
        },
    )


@router.post("/tipos-usuario/novo")
async def cadastrar_tipo_usuario_admin(
    request: Request,
    nome: str = Form(...),
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Cadastra novo tipo de conta para ser usado no registro do site."""
    nome_limpo = nome.strip()
    if not nome_limpo:
        return RedirectResponse(url="/admin/tipos-usuario?erro=Nome+invalido", status_code=303)

    slug = nome_limpo.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ç", "c")

    existente = db.query(TipoUsuario).filter(
        (TipoUsuario.nome.ilike(nome_limpo)) | (TipoUsuario.slug == slug)
    ).first()

    if existente:
        return RedirectResponse(url="/admin/tipos-usuario?erro=Tipo+de+usuario+ja+existente", status_code=303)

    novo_tipo = TipoUsuario(nome=nome_limpo, slug=slug)
    db.add(novo_tipo)
    db.commit()

    return RedirectResponse(url="/admin/tipos-usuario?sucesso=Novo+tipo+de+conta+cadastrado+com+sucesso", status_code=303)


@router.post("/tipos-usuario/{id_tipo}/excluir")
async def excluir_tipo_usuario_admin(
    id_tipo: int,
    request: Request,
    admin: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Remove um tipo de usuário."""
    tipo = db.query(TipoUsuario).filter(TipoUsuario.id == id_tipo).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo não encontrado")

    db.delete(tipo)
    db.commit()

    return RedirectResponse(url="/admin/tipos-usuario?sucesso=Tipo+removido+com+sucesso", status_code=303)
