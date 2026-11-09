"""
API REST (JSON) do MarketMóvel IA — versão 1.

Todas as rotas ficam sob o prefixo /api/v1 e usam autenticação via
token JWT no header:  Authorization: Bearer <token>
"""
from fastapi import APIRouter

from app.api import (
    auth_api,
    usuarios_api,
    tipos_usuario_api,
    imoveis_api,
    imagens_api,
    interesses_api,
    favoritos_api,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_api.router)
api_router.include_router(usuarios_api.router)
api_router.include_router(tipos_usuario_api.router)
api_router.include_router(imoveis_api.router)
api_router.include_router(imagens_api.router)
api_router.include_router(interesses_api.router)
api_router.include_router(favoritos_api.router)

