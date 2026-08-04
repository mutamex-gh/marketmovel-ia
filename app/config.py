"""
Configurações do projeto.
Carrega variáveis de ambiente do arquivo .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Segurança
SECRET_KEY = os.getenv("SECRET_KEY", "chave-padrao-insegura-trocar-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./marketplace.db")

# Uploads
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Tamanho máximo de imagem (largura) para redimensionar
MAX_IMAGE_WIDTH = 1200
