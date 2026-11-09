"""
Resource: AUTH — registro, login (gera JWT) e dados do usuário logado.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import hash_senha, verificar_senha, criar_token_jwt
from app.database import get_db
from app.models import Usuario, TipoUsuario
from app.api.deps import usuario_autenticado
from app.api.schemas_api import RegistroIn, LoginIn, TokenOut, UsuarioOut

router = APIRouter(prefix="/auth", tags=["Auth"])


def _tipos_validos(db: Session) -> set[str]:
    slugs = {t.slug for t in db.query(TipoUsuario).all()}
    return slugs or {"proprietario", "corretor", "imobiliaria"}


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def registrar(dados: RegistroIn, db: Session = Depends(get_db)):
    """Cria uma conta (público). Não é possível se registrar como 'admin'."""
    email = dados.email.strip().lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com este e-mail.")

    if dados.tipo_usuario not in _tipos_validos(db):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"tipo_usuario inválido. Use um destes: {sorted(_tipos_validos(db))}",
        )

    usuario = Usuario(
        nome=dados.nome.strip(),
        email=email,
        senha_hash=hash_senha(dados.senha),
        telefone=dados.telefone,
        documento=dados.documento,
        tipo_usuario=dados.tipo_usuario,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = criar_token_jwt({"sub": str(usuario.id)})
    return TokenOut(access_token=token, usuario=UsuarioOut.model_validate(usuario))


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn, db: Session = Depends(get_db)):
    """Autentica com e-mail e senha e devolve um token JWT (válido por 24h)."""
    usuario = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")

    token = criar_token_jwt({"sub": str(usuario.id)})
    return TokenOut(access_token=token, usuario=UsuarioOut.model_validate(usuario))


@router.get("/me", response_model=UsuarioOut)
def meus_dados(usuario: Usuario = Depends(usuario_autenticado)):
    """Retorna os dados do usuário dono do token."""
    return usuario

