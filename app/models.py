"""
Modelos SQLAlchemy — representam as tabelas do banco de dados.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class Usuario(Base):
    """Usuário do sistema (corretor, imobiliária ou proprietário)."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    tipo_usuario = Column(String(50), default="proprietario")  # proprietario, corretor, imobiliaria
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    imoveis = relationship("Imovel", back_populates="proprietario", cascade="all, delete-orphan")
    interesses = relationship("Interesse", back_populates="usuario", cascade="all, delete-orphan")


class Imovel(Base):
    """Imóvel cadastrado no marketplace."""
    __tablename__ = "imoveis"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=False)
    preco = Column(Float, nullable=False)
    cidade = Column(String(100), nullable=False)
    bairro = Column(String(100), nullable=False)
    localizacao = Column(String(255), nullable=True)  # Endereço exato / localização detalhada
    quartos = Column(Integer, default=1)
    area = Column(Float, nullable=True)  # metros quadrados
    tipo_imovel = Column(String(50), nullable=False)  # apartamento, casa, cobertura, terreno, comercial
    embedding = Column(Text, nullable=True)  # JSON serializado do vetor de embedding
    visualizacoes = Column(Integer, default=0)  # Contador de acessos ao imóvel
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    proprietario = relationship("Usuario", back_populates="imoveis")
    imagens = relationship("Imagem", back_populates="imovel", cascade="all, delete-orphan")
    interesses = relationship("Interesse", back_populates="imovel", cascade="all, delete-orphan")


class Imagem(Base):
    """Imagem associada a um imóvel."""
    __tablename__ = "imagens"

    id = Column(Integer, primary_key=True, index=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False)
    caminho = Column(String(500), nullable=False)  # caminho relativo em static/uploads/
    ordem = Column(Integer, default=0)

    # Relacionamento
    imovel = relationship("Imovel", back_populates="imagens")


class Interesse(Base):
    """Registro de interesse de um usuário em um imóvel."""
    __tablename__ = "interesses"

    id = Column(Integer, primary_key=True, index=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensagem = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    imovel = relationship("Imovel", back_populates="interesses")
    usuario = relationship("Usuario", back_populates="interesses")
