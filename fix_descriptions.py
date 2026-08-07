import re
import sys
import urllib.request
from html import unescape

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from app.database import SessionLocal
from app.models import Imovel, Usuario
from app.embeddings import montar_texto_imovel, gerar_embedding, embedding_para_json

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def extrair_descricao_limpa(html, titulo, bairro):
    clean = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<svg[^>]*>.*?</svg>', '', clean, flags=re.DOTALL | re.IGNORECASE)

    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', clean, flags=re.DOTALL | re.IGNORECASE)
    candidatos = []
    for p in paragraphs:
        text = unescape(re.sub(r'<[^>]+>', '', p)).strip()
        text = re.sub(r'\s+', ' ', text)
        if len(text) > 30 and not any(x in text for x in ['Cookie', 'Privacidade', 'Razão social', 'CRECI', 'Copyright', 'Onde nos encontrar']):
            candidatos.append(text)

    if candidatos:
        for c in candidatos:
            if c.startswith("Apartamento") or "bairro" in c.lower() or "localizado" in c.lower():
                return c
        return candidatos[0]
    return f"{titulo}. Excelente apartamento no bairro {bairro} em Chapecó."

def corrigir_descricoes():
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter_by(email='contato@plazachapeco.com.br').first()
        if not user:
            print("Usuário não encontrado.")
            return

        imoveis = db.query(Imovel).filter_by(usuario_id=user.id).all()
        print(f"🔧 Corrigindo descrições de {len(imoveis)} imóveis no banco...")

        # Para obter o link original, usaremos os links da raspagem
        req = urllib.request.Request("https://plazachapeco.com.br/comprar/apartamento/", headers=HEADERS)
        html_list = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
        links_1 = set(re.findall(r'href=["\'](https://plazachapeco\.com\.br/imovel/(\d+)/[^"\']+)["\']', html_list))
        
        req2 = urllib.request.Request("https://plazachapeco.com.br/comprar/apartamento/pag-2/", headers=HEADERS)
        html_list2 = urllib.request.urlopen(req2).read().decode('utf-8', errors='ignore')
        links_2 = set(re.findall(r'href=["\'](https://plazachapeco\.com\.br/imovel/(\d+)/[^"\']+)["\']', html_list2))

        req3 = urllib.request.Request("https://plazachapeco.com.br/comprar/apartamento/pag-3/", headers=HEADERS)
        html_list3 = urllib.request.urlopen(req3).read().decode('utf-8', errors='ignore')
        links_3 = set(re.findall(r'href=["\'](https://plazachapeco\.com\.br/imovel/(\d+)/[^"\']+)["\']', html_list3))

        url_by_cod = {}
        for full_url, cod in links_1.union(links_2).union(links_3):
            url_by_cod[cod] = full_url

        atualizados = 0
        for im in imoveis:
            # Encontra cod pelo titulo ou desc
            cod_match = re.search(r'COD\.?\s*(\d+)', im.descricao, re.IGNORECASE)
            cod = cod_match.group(1) if cod_match else None
            
            if not cod:
                # Tenta buscar em url_by_cod por bairro/preco
                for c, url in url_by_cod.items():
                    if c in im.titulo or f"/{c}/" in str(url):
                        cod = c
                        break

            if cod and cod in url_by_cod:
                url_imovel = url_by_cod[cod]
                req_im = urllib.request.Request(url_imovel, headers=HEADERS)
                html_im = urllib.request.urlopen(req_im).read().decode('utf-8', errors='ignore')
                desc_limpa = extrair_descricao_limpa(html_im, im.titulo, im.bairro)
            else:
                desc_limpa = f"{im.titulo}. Excelente apartamento localizado no bairro {im.bairro} em Chapecó-SC."

            im.descricao = desc_limpa
            texto_ia = montar_texto_imovel(im)
            vetor = gerar_embedding(texto_ia)
            if vetor:
                im.embedding = embedding_para_json(vetor)

            atualizados += 1
            print(f"  ✅ [{im.id}] {im.titulo[:40]}")
            print(f"     -> {desc_limpa[:80]}...")

        db.commit()
        print(f"\n🎉 {atualizados} descrições atualizadas no banco de dados com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    corrigir_descricoes()
