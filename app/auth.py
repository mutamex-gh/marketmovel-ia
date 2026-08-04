"""
Autenticação — hash de senhas com bcrypt e tokens JWT via cookie.
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Request, Depends
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.models import Usuario


# ---------------------------------------------------------------------------
# Senhas
# ---------------------------------------------------------------------------

def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def criar_token_jwt(dados: dict) -> str:
    """Cria token JWT com expiração."""
    payload = dados.copy()
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expira})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    """Decodifica token JWT. Retorna None se inválido ou expirado."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Dependency do FastAPI — obtém usuário logado (ou None)
# ---------------------------------------------------------------------------

async def obter_usuario_logado(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    """
    Extrai o token JWT do cookie 'access_token' e retorna o usuário.
    Retorna None se não estiver logado (não bloqueia a rota).
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = decodificar_token(token)
    if payload is None:
        return None

    usuario_id = payload.get("sub")
    if usuario_id is None:
        return None

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    return usuario
