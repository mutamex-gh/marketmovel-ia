"""
Script para raspar imóveis (apartamentos à venda) do site Plaza Chapecó,
baixar fotos reais, cadastrar no banco de dados e gerar embeddings vetoriais para IA.
"""
import os
import sys
import re
import time
import urllib.request
from html import unescape
from pathlib import Path

# Suporte UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adiciona o diretório do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal, engine, Base
from app.models import Usuario, Imovel, Imagem
from app.auth import hash_senha
from app.embeddings import montar_texto_imovel, gerar_embedding, embedding_para_json

# Garante a criação das tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)

# Diretório de destino para fotos salvas
UPLOADS_DIR = BASE_DIR / "static" / "uploads"
PLAZA_DIR = UPLOADS_DIR / "plaza"
PLAZA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def obter_ou_criar_usuario_plaza(db):
    """Retorna o usuário imobiliária da Plaza Chapecó, criando-o se necessário."""
    usuario = db.query(Usuario).filter(Usuario.email == "contato@plazachapeco.com.br").first()
    if not usuario:
        usuario = Usuario(
            nome="Plaza Imóveis Chapecó",
            email="contato@plazachapeco.com.br",
            senha_hash=hash_senha("plaza12345"),
            telefone="(49) 3316-3020",
            documento="16.927.275/0001-05",
            tipo_usuario="imobiliaria"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        print(f"👤 Usuário criado: {usuario.nome} (ID: {usuario.id})")
    else:
        print(f"👤 Usuário existente encontrado: {usuario.nome} (ID: {usuario.id})")
    return usuario


def baixar_imagem(url, caminho_local):
    """Baixa uma imagem da URL para o caminho local informado."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp, open(caminho_local, "wb") as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"    ⚠️ Erro ao baixar foto ({url[:60]}...): {e}")
        return False


def extrair_detalhes_imovel(url):
    """Acessa a página de um imóvel específico e extrai seus atributos."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Título
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        titulo = unescape(re.sub(r'<[^>]+>', '', title_match.group(1)).strip()) if title_match else "Apartamento à venda em Chapecó"

        # Preço
        price_match = re.search(r'R\$\s*([\d\.\,]+)', html)
        if price_match:
            price_clean = price_match.group(1).replace(".", "").replace(",", ".")
            preco = float(price_clean)
        else:
            preco = 450000.0

        # Bairro e Cidade
        location_match = re.search(r'([A-Za-zÀ-ú\s]+),\s*Chapecó\s*-\s*SC', html)
        if location_match:
            bairro = location_match.group(1).strip()
        else:
            bairro = "Centro"
        cidade = "Chapecó"
        localizacao = f"{bairro}, Chapecó - SC"

        # Área
        area_match = re.search(r'(\d+[\,\.]?\d*)\s*m²', html, re.IGNORECASE)
        area = float(area_match.group(1).replace(',', '.')) if area_match else 70.0

        # Quartos
        quartos_match = re.search(r'(\d+)\s*(?:quartos|dormitórios|quarto)', html, re.IGNORECASE)
        quartos = int(quartos_match.group(1)) if quartos_match else 2

        # Limpa o HTML removendo tags <head>, <style>, <script> e <svg> para evitar captura de CSS/JSON-LD
        clean_html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'<script[^>]*>.*?</script>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'<svg[^>]*>.*?</svg>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)

        # Extração de Descrição dos parágrafos do HTML limpo
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', clean_html, flags=re.DOTALL | re.IGNORECASE)
        candidatos = []
        for p in paragraphs:
            text = unescape(re.sub(r'<[^>]+>', '', p)).strip()
            text = re.sub(r'\s+', ' ', text)
            if len(text) > 30 and not any(x in text for x in ['Cookie', 'Privacidade', 'Razão social', 'CRECI', 'Copyright', 'Onde nos encontrar']):
                candidatos.append(text)

        descricao = f"{titulo}. Excelente apartamento no bairro {bairro} em Chapecó."
        if candidatos:
            for c in candidatos:
                if c.startswith("Apartamento") or "bairro" in c.lower() or "localizado" in c.lower():
                    descricao = c
                    break
            else:
                descricao = candidatos[0]

        # Fotos
        all_imgs = re.findall(r'(https://cdn\.imoview\.com\.br/[^"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^"\']*)?)', html, re.IGNORECASE)
        if not all_imgs:
            all_imgs = re.findall(r'(https://[^\'"]+/Imoveis/[^"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^"\']*)?)', html, re.IGNORECASE)
        # Filtra logos, ícones e arquivos pequenos
        fotos = [img for img in set(all_imgs) if not any(x in img.lower() for x in ['logo', 'icon', 'favicon', 'theme', 'svg', 'avatar', 'user'])]
        
        return {
            "titulo": titulo,
            "preco": preco,
            "cidade": cidade,
            "bairro": bairro,
            "localizacao": localizacao,
            "area": area,
            "quartos": quartos,
            "tipo_imovel": "apartamento",
            "descricao": descricao,
            "fotos": list(dict.fromkeys(fotos))[:5]  # Preserva ordem e limita a até 5 fotos por imóvel
        }
    except Exception as e:
        print(f"  ❌ Erro ao extrair imóvel ({url}): {e}")
        return None


def raspar_plaza(max_paginas=3):
    """Percorre as páginas de listagem do site da Plaza Chapecó e salva imóveis no banco."""
    print("🚀 Iniciando raspagem de apartamentos no site da Plaza Chapecó...")
    db = SessionLocal()

    try:
        usuario = obter_ou_criar_usuario_plaza(db)
        links_imoveis = []

        # 1. Coleta os links de todos os apartamentos em max_paginas
        for pag in range(1, max_paginas + 1):
            if pag == 1:
                url_listagem = "https://plazachapeco.com.br/comprar/apartamento/"
            else:
                url_listagem = f"https://plazachapeco.com.br/comprar/apartamento/pag-{pag}/"

            print(f"📖 Lendo página {pag}: {url_listagem}")
            req = urllib.request.Request(url_listagem, headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                
                encontrados = re.findall(r'href=["\'](https://plazachapeco\.com\.br/imovel/\d+/[^"\']+)["\']', html)
                links_unicos = list(set(encontrados))
                print(f"  ✓ {len(links_unicos)} imóveis encontrados na página {pag}")
                for link in links_unicos:
                    if link not in links_imoveis:
                        links_imoveis.append(link)
            except Exception as e:
                print(f"  ⚠️ Falha ao carregar página {pag}: {e}")

        print(f"\n📦 Total de imóveis únicos para processar: {len(links_imoveis)}")

        # 2. Processa cada imóvel
        novos_imoveis = 0
        for idx, url_imovel in enumerate(links_imoveis, 1):
            cod_match = re.search(r'/imovel/(\d+)/', url_imovel)
            cod_imovel = cod_match.group(1) if cod_match else f"{idx:03d}"

            print(f"\n[{idx}/{len(links_imoveis)}] Processando Cód {cod_imovel}: {url_imovel[:70]}...")
            
            detalhes = extrair_detalhes_imovel(url_imovel)
            if not detalhes:
                continue

            # Evita duplicatas verificando título e usuário
            imovel_existente = db.query(Imovel).filter(
                Imovel.usuario_id == usuario.id,
                Imovel.titulo == detalhes["titulo"]
            ).first()

            if imovel_existente:
                print(f"  ✏️ Atualizando descrição e IA do imóvel (ID: {imovel_existente.id})...")
                imovel_existente.descricao = detalhes["descricao"]
                texto_ia = montar_texto_imovel(imovel_existente)
                vetor_ia = gerar_embedding(texto_ia)
                if vetor_ia:
                    imovel_existente.embedding = embedding_para_json(vetor_ia)
                db.commit()
                novos_imoveis += 1
                continue

            # Cria a instância do Imóvel
            novo_imovel = Imovel(
                usuario_id=usuario.id,
                titulo=detalhes["titulo"],
                descricao=detalhes["descricao"],
                preco=detalhes["preco"],
                cidade=detalhes["cidade"],
                bairro=detalhes["bairro"],
                localizacao=detalhes["localizacao"],
                quartos=detalhes["quartos"],
                area=detalhes["area"],
                tipo_imovel=detalhes["tipo_imovel"]
            )

            db.add(novo_imovel)
            db.flush()  # Gera o ID do imóvel

            # Baixa e associa as imagens
            fotos_salvas = 0
            for foto_idx, url_foto in enumerate(detalhes["fotos"], 1):
                nome_foto = f"plaza_{cod_imovel}_{foto_idx}.jpg"
                caminho_abs = PLAZA_DIR / nome_foto
                caminho_rel = f"plaza/{nome_foto}"

                if baixar_imagem(url_foto, caminho_abs):
                    imagem = Imagem(
                        imovel_id=novo_imovel.id,
                        caminho=caminho_rel,
                        ordem=foto_idx - 1
                    )
                    db.add(imagem)
                    fotos_salvas += 1

            print(f"  📸 {fotos_salvas} fotos salvas com sucesso.")

            # Gera embedding de IA
            texto_ia = montar_texto_imovel(novo_imovel)
            vetor_ia = gerar_embedding(texto_ia)
            if vetor_ia:
                novo_imovel.embedding = embedding_para_json(vetor_ia)
                print(f"  🤖 Embedding de IA gerado com sucesso.")

            db.commit()
            novos_imoveis += 1
            time.sleep(0.3)  # Respeita o servidor de origem

        print(f"\n🎉 Processamento concluído! {novos_imoveis} novos imóveis cadastrados no banco de dados.")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro crítico no processo de raspagem: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    raspar_plaza(max_paginas=3)
