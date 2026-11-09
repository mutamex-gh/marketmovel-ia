"""
Resource: USUÁRIOS — CRUD.

Autorização:
- Listar / criar usuários ............ somente ADMIN
- Ver / editar / excluir um usuário .. o próprio usuário ou ADMIN
- Alterar o papel (tipo_usuario) ..... somente ADMIN
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import hash_senha
from app.database import get_db
from app.models import Usuario
from app.api.deps import usuario_autenticado, exigir_admin, verificar_dono_ou_admin, eh_admin
from app.api.schemas_api import UsuarioOut, UsuarioCreateAdmin, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _buscar_usuario(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
    return usuario


@router.get("", response_model=List[UsuarioOut])
def listar_usuarios(
    tipo_usuario: Optional[str] = Query(None, description="Filtra por tipo (ex: corretor)"),
    q: Optional[str] = Query(None, description="Busca por nome ou e-mail"),
    _: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Lista todos os usuários (ADMIN)."""
    query = db.query(Usuario)
    if tipo_usuario:
        query = query.filter(Usuario.tipo_usuario == tipo_usuario)
    if q:
        like = f"%{q}%"
        query = query.filter((Usuario.nome.ilike(like)) | (Usuario.email.ilike(like)))
    return query.order_by(Usuario.id).all()


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: UsuarioCreateAdmin,
    _: Usuario = Depends(exigir_admin),
    db: Session = Depends(get_db),
):
    """Cria um usuário de qualquer tipo, inclusive admin (ADMIN)."""
    email = dados.email.strip().lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com este e-mail.")
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
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obter_usuario(
    usuario_id: int,
    atual: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Detalhe de um usuário (o próprio ou ADMIN)."""
    verificar_dono_ou_admin(atual, usuario_id)
    return _buscar_usuario(db, usuario_id)


@router.put("/{usuario_id}", response_model=UsuarioOut)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioUpdate,
    atual: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Atualiza dados do usuário (o próprio ou ADMIN). Envie só os campos a alterar."""
    verificar_dono_ou_admin(atual, usuario_id)
    usuario = _buscar_usuario(db, usuario_id)
    campos = dados.model_dump(exclude_unset=True)

    if "tipo_usuario" in campos and not eh_admin(atual):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas administradores podem alterar o tipo de usuário.")

    if "email" in campos and campos["email"]:
        novo_email = campos["email"].strip().lower()
        existe = db.query(Usuario).filter(Usuario.email == novo_email, Usuario.id != usuario_id).first()
        if existe:
            raise HTTPException(status.HTTP_409_CONFLICT, "Este e-mail já está em uso.")
        campos["email"] = novo_email

    if "senha" in campos:
        senha = campos.pop("senha")
        if senha:
            usuario.senha_hash = hash_senha(senha)

    for campo, valor in campos.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuario(
    usuario_id: int,
    atual: Usuario = Depends(usuario_autenticado),
    db: Session = Depends(get_db),
):
    """Exclui o usuário e, em cascata, seus imóveis/favoritos/interesses (o próprio ou ADMIN)."""
    verificar_dono_ou_admin(atual, usuario_id)
    usuario = _buscar_usuario(db, usuario_id)
    if usuario.email == "admin@marketmovel.com.br":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O administrador padrão não pode ser excluído.")
    db.delete(usuario)
    db.commit()

