"""
Schemas Pydantic — validação de dados de formulários.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UsuarioCadastro(BaseModel):
    """Dados para cadastro de novo usuário."""
    nome: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    senha: str = Field(min_length=6, max_length=100)
    tipo_usuario: str = Field(default="proprietario")


class UsuarioLogin(BaseModel):
    """Dados para login."""
    email: str
    senha: str


class ImovelCadastro(BaseModel):
    """Dados para cadastro de imóvel."""
    titulo: str = Field(min_length=5, max_length=200)
    descricao: str = Field(min_length=20)
    preco: float = Field(gt=0)
    cidade: str = Field(min_length=2, max_length=100)
    bairro: str = Field(min_length=2, max_length=100)
    quartos: int = Field(ge=0, default=1)
    area: Optional[float] = Field(default=None, ge=0)
    tipo_imovel: str = Field(default="apartamento")


class BuscaQuery(BaseModel):
    """Parâmetros de busca."""
    q: Optional[str] = None  # busca em linguagem natural
    cidade: Optional[str] = None
    bairro: Optional[str] = None
    tipo_imovel: Optional[str] = None
    quartos_min: Optional[int] = None
    preco_min: Optional[float] = None
    preco_max: Optional[float] = None
