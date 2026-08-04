"""
Aplicação principal FastAPI — ponto de entrada do servidor.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routes import auth_routes, imovel_routes, busca_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Evento de startup: cria tabelas no banco se não existirem.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado!")
    yield


# Cria app FastAPI
app = FastAPI(
    title="Marketplace de Imóveis",
    description="MVP acadêmico — busca inteligente de imóveis com IA",
    version="1.0.0",
    lifespan=lifespan,
)

# Arquivos estáticos (CSS, JS, uploads de imagens)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclui routers
app.include_router(busca_routes.router)
app.include_router(auth_routes.router)
app.include_router(imovel_routes.router)


# ---------------------------------------------------------------------------
# Página de erro 404 customizada
# ---------------------------------------------------------------------------

templates = Jinja2Templates(directory="templates")


@app.exception_handler(404)
async def pagina_nao_encontrada(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "usuario": None,
            "erro_404": True,
        },
        status_code=404,
    )

