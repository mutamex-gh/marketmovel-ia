"""
Configuração do banco de dados SQLAlchemy com SQLite.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL

# connect_args necessário para SQLite permitir uso em múltiplas threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base para todos os modelos SQLAlchemy."""
    pass


def get_db():
    """
    Dependency do FastAPI que fornece uma sessão do banco.
    Garante que a sessão é fechada após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
