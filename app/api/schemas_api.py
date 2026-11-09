"""
Schemas Pydantic (entrada e saída JSON) da API REST.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

class RegistroIn(BaseModel):
    nome: str = Field(min_length=2, max_length=150, examples=["Maria Silva"])
    email: str = Field(min_length=5, max_length=255, examples=["maria@email.com"])
    senha: str = Field(min_length=6, max_length=100, examples=["123456"])
    telefone: Optional[str] = Field(default=None, examples=["(49) 99999-0000"])
    documento: Optional[str] = Field(default=None, examples=["123.456.789-00"])
    tipo_usuario: str = Field(default="proprietario", examples=["proprietario"])


class LoginIn(BaseModel):
    email: str = Field(examples=["admin@marketmovel.com.br"])
    senha: str = Field(examples=["admin"])


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------

class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    telefone: Optional[str] = None
    documento: Optional[str] = None
    tipo_usuario: Optional[str] = None
    foto_perfil: Optional[str] = None
    criado_em: Optional[datetime] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class UsuarioCreateAdmin(RegistroIn):
    """Admin pode criar usuários de qualquer tipo, inclusive 'admin'."""
    pass


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=2, max_length=150)
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    senha: Optional[str] = Field(default=None, min_length=6, max_length=100)
    telefone: Optional[str] = None
    documento: Optional[str] = None
    tipo_usuario: Optional[str] = Field(
        default=None, description="Apenas administradores podem alterar o tipo/papel."
    )


# ---------------------------------------------------------------------------
# Tipos de usuário
# ---------------------------------------------------------------------------

class TipoUsuarioIn(BaseModel):
    nome: str = Field(min_length=2, max_length=100, examples=["Construtora"])
    slug: Optional[str] = Field(default=None, max_length=100, examples=["construtora"])


class TipoUsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str
    criado_em: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Imagens
# ---------------------------------------------------------------------------

class ImagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    imovel_id: int
    caminho: str
    ordem: Optional[int] = 0

    @computed_field
    @property
    def url(self) -> str:
        return f"/static/uploads/{self.caminho}"


# ---------------------------------------------------------------------------
# Imóveis
# ---------------------------------------------------------------------------

class ImovelBase(BaseModel):
    titulo: str = Field(min_length=5, max_length=200, examples=["Apartamento 2 quartos no Centro"])
    descricao: str = Field(min_length=20, examples=["Lindo apartamento com sacada, churrasqueira e 1 vaga de garagem."])
    preco: float = Field(gt=0, examples=[350000])
    cidade: str = Field(min_length=2, max_length=100, examples=["Chapecó"])
    bairro: str = Field(min_length=2, max_length=100, examples=["Centro"])
    localizacao: Optional[str] = Field(default=None, max_length=255)
    quartos: int = Field(default=1, ge=0)
    area: Optional[float] = Field(default=None, ge=0)
    banheiros: Optional[int] = Field(default=None, ge=0)
    suites: Optional[int] = Field(default=None, ge=0)
    vagas_garagem: Optional[int] = Field(default=None, ge=0)
    area_construida: Optional[float] = Field(default=None, ge=0)
    andar: Optional[int] = Field(default=None, ge=0)
    aceita_pets: bool = False
    mobiliado: Literal["nao", "semi", "completo"] = "nao"
    condominio: Optional[float] = Field(default=None, ge=0)
    iptu: Optional[float] = Field(default=None, ge=0)
    finalidade: Literal["venda", "aluguel"] = "venda"
    tipo_imovel: str = Field(default="apartamento", max_length=50)


class ImovelCreate(ImovelBase):
    pass


class ImovelUpdate(BaseModel):
    """Atualização parcial (PATCH/PUT) — envie apenas os campos a alterar."""
    titulo: Optional[str] = Field(default=None, min_length=5, max_length=200)
    descricao: Optional[str] = Field(default=None, min_length=20)
    preco: Optional[float] = Field(default=None, gt=0)
    cidade: Optional[str] = Field(default=None, min_length=2, max_length=100)
    bairro: Optional[str] = Field(default=None, min_length=2, max_length=100)
    localizacao: Optional[str] = None
    quartos: Optional[int] = Field(default=None, ge=0)
    area: Optional[float] = Field(default=None, ge=0)
    banheiros: Optional[int] = Field(default=None, ge=0)
    suites: Optional[int] = Field(default=None, ge=0)
    vagas_garagem: Optional[int] = Field(default=None, ge=0)
    area_construida: Optional[float] = Field(default=None, ge=0)
    andar: Optional[int] = Field(default=None, ge=0)
    aceita_pets: Optional[bool] = None
    mobiliado: Optional[Literal["nao", "semi", "completo"]] = None
    condominio: Optional[float] = Field(default=None, ge=0)
    iptu: Optional[float] = Field(default=None, ge=0)
    finalidade: Optional[Literal["venda", "aluguel"]] = None
    tipo_imovel: Optional[str] = Field(default=None, max_length=50)


class ProprietarioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: Optional[str] = None
    tipo_usuario: Optional[str] = None


class ImovelOut(BaseModel):
    """Saída sem restrições de validação (aceita dados legados do banco)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    titulo: str
    descricao: str
    preco: float
    cidade: str
    bairro: str
    localizacao: Optional[str] = None
    quartos: Optional[int] = None
    area: Optional[float] = None
    banheiros: Optional[int] = None
    suites: Optional[int] = None
    vagas_garagem: Optional[int] = None
    area_construida: Optional[float] = None
    andar: Optional[int] = None
    aceita_pets: Optional[bool] = False
    mobiliado: Optional[str] = "nao"
    condominio: Optional[float] = None
    iptu: Optional[float] = None
    finalidade: Optional[str] = "venda"
    tipo_imovel: str
    visualizacoes: Optional[int] = 0
    criado_em: Optional[datetime] = None
    proprietario: Optional[ProprietarioResumo] = None
    imagens: List[ImagemOut] = []


class ImovelBuscaOut(BaseModel):
    score: float
    imovel: ImovelOut


class PaginaImoveis(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    itens: List[ImovelOut]


# ---------------------------------------------------------------------------
# Interesses
# ---------------------------------------------------------------------------

class InteresseIn(BaseModel):
    imovel_id: int = Field(examples=[1])
    mensagem: Optional[str] = Field(default=None, max_length=2000, examples=["Tenho interesse, podemos agendar uma visita?"])


class InteresseUpdate(BaseModel):
    mensagem: str = Field(min_length=1, max_length=2000)


class InteresseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    imovel_id: int
    usuario_id: int
    mensagem: Optional[str] = None
    criado_em: Optional[datetime] = None
    usuario: Optional[ProprietarioResumo] = None


# ---------------------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------------------

class FavoritoIn(BaseModel):
    imovel_id: int = Field(examples=[1])


class ImovelResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    preco: float
    cidade: str
    bairro: str
    tipo_imovel: str


class FavoritoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    imovel_id: int
    usuario_id: int
    criado_em: Optional[datetime] = None
    imovel: Optional[ImovelResumo] = None


class MensagemOut(BaseModel):
    detail: str
