"""
Módulo de embeddings — busca semântica por IA usando Redes Neurais (Sentence-Transformers).

Utiliza o modelo pré-treinado 'paraphrase-multilingual-MiniLM-L12-v2'
para gerar embeddings vetoriais densos que representam o significado semântico do imóvel.
Combina busca semântica vetorial com filtros inteligentes de localização e tipo de imóvel.
"""
import json
import re
from typing import List, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Imovel

# Instância global do modelo de IA (carregado sob demanda ou no startup)
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
            print("[IA] Carregando Modelo Neural (paraphrase-multilingual-MiniLM-L12-v2)...")
            _modelo_ia = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            print("[IA] Modelo de IA carregado e pronto para busca semantica!")
        except Exception as e:
            print(f"[Aviso] Nao foi possivel carregar Sentence-Transformers: {e}")
            print("[Aviso] Usando fallback para TF-IDF + Matching Hibrido.")
            _modelo_ia = None
    return _modelo_ia


# ---------------------------------------------------------------------------
# Construção do texto do imóvel para a IA
# ---------------------------------------------------------------------------

def montar_texto_imovel(imovel: Imovel) -> str:
    """
    Combina os campos relevantes do imóvel em um texto rico e contextualizado para a IA.
    """
    partes = [
        f"Imóvel: {imovel.titulo}.",
        f"Tipo de imóvel: {imovel.tipo_imovel}.",
        f"Cidade: {imovel.cidade}.",
        f"Bairro: {imovel.bairro}.",
        f"Descrição: {imovel.descricao}.",
        f"Especificações: {imovel.quartos} quartos, preço R$ {imovel.preco:.2f}."
    ]
    if imovel.area:
        partes.append(f"Área de {imovel.area} m².")
    if imovel.localizacao:
        partes.append(f"Localização exata: {imovel.localizacao}.")
    return " ".join(partes)


def gerar_embedding(texto: str) -> List[float]:
    """
    Gera o vetor de embedding (384 dimensões) utilizando o modelo neural de IA.
    """
    modelo = obter_modelo_ia()
    if modelo is not None:
        try:
            vector = modelo.encode(texto, convert_to_numpy=True)
            return vector.tolist()
        except Exception as e:
            print(f"[Erro] Falha ao gerar embedding: {e}")
    return []


def embedding_para_json(embedding: List[float]) -> str:
    """Serializa embedding para salvar no banco."""
    return json.dumps(embedding) if embedding else ""


def embedding_do_json(json_str: str) -> List[float]:
    """Desserializa embedding do banco."""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Fallback TF-IDF com busca textual
# ---------------------------------------------------------------------------

def _buscar_tfidf_fallback(query_texto: str, imoveis: List[Imovel]) -> np.ndarray:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        textos_imoveis = [montar_texto_imovel(im) for im in imoveis]
        corpus = [query_texto] + textos_imoveis
        vetorizador = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", lowercase=True)
        matriz = vetorizador.fit_transform(corpus)
        return cosine_similarity(matriz[0:1], matriz[1:]).flatten()
    except Exception:
        return np.zeros(len(imoveis))


# ---------------------------------------------------------------------------
# Algoritmo Híbrido: Vetores + Boosting Inteligente de Localização e Tipo
# ---------------------------------------------------------------------------

def buscar_similares(
    query_texto: str,
    imoveis: List[Imovel],
    top_k: int = 20,
) -> List[Tuple[Imovel, float]]:
    """
    Compara a busca do usuário com os imóveis usando Rede Neural IA (ou embeddings salvos)
    mais um algoritmo de ranking híbrido que prioriza cidade, bairro e tipo de imóvel.
    """
    if not imoveis:
        return []

    query_clean = query_texto.strip()
    query_lower = query_clean.lower()
    modelo = obter_modelo_ia()

    # 1. Obtenção dos vetores de similaridade base
    if modelo is not None:
        try:
            vetor_query = modelo.encode([query_clean], convert_to_numpy=True)

            vetores_list = []
            for im in imoveis:
                vec = embedding_do_json(im.embedding) if im.embedding else []
                if not vec:
                    # Se o imóvel ainda não possui embedding no banco, calcula na hora
                    vec = gerar_embedding(montar_texto_imovel(im))
                vetores_list.append(vec)

            # Se todos tiverem vetores válidos (384-dim)
            if vetores_list and len(vetores_list[0]) == len(vetor_query[0]):
                vetores_matrix = np.array(vetores_list)
                raw_scores = cosine_similarity(vetor_query, vetores_matrix).flatten()
            else:
                raw_scores = _buscar_tfidf_fallback(query_clean, imoveis)
        except Exception as e:
            print(f"[Aviso] Erro na matriz de embeddings: {e}")
            raw_scores = _buscar_tfidf_fallback(query_clean, imoveis)
    else:
        raw_scores = _buscar_tfidf_fallback(query_clean, imoveis)

    # 2. Ranking Híbrido: Impulso por Cidade, Bairro e Tipo de Imóvel
    # Identifica se o usuário digitou uma cidade ou tipo de imóvel explícito na busca
    cidades_no_banco = {im.cidade.lower() for im in imoveis if im.cidade}
    tipos_no_banco = {"apartamento", "casa", "cobertura", "terreno", "comercial", "chale", "chalé", "studio", "loft"}

    cidades_mencionadas = [c for c in cidades_no_banco if c in query_lower]
    tipos_mencionados = [t for t in tipos_no_banco if t in query_lower]

    resultados = []
    for imovel, base_score in zip(imoveis, raw_scores):
        score = float(max(0.0, base_score))

        cidade_imovel = imovel.cidade.lower() if imovel.cidade else ""
        bairro_imovel = imovel.bairro.lower() if imovel.bairro else ""
        tipo_imovel = imovel.tipo_imovel.lower() if imovel.tipo_imovel else ""
        titulo_imovel = imovel.titulo.lower() if imovel.titulo else ""

        # --- BOOST DE CIDADE ---
        if cidades_mencionadas:
            if cidade_imovel in cidades_mencionadas:
                score += 0.45  # Forte impulso para a cidade correta!
            else:
                score -= 0.50  # Penalidade se o usuário pediu uma cidade e o imóvel é de outra!

        # Se a cidade bater com palavras soltas na busca (ex: "chapecó")
        elif cidade_imovel and cidade_imovel in query_lower:
            score += 0.40

        # --- BOOST DE BAIRRO ---
        if bairro_imovel and bairro_imovel in query_lower:
            score += 0.30

        # --- BOOST DE TIPO DE IMÓVEL ---
        if tipos_mencionados:
            if tipo_imovel in tipos_mencionados or (tipo_imovel == "casa" and "chalé" in tipos_mencionados):
                score += 0.25
            else:
                score -= 0.20

        # --- BOOST DE TÍTULO ---
        tokens_query = set(re.findall(r'\w+', query_lower))
        tokens_titulo = set(re.findall(r'\w+', titulo_imovel))
        matches_titulo = tokens_query.intersection(tokens_titulo) - {"de", "em", "com", "no", "na", "para", "um", "uma", "do", "da"}
        if matches_titulo:
            score += 0.10 * len(matches_titulo)

        # Limita o score final entre 0.0 e 1.0 (para exibição em %)
        final_score = float(np.clip(score, 0.0, 1.0))
        resultados.append((imovel, final_score))

    # 3. Ordena por relevância decrescente
    resultados.sort(key=lambda x: x[1], reverse=True)

    return resultados[:top_k]


def buscar_imoveis_similares_por_imovel(imovel_alvo: Imovel, imoveis: List[Imovel], top_k: int = 4) -> List[Imovel]:
    """
    Encontra imóveis mais semelhantes ao 'imovel_alvo' com base nos vetores de IA (embeddings)
    e heurísticas de tipo de imóvel, cidade e especificações similares.
    """
    # Filtra o próprio imóvel alvo
    outros_imoveis = [i for i in imoveis if i.id != imovel_alvo.id]
    if not outros_imoveis:
        return []

    # Tenta usar os vetores de embedding já salvos
    vetor_alvo = embedding_do_json(imovel_alvo.embedding) if imovel_alvo.embedding else None

    # Se não tiver vetor salvo no alvo, gera dinamicamente
    if not vetor_alvo:
        vetor_alvo = gerar_embedding(montar_texto_imovel(imovel_alvo))

    cand_com_vetor = []
    for cand in outros_imoveis:
        vetor_cand = embedding_do_json(cand.embedding) if cand.embedding else None
        if not vetor_cand:
            vetor_cand = gerar_embedding(montar_texto_imovel(cand))
        cand_com_vetor.append((cand, vetor_cand))

    scores = []
    for cand, v_cand in cand_com_vetor:
        if vetor_alvo and v_cand:
            try:
                sim = float(cosine_similarity([vetor_alvo], [v_cand])[0][0])
            except Exception:
                sim = 0.5
        else:
            sim = 0.5  # base

        # Boost de mesma cidade (+0.25)
        if cand.cidade and imovel_alvo.cidade and cand.cidade.lower() == imovel_alvo.cidade.lower():
            sim += 0.25
        # Boost de mesmo tipo de imóvel (+0.20)
        if cand.tipo_imovel and imovel_alvo.tipo_imovel and cand.tipo_imovel.lower() == imovel_alvo.tipo_imovel.lower():
            sim += 0.20
        # Boost de quantidade de quartos similar (+0.10)
        if cand.quartos and imovel_alvo.quartos and abs(cand.quartos - imovel_alvo.quartos) <= 1:
            sim += 0.10

        scores.append((cand, sim))

    # Ordena por similaridade decrescente
    scores.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scores[:top_k]]

