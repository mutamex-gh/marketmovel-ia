"""
Aplicação principal FastAPI — ponto de entrada do servidor.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routes import auth_routes, imovel_routes, busca_routes, admin_routes


from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    # Migração SQLite automática para colunas recentes
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(imoveis)")).fetchall()
            colunas = [row[1] for row in result]
            if "localizacao" not in colunas:
                conn.execute(text("ALTER TABLE imoveis ADD COLUMN localizacao VARCHAR(255)"))
            if "visualizacoes" not in colunas:
                conn.execute(text("ALTER TABLE imoveis ADD COLUMN visualizacoes INTEGER DEFAULT 0"))

            res_usr = conn.execute(text("PRAGMA table_info(usuarios)")).fetchall()
            colunas_usr = [row[1] for row in res_usr]
            if "telefone" not in colunas_usr:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN telefone VARCHAR(50)"))
            if "documento" not in colunas_usr:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN documento VARCHAR(50)"))
            if "foto_perfil" not in colunas_usr:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN foto_perfil VARCHAR(500)"))
            conn.commit()
    except Exception as e:
        print(f"Aviso na migração de banco: {e}")

    # Seed de tipos de usuário e usuário Admin padrão
    try:
        from sqlalchemy.orm import Session
        from app.models import Usuario, TipoUsuario
        from app.auth import hash_senha

        with Session(engine) as db:
            # Seed tipos de usuário
            if db.query(TipoUsuario).count() == 0:
                tipos_padrao = [
                    TipoUsuario(nome="Proprietário", slug="proprietario"),
                    TipoUsuario(nome="Corretor", slug="corretor"),
                    TipoUsuario(nome="Imobiliária", slug="imobiliaria"),
                ]
                db.add_all(tipos_padrao)
                db.commit()

            # Seed Admin
            admin_email = "admin@marketmovel.com.br"
            admin_usr = db.query(Usuario).filter(Usuario.email == admin_email).first()
            if not admin_usr:
                admin_usr = Usuario(
                    nome="Administrador",
                    email=admin_email,
                    senha_hash=hash_senha("admin"),
                    tipo_usuario="admin",
                    telefone="(49) 9 9999-9999",
                    documento="000.000.000-00",
                )
                db.add(admin_usr)
                db.commit()
            elif admin_usr.tipo_usuario != "admin":
                admin_usr.tipo_usuario = "admin"
                db.commit()
    except Exception as e:
        print(f"Aviso no seed inicial de admin/tipos: {e}")

    # Pre-carrega o modelo neural de IA na memória no startup
    try:
        from app.embeddings import obter_modelo_ia
        obter_modelo_ia()
    except Exception as e:
        print(f"Aviso no carregamento da IA: {e}")

    print("[OK] Banco de dados e Modelo de IA prontos!")
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
app.include_router(admin_routes.router)


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

