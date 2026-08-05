"""
Script para popular o banco com dados de exemplo.
Cria 3 usuários e 10 imóveis fictícios.

Uso:
    python seed_data.py
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app.models import Usuario, Imovel, Interesse
from app.auth import hash_senha



def seed():
    """Popula o banco com dados de exemplo."""
    # Cria tabelas
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Verifica se já existe dados
    if db.query(Usuario).count() > 0:
        print("⚠️  Banco já possui dados. Pulando seed.")
        db.close()
        return

    print("🌱 Populando banco de dados com dados de exemplo...")

    # --- Usuários ---
    usuario1 = Usuario(
        nome="Maria Silva",
        email="maria@email.com",
        senha_hash=hash_senha("123456"),
        tipo_usuario="corretor",
    )
    usuario2 = Usuario(
        nome="João Santos",
        email="joao@email.com",
        senha_hash=hash_senha("123456"),
        tipo_usuario="proprietario",
    )
    usuario3 = Usuario(
        nome="Ana Costa Imóveis",
        email="ana@email.com",
        senha_hash=hash_senha("123456"),
        tipo_usuario="imobiliaria",
    )
    db.add_all([usuario1, usuario2, usuario3])
    db.flush()

    print(f"✅ 3 usuários criados (senha: 123456 para todos)")

    # --- Imóveis ---
    imoveis_dados = [
        {
            "usuario": usuario1,
            "titulo": "Apartamento moderno com home office no Itaim",
            "descricao": "Apartamento completamente reformado, com um cômodo dedicado para home office, "
                         "com isolamento acústico e iluminação natural abundante. Fica em um prédio com "
                         "academia, coworking e rooftop. Próximo ao metrô, restaurantes e supermercados. "
                         "Ambiente silencioso e produtivo, perfeito para quem trabalha remotamente.",
            "preco": 650000,
            "cidade": "São Paulo",
            "bairro": "Itaim Bibi",
            "quartos": 2,
            "area": 68,
            "tipo_imovel": "apartamento",
        },
        {
            "usuario": usuario1,
            "titulo": "Casa espaçosa com quintal e piscina",
            "descricao": "Linda casa com amplo quintal gramado, piscina de vinil aquecida, churrasqueira "
                         "gourmet e área de lazer completa. Ideal para famílias com crianças e pets. "
                         "Rua tranquila e arborizada, vizinhança familiar. 4 quartos sendo 2 suítes, "
                         "cozinha planejada e garagem para 3 carros.",
            "preco": 980000,
            "cidade": "São Paulo",
            "bairro": "Granja Viana",
            "quartos": 4,
            "area": 250,
            "tipo_imovel": "casa",
        },
        {
            "usuario": usuario2,
            "titulo": "Studio compacto e prático no centro",
            "descricao": "Studio novo, mobiliado, no coração da cidade. Perfeito para estudantes ou "
                         "profissionais solteiros. A poucos metros do metrô, universidades, bibliotecas "
                         "e centros culturais. Prédio com lavanderia, bicicletário e portaria 24h. "
                         "Condomínio baixo e ótimo custo-benefício.",
            "preco": 280000,
            "cidade": "São Paulo",
            "bairro": "República",
            "quartos": 1,
            "area": 32,
            "tipo_imovel": "apartamento",
        },
        {
            "usuario": usuario2,
            "titulo": "Cobertura duplex com vista panorâmica",
            "descricao": "Cobertura espetacular com vista 360 graus da cidade. Dois andares, terraço com "
                         "jacuzzi, sala com pé direito duplo e lareira. Acabamento de alto padrão, piso "
                         "de porcelanato, iluminação LED embutida. Condomínio com spa, piscina infinity "
                         "e serviço de concierge. Para quem busca luxo e exclusividade.",
            "preco": 2500000,
            "cidade": "São Paulo",
            "bairro": "Vila Nova Conceição",
            "quartos": 3,
            "area": 180,
            "tipo_imovel": "cobertura",
        },
        {
            "usuario": usuario3,
            "titulo": "Casa de campo com natureza e tranquilidade",
            "descricao": "Refúgio em meio à natureza, cercado por Mata Atlântica. Casa de madeira e vidro "
                         "com varanda ampla, lareira, horta orgânica e trilha particular. Silêncio total, "
                         "ar puro, nascente de água natural. Ideal para desconectar do estresse urbano. "
                         "A 1 hora de São Paulo, perfeita para fins de semana ou moradia permanente.",
            "preco": 750000,
            "cidade": "São Roque",
            "bairro": "Zona Rural",
            "quartos": 3,
            "area": 200,
            "tipo_imovel": "casa",
        },
        {
            "usuario": usuario3,
            "titulo": "Apartamento pet friendly com parque na porta",
            "descricao": "Apartamento em frente ao Parque Villa-Lobos, perfeito para quem tem pets. "
                         "Condomínio aceita animais de todos os portes, tem pet place e dog wash. "
                         "3 quartos, varanda gourmet com vista para o parque. Região arborizada, "
                         "ciclovia na porta, ambiente tranquilo e seguro para caminhar com seu cão.",
            "preco": 890000,
            "cidade": "São Paulo",
            "bairro": "Alto de Pinheiros",
            "quartos": 3,
            "area": 95,
            "tipo_imovel": "apartamento",
        },
        {
            "usuario": usuario1,
            "titulo": "Sala comercial moderna no Faria Lima",
            "descricao": "Sala comercial em edifício corporativo de alto padrão na Av. Faria Lima. "
                         "Open space flexível, infraestrutura para TI, ar condicionado central, "
                         "piso elevado. Prédio com certificação LEED, recepção imponente, "
                         "estacionamento rotativo. Ideal para startups, escritórios de advocacia "
                         "ou consultorias.",
            "preco": 1200000,
            "cidade": "São Paulo",
            "bairro": "Faria Lima",
            "quartos": 0,
            "area": 120,
            "tipo_imovel": "comercial",
        },
        {
            "usuario": usuario2,
            "titulo": "Terreno para construir em condomínio fechado",
            "descricao": "Terreno plano de 500m² em condomínio fechado com portaria 24h, "
                         "segurança perimetral, lago artificial e área verde preservada. "
                         "Infraestrutura completa: água, esgoto, energia e internet fibra. "
                         "Perfeito para construir a casa dos seus sonhos em ambiente seguro "
                         "e com qualidade de vida.",
            "preco": 350000,
            "cidade": "Campinas",
            "bairro": "Alphaville",
            "quartos": 0,
            "area": 500,
            "tipo_imovel": "terreno",
        },
        {
            "usuario": usuario3,
            "titulo": "Apartamento aconchegante para aposentados",
            "descricao": "Apartamento térreo, sem escadas, ideal para idosos ou pessoas com "
                         "mobilidade reduzida. Perto de farmácias, posto de saúde e praça com "
                         "academia ao ar livre. Condomínio com portaria, elevador e acessibilidade. "
                         "Bairro calmo e seguro, ótima vizinhança. 2 quartos com armários planejados, "
                         "banheiro adaptado com barras de apoio.",
            "preco": 420000,
            "cidade": "São Paulo",
            "bairro": "Saúde",
            "quartos": 2,
            "area": 65,
            "tipo_imovel": "apartamento",
        },
        {
            "usuario": usuario1,
            "titulo": "Loft industrial reformado na Vila Madalena",
            "descricao": "Loft com pegada industrial — concreto aparente, tubulação exposta, "
                         "janelas de ferro com vidro temperado. Espaço aberto e versátil, "
                         "pé direito de 4 metros. Perfeito para artistas, designers ou quem "
                         "busca um espaço autêntico. Vila Madalena: bares, galerias de arte, "
                         "feiras de rua e vida cultural intensa a pé.",
            "preco": 520000,
            "cidade": "São Paulo",
            "bairro": "Vila Madalena",
            "quartos": 1,
            "area": 55,
            "tipo_imovel": "apartamento",
        },
    ]

    for dados in imoveis_dados:
        imovel = Imovel(
            usuario_id=dados["usuario"].id,
            titulo=dados["titulo"],
            descricao=dados["descricao"],
            preco=dados["preco"],
            cidade=dados["cidade"],
            bairro=dados["bairro"],
            quartos=dados["quartos"],
            area=dados["area"],
            tipo_imovel=dados["tipo_imovel"],
        )
        db.add(imovel)
        db.flush()

        # Nota: vetores TF-IDF são calculados no momento da busca

        print(f"  📍 {imovel.titulo}")

    # --- Alguns interesses de exemplo ---
    db.flush()
    imoveis_db = db.query(Imovel).all()
    if len(imoveis_db) >= 3:
        interesse1 = Interesse(
            imovel_id=imoveis_db[0].id,
            usuario_id=usuario2.id,
            mensagem="Gostaria de agendar uma visita neste final de semana!",
        )
        interesse2 = Interesse(
            imovel_id=imoveis_db[0].id,
            usuario_id=usuario3.id,
            mensagem="Aceita financiamento?",
        )
        interesse3 = Interesse(
            imovel_id=imoveis_db[5].id,
            usuario_id=usuario2.id,
            mensagem="Tenho 2 cachorros, posso levar para conhecer?",
        )
        db.add_all([interesse1, interesse2, interesse3])

    db.commit()
    db.close()

    print(f"\n🎉 Seed completo! {len(imoveis_dados)} imóveis criados com embeddings.")
    print("   Usuários de teste: maria@email.com / joao@email.com / ana@email.com")
    print("   Senha para todos: 123456")


from popular_banco import executar_seed

if __name__ == "__main__":
    executar_seed(reset=True)

