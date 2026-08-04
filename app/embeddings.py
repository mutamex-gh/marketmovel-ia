"""
Módulo de embeddings — busca semântica por IA usando Redes Neurais (Sentence-Transformers).

Utiliza o modelo pré-treinado 'paraphrase-multilingual-MiniLM-L12-v2' (ou 'all-MiniLM-L6-v2')
para gerar embeddings vetoriais densos que representam o significado semântico do imóvel.
Isso permite encontrar imóveis por intenção ("lugar calmo pra home office", "perto do verde")
mesmo que as palavras exatas não estejam na descrição.
"""
import json
from typing import List, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Imovel

# Instância global do modelo de IA (carregado sob demanda para não atrasar o boot)
_modelo_ia = None
_tentou_carregar = False


def obter_modelo_ia():
    """
    Carrega o modelo de inteligência artificial Sentence Transformers.
    Utiliza o modelo neural multilíngue para interpretação em Português.
    """
    global _modelo_ia, _tentou_carregar
    if not _tentou_carregar:
        _tentou_carregar = True
        try:
            from sentence_transformers import SentenceTransformer
            print("🧠 Carregando Modelo Neural de IA (Sentence Transformers)...")
            _modelo_ia = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            print("✅ Modelo de IA carregado e pronto para busca semântica!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar Sentence-Transformers: {e}")
            print("🔄 Usando fallback para TF-IDF até que o modelo neural esteja disponível.")
            _modelo_ia = None
    return _modelo_ia


# ---------------------------------------------------------------------------
# Construção do texto do imóvel
# ---------------------------------------------------------------------------

def montar_texto_imovel(imovel: Imovel) -> str:
    """
    Combina os campos relevantes do imóvel em um texto contextualizado para a IA.
    """
    partes = [
        f"Imóvel: {imovel.titulo}.",
        f"Tipo: {imovel.tipo_imovel}.",
        f"Descrição: {imovel.descricao}.",
        f"Localização: bairro {imovel.bairro}, cidade {imovel.cidade}.",
        f"Características: {imovel.quartos} quartos, preço R$ {imovel.preco:.2f}."
    ]
    if imovel.area:
        partes.append(f"Área de {imovel.area} metros quadrados.")
    return " ".join(partes)


def gerar_embedding(texto: str) -> List[float]:
    """
    Gera o vetor de embedding real (384 dimensões) utilizando o modelo neural de IA.
    """
    modelo = obter_modelo_ia()
    if modelo is not None:
        vector = modelo.encode(texto, convert_to_numpy=True)
        return vector.tolist()
    return []


def embedding_para_json(embedding: List[float]) -> str:
    """Serializa embedding para salvar no banco."""
    return json.dumps(embedding)


def embedding_do_json(json_str: str) -> List[float]:
    """Desserializa embedding do banco."""
    if not json_str:
        return []
    return json.loads(json_str)


# ---------------------------------------------------------------------------
# Fallback TF-IDF (se a biblioteca de IA ainda estiver baixando)
# ---------------------------------------------------------------------------

def _buscar_tfidf_fallback(query_texto: str, imoveis: List[Imovel], top_k: int) -> List[Tuple[Imovel, float]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    textos_imoveis = [montar_texto_imovel(im) for im in imoveis]
    corpus = [query_texto] + textos_imoveis
    vetorizador = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", lowercase=True)
    matriz = vetorizador.fit_transform(corpus)
    scores = cosine_similarity(matriz[0:1], matriz[1:]).flatten()
    resultados = [(imovel, float(score)) for imovel, score in zip(imoveis, scores)]
    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados[:top_k]


# ---------------------------------------------------------------------------
# Busca por similaridade neural de IA
# ---------------------------------------------------------------------------

def buscar_similares(
    query_texto: str,
    imoveis: List[Imovel],
    top_k: int = 20,
) -> List[Tuple[Imovel, float]]:
    """
    Compara a busca do usuário com os imóveis usando a Rede Neural da IA + similaridade de cosseno.

    Retorna lista de tuplas (imóvel, score). Score vai de 0 a 1 (convertido em %).
    """
    if not imoveis:
        return []

    modelo = obter_modelo_ia()

    # Se o modelo neural não estiver disponível, usa fallback TF-IDF
    if modelo is None:
        return _buscar_tfidf_fallback(query_texto, imoveis, top_k)

    # 1. Gera embedding da busca do usuário com a Rede Neural
    vetor_query = modelo.encode([query_texto], convert_to_numpy=True)

    # 2. Gera embeddings dos imóveis filtrados
    textos_imoveis = [montar_texto_imovel(im) for im in imoveis]
    vetores_imoveis = modelo.encode(textos_imoveis, convert_to_numpy=True)

    # 3. Calcula similaridade semântica por cosseno no espaço vetorial neural
    scores = cosine_similarity(vetor_query, vetores_imoveis).flatten()

    # 4. Normaliza e monta resultados
    resultados = []
    for imovel, score in zip(imoveis, scores):
        # Garante score numérico válido e não negativo
        val_score = float(max(0.0, score))
        resultados.append((imovel, val_score))

    # 5. Ordena por score decrescente
    resultados.sort(key=lambda x: x[1], reverse=True)

    return resultados[:top_k]
