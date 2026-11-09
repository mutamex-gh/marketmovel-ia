"""
Dependências de AUTENTICAÇÃO e AUTORIZAÇÃO da API REST.

- Autenticação: token JWT enviado no header `Authorization: Bearer <token>`.
- Autorização : papéis (admin x usuário comum) e regra de "dono do recurso".
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth import decodificar_token
from app.database import get_db
from app.models import Usuario

# auto_error=False para podermos devolver nossa própria mensagem 401
bearer_scheme = HTTPBearer(auto_error=False)


def _usuario_do_token(
    credenciais: Optional[HTTPAuthorizationCredentials],
    db: Session,
) -> Optional[Usuario]:
    if credenciais is None or not credenciais.credentials:
        return None
    payload = decodificar_token(credenciais.credentials)
    if not payload or payload.get("sub") is None:
        return None
    return db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()


def usuario_autenticado(
    credenciais: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """AUTENTICAÇÃO: exige um token JWT válido. Caso contrário -> 401."""
    usuario = _usuario_do_token(credenciais, db)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Envie um token válido em 'Authorization: Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def usuario_opcional(
    credenciais: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    """Retorna o usuário se houver token válido, ou None (rotas públicas)."""
    return _usuario_do_token(credenciais, db)


def exigir_admin(usuario: Usuario = Depends(usuario_autenticado)) -> Usuario:
    """AUTORIZAÇÃO: somente usuários com papel 'admin'. Caso contrário -> 403."""
    if usuario.tipo_usuario != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem executar esta ação.",
        )
    return usuario


def eh_admin(usuario: Optional[Usuario]) -> bool:
    return usuario is not None and usuario.tipo_usuario == "admin"


def verificar_dono_ou_admin(usuario: Usuario, dono_id: int) -> None:
    """AUTORIZAÇÃO: só o dono do recurso ou um admin pode alterar/excluir -> 403."""
    if usuario.id != dono_id and not eh_admin(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Você só pode alterar recursos que pertencem a você.",
        )

