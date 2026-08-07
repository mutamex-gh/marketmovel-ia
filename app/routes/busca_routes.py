import math
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario, Imovel
from app.auth import obter_usuario_logado
from app.embeddings import buscar_similares

router = APIRouter(tags=["busca"])
templates = Jinja2Templates(directory="templates")

PER_PAGE = 12


def calcular_intervalo_paginas(pagina: int, total_paginas: int) -> list:
    """
    Gera lista de páginas inteligentes com reticências '...' para muitas páginas.
    Ex: [1, 2, 3, '...', 30] ou [1, '...', 14, 15, 16, '...', 30]
    """
    if total_paginas <= 7:
        return list(range(1, total_paginas + 1))

    paginas = set([1, total_paginas])
    for p in range(pagina - 2, pagina + 3):
        if 1 <= p <= total_paginas:
            paginas.add(p)

    resultado = []
    ultimo = 0
    for p in sorted(list(paginas)):
        if ultimo > 0 and p - ultimo > 1:
            resultado.append("...")
        resultado.append(p)
        ultimo = p

    return resultado


@router.get("/")
async def home(
    request: Request,
    pagina: int = Query(default=1, ge=1),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """Página inicial com lista paginada de imóveis recentes."""
    total_imoveis = db.query(Imovel).count()
    num_paginas = math.ceil(total_imoveis / PER_PAGE) if total_imoveis > 0 else 1
    pagina = min(max(1, pagina), num_paginas)

    offset = (pagina - 1) * PER_PAGE
    imoveis_recentes = db.query(Imovel).order_by(
        Imovel.criado_em.desc()
    ).offset(offset).limit(PER_PAGE).all()

    intervalo_paginas = calcular_intervalo_paginas(pagina, num_paginas)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "usuario": usuario,
            "imoveis": imoveis_recentes,
            "resultados": None,
            "query": "",
            "filtros": {},
            "pagina": pagina,
            "num_paginas": num_paginas,
            "intervalo_paginas": intervalo_paginas,
            "total_imoveis": total_imoveis,
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
    pagina: int = Query(default=1, ge=1),
    usuario: Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db),
):
    """
    Busca combinando filtros SQL + busca semântica por IA com paginação.
    """
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

    # Query base
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

    # Busca semântica por IA
    resultados_todos = []
    if q and q.strip():
        resultados_com_score = buscar_similares(q.strip(), imoveis_filtrados, top_k=len(imoveis_filtrados))
        resultados_todos = [
            {"imovel": imovel, "score": round(score * 100, 1)}
            for imovel, score in resultados_com_score
        ]
    else:
        resultados_todos = [
            {"imovel": imovel, "score": None}
            for imovel in sorted(imoveis_filtrados, key=lambda x: x.criado_em, reverse=True)
        ]

    # Paginação dos resultados
    total_resultados = len(resultados_todos)
    num_paginas = math.ceil(total_resultados / PER_PAGE) if total_resultados > 0 else 1
    pagina = min(max(1, pagina), num_paginas)

    start = (pagina - 1) * PER_PAGE
    end = start + PER_PAGE
    resultados_paginados = resultados_todos[start:end]

    intervalo_paginas = calcular_intervalo_paginas(pagina, num_paginas)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "usuario": usuario,
            "imoveis": None,
            "resultados": resultados_paginados,
            "query": q or "",
            "filtros": filtros,
            "pagina": pagina,
            "num_paginas": num_paginas,
            "intervalo_paginas": intervalo_paginas,
            "total_imoveis": total_resultados,
        },
    )
