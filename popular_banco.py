"""
Script para popular o banco de dados do Marketplace com diversos imóveis reais e detalhados.
Gera embeddings vetoriais com IA para busca semântica e cria cenários reais de imóveis.

Uso:
    python popular_banco.py            (Popula o banco se estiver vazio ou pergunta)
    python popular_banco.py --reset    (Limpa os imóveis atuais e recria tudo do zero)
    python popular_banco.py --add      (Adiciona os imóveis aos dados existentes)
"""
import sys
import os
import argparse

# Configura encoding do console para UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))


from app.database import engine, SessionLocal, Base
from app.models import Usuario, Imovel, Imagem, Interesse
from app.auth import hash_senha
from app.embeddings import montar_texto_imovel, gerar_embedding, embedding_para_json


# --- BASE DE DADOS COMPLETA DE IMÓVEIS REAIS ---
IMOVEIS_DADOS = [
    {
        "dono_key": "maria",
        "titulo": "Apartamento com Home Office Acústico e Fibra Óptica no Itaim Bibi",
        "descricao": "Apartamento inteiramente planejado para profissionais remotos e executivos de tecnologia. "
                     "Conta com um escritório dedicado equipado com tratamento acústico nas paredes, iluminação natural direcionada, "
                     "tomada dedicada para servidor e infraestrutura de internet fibra de alta velocidade. "
                     "Condomínio moderno com coworking no térreo, sala de reuniões reservável, gerador de energia e rooftop com lounge. "
                     "Localizado a poucos passos de restaurantes corporativos, academias e ciclofaixa.",
        "preco": 720000.0,
        "cidade": "São Paulo",
        "bairro": "Itaim Bibi",
        "quartos": 2,
        "area": 75.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "ana",
        "titulo": "Casa de Condomínio com 5 Suítes, Piscina Aquecida e Espaço Gourmet",
        "descricao": "Residência de altíssimo padrão em condomínio fechado de segurança total. 5 amplas suítes com closet, "
                     "suíte master com hidro e varanda privativa. Área externa espetacular com piscina aquecida por energia solar, "
                     "spa integrado, deck de madeira maciça, churrasqueira a carvão e forno de pizza. Quintal gramado ideal para crianças e animais de estimação. "
                     "Condomínio com quadra de tênis, campo de futebol, lago para pesca esportiva e portaria 24h com ronda biométrica.",
        "preco": 2100000.0,
        "cidade": "Campinas",
        "bairro": "Alphaville",
        "quartos": 5,
        "area": 420.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "carlos",
        "titulo": "Apartamento Pet Friendly com Varanda Integrada perto do Parque Ibirapuera",
        "descricao": "Ideal para quem ama animais e vida ao ar livre! Localizado a apenas 200 metros da entrada do Parque Ibirapuera. "
                     "O condomínio oferece estrutura completa para pets: pet place com brinquedos de agilidade, área de dog wash climatizada e monitorada. "
                     "Apartamento ensolarado com piso cerâmico antiderrapante e de fácil limpeza, tela de proteção em todas as janelas e varanda envidraçada integrada à sala. "
                     "3 quartos (1 suíte) e 2 vagas de garagem.",
        "preco": 1150000.0,
        "cidade": "São Paulo",
        "bairro": "Vila Nova Conceição",
        "quartos": 3,
        "area": 110.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "joao",
        "titulo": "Studio Moderno e Mobiliado a 100m do Metrô Consolação e Paulista",
        "descricao": "Studio novíssimo, completamente mobiliado e decorado por arquiteto. Possui marcenaria inteligente multifuncional, "
                     "ar condicionado inverter, cooktop por indução e geladeira inox. Prédio com conceito coliving: lavanderia compartilhada, "
                     "academia por aplicativo, bicicletário com oficina, conveniência grab and go e rooftop com churrasqueira e vista panorâmica da Av. Paulista. "
                     "Localização imbatível para estudantes da USP/PUC/Mackenzie e jovens profissionais.",
        "preco": 340000.0,
        "cidade": "São Paulo",
        "bairro": "Consolação",
        "quartos": 1,
        "area": 34.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "patricia",
        "titulo": "Apartamento Térreo Reformado com Acessibilidade e Horta na Saúde",
        "descricao": "Imóvel perfeito para idosos, pessoas com mobilidade reduzida ou quem busca facilidade de acesso sem depender de elevadores. "
                     "Totalmente plano, sem degraus na entrada ou entre cômodos. Portas amplas de 90cm, banheiros adaptados com barras de apoio em inox e assento retrátil no box. "
                     "Conta com uma charmosa área externa privativa para jardim ou horta em vasos. Bairro extremamente calmo, a pouca distância de farmácias, supermercados e praças.",
        "preco": 460000.0,
        "cidade": "São Paulo",
        "bairro": "Saúde",
        "quartos": 2,
        "area": 70.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "carlos",
        "titulo": "Cobertura Duplex Magnífica com Piscina Privativa na Orla de Copacabana",
        "descricao": "Exclusiva cobertura duplex de frente para o mar na mítica praia de Copacabana. No primeiro pavimento, ampla sala de estar em 3 ambientes "
                     "com piso de mármore italiano, 3 suítes cinematográficas e cozinha gourmet. No segundo pavimento, terraço privativo descoberto com piscina de borda infinita, "
                     "sauna a vapor, deck de madeira e espaço bar. Vista indevassável do Posto 4 ao Pão de Açúcar. Edifício histórico conservado com concierge e segurança armada 24h.",
        "preco": 4800000.0,
        "cidade": "Rio de Janeiro",
        "bairro": "Copacabana",
        "quartos": 4,
        "area": 320.0,
        "tipo_imovel": "cobertura",
    },
    {
        "dono_key": "maria",
        "titulo": "Loft Estilo Nova-Iorquino com Pé Direito Duplo na Vila Madalena",
        "descricao": "Loft exclusivo inspirado no design industrial de Soho/NY. Apresenta paredes de tijolo aparente, vigas de aço expostas, "
                     "grandes janelas em caixilharia preta e pé-direito de 4,5 metros. Mezanino em madeira de demolição destinado ao quarto com closet. "
                     "Ambiente integrado de sala, cozinha americana e espaço para atelier ou estúdio de criação. Localizado no epicentro cultural da Vila Madalena, "
                     "rodeado por galerias de arte, bistrôs e feiras de design.",
        "preco": 590000.0,
        "cidade": "São Paulo",
        "bairro": "Vila Madalena",
        "quartos": 1,
        "area": 62.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "ana",
        "titulo": "Casa Pé na Areia com Deck e Vista para o Mar em Jurerê Internacional",
        "descricao": "Espetacular casa pé na areia localizada na área mais nobre de Jurerê Internacional. Acesso direto à praia com deck privativo de madeira, "
                     "duchas externas e lounge com ombrelones. Sala de estar com paredes de vidro retráteis abrindo totalmente para o mar. "
                     "4 suítes climatizadas, cozinha equipada para banquetes e garagem subterrânea para 4 carros e jet-ski. Excelente rendimento para locação de temporada.",
        "preco": 3900000.0,
        "cidade": "Florianópolis",
        "bairro": "Jurerê Internacional",
        "quartos": 4,
        "area": 380.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "joao",
        "titulo": "Chalé Aconchegante nas Montanhas com Lareira e Pomar em Campos do Jordão",
        "descricao": "Encantador chalé em estilo suíço cercado pelas araucárias de Campos do Jordão. Possui sala com lareira a lenha tradicional, "
                     "teto com vigamento aparente de madeira nobre e varanda envidraçada com vista para o vale. Terreno de 1.500m² enriquecido com pomar de frutas vermelhas, "
                     "horta orgânica e espaço para fogo de chão ao ar livre. Silêncio absoluto, canto dos pássaros e ar puro das montanhas. Perfeito para refúgio no inverno.",
        "preco": 850000.0,
        "cidade": "Campos do Jordão",
        "bairro": "Alto da Boa Vista",
        "quartos": 3,
        "area": 160.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "ana",
        "titulo": "Lajão Corporativo em Edifício Triple A na Avenida Faria Lima",
        "descricao": "Laje comercial de 350m² úteis no centro financeiro de São Paulo. Edifício corporativo Triple A com certificação sustentável LEED Gold, "
                     "heliponto homologado, 12 elevadores inteligentes com antecipação de chamada e gerador full atendendo 100% das áreas privativas. "
                     "Andar alto com vista panorâmica, piso elevado com cabeamento estruturado instalado, sistema de ar condicionado VRF e 10 vagas de garagem com manobrista.",
        "preco": 4200000.0,
        "cidade": "São Paulo",
        "bairro": "Faria Lima",
        "quartos": 0,
        "area": 350.0,
        "tipo_imovel": "comercial",
    },
    {
        "dono_key": "patricia",
        "titulo": "Sobrado Histórico Reformado com Vista para a Baía de Guanabara",
        "descricao": "Charmosa casa de época totalmente restaurada mantendo os traços arquitetônicos originais do século XIX combinados com confortos modernos. "
                     "Azulejos portugueses preservados, pé direito alto de 4 metros, piso de taco de madeira nobre e portas em arco. Possui pátio interno arborizado com fonte de água, "
                     "varandão com vista panorâmica para o Centro do Rio e Baía de Guanabara. Localizado no coração boêmio e cultural de Santa Teresa.",
        "preco": 890000.0,
        "cidade": "Rio de Janeiro",
        "bairro": "Santa Teresa",
        "quartos": 3,
        "area": 210.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "carlos",
        "titulo": "Apartamento Studio Smart no Batel com Alta Rentabilidade por Airbnb",
        "descricao": "Studio projetado especificamente para rentabilidade via plataformas de aluguel por temporada (Airbnb/Booking). Fechadura eletrônica por senha, "
                     "automação de iluminação e ar condicionado. Localizado no elegante bairro Batel em Curitiba, a passos dos melhores shoppings, restaurantes renomados e centros empresariais. "
                     "Prédio oferece gestão de locação profissional na recepção, piscina aquecida no ático e academia completa.",
        "preco": 310000.0,
        "cidade": "Curitiba",
        "bairro": "Batel",
        "quartos": 1,
        "area": 30.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "maria",
        "titulo": "Casa de Vila Fechada com Portão Eletrônico e Jardim na Moema",
        "descricao": "Raridade em São Paulo! Charmosa casa de vila estritamente residencial e fechada com portão eletrônico e interfone. "
                     "Ambiente extremamente seguro e acolhedor, onde as crianças brincam na rua sem trânsito de veículos. Sobrado com sala espaçosa para 2 ambientes, "
                     "cozinha gourmet integrada ao quintal privativo com jabuticabeira e churrasqueira. 3 quartos confortáveis e 1 vaga em frente à casa. A pouca distância a pé do Parque Ibirapuera.",
        "preco": 1350000.0,
        "cidade": "São Paulo",
        "bairro": "Moema",
        "quartos": 3,
        "area": 140.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "ana",
        "titulo": "Terreno Plano de 800m² em Condomínio Fechado nas Serras Gaúchas",
        "descricao": "Excelente lote plano de 800m² pronto para construir a casa de campo dos seus sonhos em Gramado. Vista permanente para as montanhas e mata de araucárias nativas. "
                     "Infraestrutura completa já instalada com fiação subterrânea (sem fios aparentes), rede de água, esgoto, gás encanado e internet de fibra. "
                     "Condomínio com clube social, piscina aquecida coberta, quadras de tênis de saibro, restaurante privativo e segurança 24h.",
        "preco": 420000.0,
        "cidade": "Gramado",
        "bairro": "Serra Gaúcha",
        "quartos": 0,
        "area": 800.0,
        "tipo_imovel": "terreno",
    },
    {
        "dono_key": "joao",
        "titulo": "Sítio com Nascente de Água, Tanque de Peixes e Pomar Orgânico em Atibaia",
        "descricao": "Sítio completo de 20.000m² (2 hectares) com abundância de água natural, incluindo nascente própria registrada e tanque para criação de peixes. "
                     "Casa sede de alvenaria com varanda de fora a fora, 4 quartos, fogão a lenha de ferro fundido e churrasqueira. Possui galinheiro estruturado, horta orgânica irrigada, "
                     "dezenas de árvores frutíferas produzindo e casa de caseiro independente. A apenas 5km do centro urbano por estrada asfaltada.",
        "preco": 680000.0,
        "cidade": "Atibaia",
        "bairro": "Zona Rural",
        "quartos": 4,
        "area": 300.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "maria",
        "titulo": "Apartamento Novo com Varanda Gourmet, Churrasqueira e Sol da Manhã",
        "descricao": "Apartamento andar alto com face norte (sol da manhã em todos os cômodos) e vista livre. Destaque para a ampla varanda gourmet com churrasqueira a carvão "
                     "e fechamento retrátil em vidro, integrada perfeitamente com a sala de jantar e cozinha. Acabamento refinado em porcelanato 90x90cm, projeto de iluminação instalado "
                     "e ar condicionado split em todos os ambientes. Condomínio clube infantil e adulto com quadra poliesportiva, piscina olímpica e pet care.",
        "preco": 890000.0,
        "cidade": "São Paulo",
        "bairro": "Perdizes",
        "quartos": 3,
        "area": 98.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "carlos",
        "titulo": "Cobertura Horizontal Única com Hidromassagem no Terraço em Belo Horizonte",
        "descricao": "Rara oportunidade de cobertura horizontal (sem escadas internas!) no topo de edifício moderno no Funcionários. Terraço ensolarado de 70m² equipado com spa "
                     "de hidromassagem para 6 pessoas, deck em madeira plástica ecológica, ducha e espaço lounge. Living integrado à cozinha americana com ilha em granito negro. "
                     "2 suítes master com persianas automatizadas. Prédio com baixo custo de condomínio e 3 vagas de garagem.",
        "preco": 1650000.0,
        "cidade": "Belo Horizonte",
        "bairro": "Funcionários",
        "quartos": 2,
        "area": 175.0,
        "tipo_imovel": "cobertura",
    },
    {
        "dono_key": "patricia",
        "titulo": "Loft Minimalista com Varanda e Vista para a Baía de Todos os Santos",
        "descricao": "Loft de design contemporâneo e minimalista no bairro da Graça em Salvador. Planta livre permitindo flexibilidade total na disposição dos móveis, "
                     "varanda ampla com vista deslumbrante para a Baía de Todos os Santos e o pôr do sol do Farol da Barra. Piso em cimento queimado tratado, marcenaria sob medida em madeira clara "
                     "e ar condicionado de alta capacidade. Prédio com piscina infinity no rooftop, pub e academia profissional.",
        "preco": 490000.0,
        "cidade": "Salvador",
        "bairro": "Graça",
        "quartos": 1,
        "area": 52.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "ana",
        "titulo": "Ponto Comercial de Rua com Grande Fluxo de Pedestres perto do Metrô",
        "descricao": "Loja térrea de rua com fachada envidraçada de 8 metros de frente para via de altíssimo tráfego de pedestres e veículos. Localizada a apenas 50 metros da estação "
                     "de metrô e cercada por bancos, escritórios e edifícios residenciais. Possui 180m² divididos em salão principal livre, 2 banheiros acessíveis, mezanino para estoque ou escritório "
                     "e vaga de carga/descarga na frente. Excelente para farmácias, padarias, clínicas ou restaurantes.",
        "preco": 1850000.0,
        "cidade": "São Paulo",
        "bairro": "Pinheiros",
        "quartos": 0,
        "area": 180.0,
        "tipo_imovel": "comercial",
    },
    {
        "dono_key": "joao",
        "titulo": "Kitnet Econômica Reformada perto do Campus da UNICAMP",
        "descricao": "Kitnet super funcional e reformada no Barão Geraldo, perfeita para estudantes da UNICAMP ou pesquisadores. Já vem com bancada de estudo com pontos de tomada e USB, "
                     "armário embutido, cozinha com cooktop elétrico e banheiro privativo com box temperado. Inclusos no condomínio: água, internet banda larga dedicada e monitoramento por câmeras 24h. "
                     "A poucos minutos de caminhada do restaurante universitário e das faculdades.",
        "preco": 195000.0,
        "cidade": "Campinas",
        "bairro": "Barão Geraldo",
        "quartos": 1,
        "area": 25.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "carlos",
        "titulo": "Mansão Neoclássica com Automação Total, Cinema e Adega Climatizada",
        "descricao": "Esplêndida mansão em estilo neoclássico construída com matérias-primas nobres e tecnologia de ponta. Sistema completo de automação residencial acionando iluminação, "
                     "persianas, áudio surround e climatização por voz ou smartphone. Possui sala de cinema privativa com 10 poltronas de couro reclináveis, adega no subsolo para 800 garrafas "
                     "com controle de umidade, 6 suítes extraordinárias e garagem coberta para 8 automóveis de coleção.",
        "preco": 7500000.0,
        "cidade": "Barueri",
        "bairro": "Alphaville",
        "quartos": 6,
        "area": 850.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "patricia",
        "titulo": "Flat Executivo com Serviço de Camareira no Setor Hoteleiro Norte",
        "descricao": "Flat executivo totalmente equipado no Setor Hoteleiro Norte de Brasília. Inclui serviços diários de arrumação e limpeza, recepção 24 horas, lavanderia, "
                     "serviço de quarto e acesso ao centro de convenções do hotel. Quarto amplo com cama king size, mesa de trabalho com iluminação adequada e mini cozinha. "
                     "Excelente alternativa tanto para moradia de executivos quanto para investimento em pool hoteleiro de alta rotatividade.",
        "preco": 380000.0,
        "cidade": "Brasília",
        "bairro": "Setor Hoteleiro Norte",
        "quartos": 1,
        "area": 42.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "joao",
        "titulo": "Casa Rústica de Praia cercada por Coqueiros em Porto de Galinhas",
        "descricao": "Encantadora casa de praia rústica construída em madeira de reflorestamento e alvenaria caiada de branco. Varandas generosas com redes de descanso "
                     "balançando com a brisa do mar, cercada por coqueirais e a escassos passos do mar de águas mornas de Porto de Galinhas. 3 quartos arejados com chuveiro solar "
                     "e ventilador de teto. Ambiente mágico e paradisíaco para desconectar e viver o estilo de vida praiano.",
        "preco": 720000.0,
        "cidade": "Ipojuca",
        "bairro": "Porto de Galinhas",
        "quartos": 3,
        "area": 145.0,
        "tipo_imovel": "casa",
    },
    {
        "dono_key": "ana",
        "titulo": "Apartamento Amplo com 4 Suítes e Vista para o Cristo Redentor",
        "descricao": "Imóvel tradicional de grande porte com 220m² de área útil. Ampla sala para 3 ambientes integrados com varanda e vista lateral para a Enseada de Botafogo "
                     "e o Cristo Redentor. 4 suítes espaçosas com armários embutidos de madeira de alta qualidade, copa separada da cozinha, dependência completa de empregada "
                     "e área de serviço ventilada. Edifício tradicional de alto padrão com 1 apartamento por andar e portaria 24 horas.",
        "preco": 1950000.0,
        "cidade": "Rio de Janeiro",
        "bairro": "Botafogo",
        "quartos": 4,
        "area": 220.0,
        "tipo_imovel": "apartamento",
    },
    {
        "dono_key": "maria",
        "titulo": "Terreno Comercial/Residencial ZEU de 1.200m² próximo ao Metrô",
        "descricao": "Lote urbano estratégico com 1.200m² de área total em zona de estruturação urbana (ZEU), ideal para incorporadoras e construtoras interessadas no desenvolvimento "
                     "de edifícios residenciais ou mistos (studios e comércio no térreo). Coeficiente de aproveitamento máximo de 4x. Terreno limpo, plano e desocupado, "
                     "com documentação 100% regularizada. Localizado a 250m de estação de metrô de grande movimento.",
        "preco": 5500000.0,
        "cidade": "São Paulo",
        "bairro": "Santana",
        "quartos": 0,
        "area": 1200.0,
        "tipo_imovel": "terreno",
    },
]


def executar_seed(reset: bool = False, adicionar: bool = False):
    """Cria usuários, imóveis com embeddings de IA, fotos e mensagens de interesse."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        cont_existentes = db.query(Imovel).count()
        if cont_existentes > 0 and not reset and not adicionar:
            print(f"⚠️  O banco já possui {cont_existentes} imóvel(is) cadastrado(s).")
            print("   Dica: Use 'python popular_banco.py --reset' para limpar e recriar,")
            print("         ou 'python popular_banco.py --add' para adicionar estes novos à lista.")
            print("\n🔄 Adicionando novos imóveis sem apagar os existentes por padrão...")

        if reset:
            print("🗑️  Limpando tabela de imóveis, imagens e interesses anteriores...")
            db.query(Interesse).delete()
            db.query(Imagem).delete()
            db.query(Imovel).delete()
            db.commit()
            print("✅ Banco resetado com sucesso!")

        print("\n👥 Garantindo usuários no sistema...")
        usuarios_map = {}
        usuarios_dados = [
            ("maria", "Maria Silva", "maria@email.com", "corretor"),
            ("joao", "João Santos", "joao@email.com", "proprietario"),
            ("ana", "Ana Costa Imóveis", "ana@email.com", "imobiliaria"),
            ("carlos", "Carlos Eduardo Luxo", "carlos@email.com", "corretor"),
            ("patricia", "Patrícia Mendes", "patricia@email.com", "proprietario"),
        ]

        senha_comum = hash_senha("123456")
        for key, nome, email, tipo in usuarios_dados:
            user = db.query(Usuario).filter(Usuario.email == email).first()
            if not user:
                user = Usuario(nome=nome, email=email, senha_hash=senha_comum, tipo_usuario=tipo)
                db.add(user)
                db.flush()
                print(f"   ➕ Usuário criado: {nome} ({email}) - {tipo}")
            usuarios_map[key] = user

        db.commit()

        print("\n🏠 Gerando imóveis com Embeddings de Inteligência Artificial...")
        
        # Foto padrão existente no projeto para exibição rica na interface
        caminho_foto_padrao = "d8d73f2fb98f4da3b4df11eff36f92ff.jpeg"
        
        novos_imoveis = []
        total = len(IMOVEIS_DADOS)

        for idx, dados in enumerate(IMOVEIS_DADOS, 1):
            dono = usuarios_map.get(dados["dono_key"], list(usuarios_map.values())[0])

            imovel = Imovel(
                usuario_id=dono.id,
                titulo=dados["titulo"],
                descricao=dados["descricao"],
                preco=dados["preco"],
                cidade=dados["cidade"],
                bairro=dados["bairro"],
                quartos=dados["quartos"],
                area=dados["area"],
                tipo_imovel=dados["tipo_imovel"],
            )

            # Calcula embedding vetorial
            texto_contexto = montar_texto_imovel(imovel)
            vetor = gerar_embedding(texto_contexto)
            if vetor:
                imovel.embedding = embedding_para_json(vetor)

            db.add(imovel)
            db.flush()

            # Adiciona imagens reais e variadas para cada imóvel
            foto_principal = f"imovel_{idx:02d}.jpg"
            if not os.path.exists(os.path.join(os.path.dirname(__file__), "static", "uploads", foto_principal)):
                foto_principal = "d8d73f2fb98f4da3b4df11eff36f92ff.jpeg"

            img1 = Imagem(
                imovel_id=imovel.id,
                caminho=foto_principal,
                ordem=0
            )
            db.add(img1)

            # Adiciona segunda foto para galeria
            idx_sec = (idx % 25) + 1
            foto_secundaria = f"imovel_{idx_sec:02d}.jpg"
            if os.path.exists(os.path.join(os.path.dirname(__file__), "static", "uploads", foto_secundaria)):
                img2 = Imagem(
                    imovel_id=imovel.id,
                    caminho=foto_secundaria,
                    ordem=1
                )
                db.add(img2)


            novos_imoveis.append(imovel)
            print(f" [{idx:02d}/{total:02d}] 📍 {imovel.titulo[:60]}...")

        # Adiciona algumas mensagens de interesse para demonstrar a aba de propostas
        print("\n💬 Gerando mensagens de interesse e propostas de exemplo...")
        if len(novos_imoveis) >= 5:
            interesses_exemplo = [
                Interesse(
                    imovel_id=novos_imoveis[0].id,
                    usuario_id=usuarios_map["joao"].id,
                    mensagem="Olá Maria! Sou desenvolvedor de software e o home office acústico é perfeito pra mim. Aceita agendar visita no sábado?",
                ),
                Interesse(
                    imovel_id=novos_imoveis[2].id,
                    usuario_id=usuarios_map["patricia"].id,
                    mensagem="Tenho 2 cachorros grandes (Golden Retriever). O pet place do prédio comporta? Gostaria de conhecer!",
                ),
                Interesse(
                    imovel_id=novos_imoveis[3].id,
                    usuario_id=usuarios_map["maria"].id,
                    mensagem="Tenho um cliente investidor interessado neste studio pra aluguel. O valor do condomínio inclui lavanderia?",
                ),
                Interesse(
                    imovel_id=novos_imoveis[8].id,
                    usuario_id=usuarios_map["carlos"].id,
                    mensagem="Excelente chalé nas montanhas. O acesso é asfaltado? Aceita permuta em imóvel comercial?",
                ),
            ]
            db.add_all(interesses_exemplo)

        db.commit()

        total_banco = db.query(Imovel).count()
        print(f"\n=======================================================")
        print(f"🎉 POPULAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Total de imóveis no banco: {total_banco}")
        print(f"🔐 Usuários de teste (Senha para todos: 123456):")
        print(f"   • maria@email.com (Corretora)")
        print(f"   • joao@email.com (Proprietário)")
        print(f"   • ana@email.com (Imobiliária)")
        print(f"   • carlos@email.com (Corretor Luxo)")
        print(f"   • patricia@email.com (Proprietária)")
        print(f"=======================================================")
        print(f"\n💡 TESTES DE BUSCA SEMÂNTICA POR IA SUGERIDOS NO SITE:")
        print(f"   1. 'lugar silencioso para trabalhar em home office com internet rapida'")
        print(f"   2. 'casa grande com piscina aquecida para crianças e animais'")
        print(f"   3. 'studio perto do metro e faculdade para estudante'")
        print(f"   4. 'apartamento terreiro sem escada adaptado para idosos'")
        print(f"   5. 'chale com lareira nas montanhas para inverno'")
        print(f"   6. 'cobertura duplex com vista para o mar'")
        print(f"   7. 'loft industrial com tijolo aparente para artista'")
        print(f"   8. 'laje corporativa na faria lima com heliponto'")
        print(f"=======================================================\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao popular banco: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Popula o banco com imóveis e descrições reais.")
    parser.add_argument("--reset", "-r", action="store_true", help="Limpa o banco e recria do zero.")
    parser.add_argument("--add", "-a", action="store_true", help="Adiciona novos imóveis sem apagar existentes.")
    args = parser.parse_args()

    executar_seed(reset=args.reset, adicionar=args.add)
