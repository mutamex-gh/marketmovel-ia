"""
Rotas de busca — home com busca semântica + filtros tradicionais.
"""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Usuario, Imovel
from app.auth import obter_usuario_logado
from app.embeddings import buscar_similares

router = APIRouter(tags=["busca"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(
    request: Request,
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Página inicial com campo de busca e imóveis recentes."""
    # Mostra os 12 imóveis mais recentes na home
    imoveis_recentes = db.query(Imovel).order_by(
        Imovel.criado_em.desc()
    ).limit(12).all()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "usuario": usuario,
            "imoveis": imoveis_recentes,
            "resultados": None,
            "query": "",
            "filtros": {},
        },
    )


@router.get("/buscar")
async def buscar(
    request: Request,
    q: Optional[str] = Query(default=None),
    cidade: Optional[str] = Query(default=None),
    tipo_imovel: Optional[str] = Query(default=None),
    quartos_min: Optional[str] = Query(default=None),
    preco_min: Optional[str] = Query(default=None),
    preco_max: Optional[str] = Query(default=None),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """
    Busca combinando filtros SQL + busca semântica por IA.
    """
    # Funções de conversão segura para evitar erro 422 com strings vazias
    def _parse_int(val: Optional[str]) -> Optional[int]:
        if not val or not str(val).strip():
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def _parse_float(val: Optional[str]) -> Optional[float]:
        if not val or not str(val).strip():
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    q_num_quartos = _parse_int(quartos_min)
    q_preco_min = _parse_float(preco_min)
    q_preco_max = _parse_float(preco_max)

    # Monta query base
    query_db = db.query(Imovel)

    # Filtros tradicionais
    filtros = {}
    if cidade and cidade.strip():
        query_db = query_db.filter(Imovel.cidade.ilike(f"%{cidade.strip()}%"))
        filtros["cidade"] = cidade.strip()
    if tipo_imovel and tipo_imovel.strip():
        query_db = query_db.filter(Imovel.tipo_imovel == tipo_imovel.strip())
        filtros["tipo_imovel"] = tipo_imovel.strip()
    if q_num_quartos is not None and q_num_quartos > 0:
        query_db = query_db.filter(Imovel.quartos >= q_num_quartos)
        filtros["quartos_min"] = q_num_quartos
    if q_preco_min is not None and q_preco_min > 0:
        query_db = query_db.filter(Imovel.preco >= q_preco_min)
        filtros["preco_min"] = q_preco_min
    if q_preco_max is not None and q_preco_max > 0:
        query_db = query_db.filter(Imovel.preco <= q_preco_max)
        filtros["preco_max"] = q_preco_max

    imoveis_filtrados = query_db.all()

    # Busca semântica
    resultados = []
    if q and q.strip():
        # Busca por similaridade TF-IDF entre a query e os imóveis filtrados
        resultados_com_score = buscar_similares(q.strip(), imoveis_filtrados, top_k=20)
        resultados = [
            {"imovel": imovel, "score": round(score * 100, 1)}
            for imovel, score in resultados_com_score
        ]
    else:
        # Sem busca semântica, ordena por data
        resultados = [
            {"imovel": imovel, "score": None}
            for imovel in sorted(imoveis_filtrados, key=lambda x: x.criado_em, reverse=True)
        ]

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "usuario": usuario,
            "imoveis": None,
            "resultados": resultados,
            "query": q or "",
            "filtros": filtros,
        },
    )
