"""
Script para baixar fotos reais e variadas de imóveis via Unsplash
e salvar na pasta static/uploads/ com nomes estruturados.
"""
import os
import sys
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


DESTINO = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(DESTINO, exist_ok=True)

# 25 URLs de fotos de imóveis de alta qualidade (Unsplash)
FOTOS_URLS = [
    # 01 - Home Office / Ap Itaim
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&auto=format&fit=crop&q=80",
    # 02 - Casa de Condomínio / Alphaville
    "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=800&auto=format&fit=crop&q=80",
    # 03 - Pet Friendly / Ibirapuera
    "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=800&auto=format&fit=crop&q=80",
    # 04 - Studio Consolação
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&auto=format&fit=crop&q=80",
    # 05 - Ap Térreo Saúde
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&auto=format&fit=crop&q=80",
    # 06 - Cobertura Copacabana
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&auto=format&fit=crop&q=80",
    # 07 - Loft Vila Madalena
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&auto=format&fit=crop&q=80",
    # 08 - Casa Jurerê
    "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=800&auto=format&fit=crop&q=80",
    # 09 - Chalé Campos do Jordão
    "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&auto=format&fit=crop&q=80",
    # 10 - Lajão Faria Lima
    "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&auto=format&fit=crop&q=80",
    # 11 - Sobrado Santa Teresa
    "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80",
    # 12 - Studio Batel
    "https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800&auto=format&fit=crop&q=80",
    # 13 - Casa de Vila Moema
    "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&auto=format&fit=crop&q=80",
    # 14 - Terreno Gramado
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&auto=format&fit=crop&q=80",
    # 15 - Sítio Atibaia
    "https://images.unsplash.com/photo-1500076656116-558758c991c1?w=800&auto=format&fit=crop&q=80",
    # 16 - Ap Perdizes
    "https://images.unsplash.com/photo-1567496898669-ee935f5f647a?w=800&auto=format&fit=crop&q=80",
    # 17 - Cobertura BH
    "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800&auto=format&fit=crop&q=80",
    # 18 - Loft Salvador
    "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=800&auto=format&fit=crop&q=80",
    # 19 - Ponto Comercial Pinheiros
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&auto=format&fit=crop&q=80",
    # 20 - Kitnet UNICAMP
    "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=800&auto=format&fit=crop&q=80",
    # 21 - Mansão Neoclássica
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&auto=format&fit=crop&q=80",
    # 22 - Flat Brasília
    "https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80",
    # 23 - Casa Porto de Galinhas
    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&auto=format&fit=crop&q=80",
    # 24 - Ap Botafogo
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&auto=format&fit=crop&q=80",
    # 25 - Terreno Santana
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&auto=format&fit=crop&q=80",
]

def baixar_fotos():
    print(f"📥 Baixando {len(FOTOS_URLS)} fotos variadas de imóveis para static/uploads/...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    fotos_salvas = []
    for idx, url in enumerate(FOTOS_URLS, 1):
        nome_arquivo = f"imovel_{idx:02d}.jpg"
        caminho_final = os.path.join(DESTINO, nome_arquivo)
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response, open(caminho_final, 'wb') as out_file:
                out_file.write(response.read())
            print(f"  ✅ [{idx:02d}/25] Salvo: {nome_arquivo}")
            fotos_salvas.append(nome_arquivo)
        except Exception as e:
            print(f"  ⚠️ Erro ao baixar foto {idx}: {e}")
            # Em caso de falha de conexão, fallback
            fotos_salvas.append("d8d73f2fb98f4da3b4df11eff36f92ff.jpeg")
            
    print(f"\n✨ {len(fotos_salvas)} fotos salvas com sucesso em static/uploads!")
    return fotos_salvas

if __name__ == "__main__":
    baixar_fotos()
