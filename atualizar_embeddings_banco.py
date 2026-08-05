"""
Script auxiliar para recarregar e salvar embeddings vetoriais de todos os imóveis existentes no banco de dados.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.database import SessionLocal
from app.models import Imovel
from app.embeddings import montar_texto_imovel, gerar_embedding, embedding_para_json

def atualizar_todos():
    db = SessionLocal()
    try:
        imoveis = db.query(Imovel).all()
        print(f"[IA] Atualizando embeddings vetoriais de {len(imoveis)} imóveis...")
        atualizados = 0
        for im in imoveis:
            texto = montar_texto_imovel(im)
            vetor = gerar_embedding(texto)
            if vetor:
                im.embedding = embedding_para_json(vetor)
                atualizados += 1
                print(f"  ✓ [{im.id}] {im.cidade} - {im.titulo[:40]}...")
        db.commit()
        print(f"[Sucesso] Embeddings de {atualizados} imóveis gerados e salvos no banco!")
    except Exception as e:
        db.rollback()
        print(f"[Erro] Falha ao atualizar embeddings: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    atualizar_todos()
