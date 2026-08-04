# 🏠 ImóvelIA — Marketplace de Imóveis com Busca Inteligente por IA

Projeto acadêmico: marketplace simplificado onde corretores, imobiliárias e proprietários cadastram imóveis, e buscadores encontram o imóvel ideal usando **busca em linguagem natural** com embeddings de IA.

## ✨ Funcionalidades

- **Busca semântica por IA** — digite "apartamento tranquilo perto de parque, bom pra home office" e a IA encontra os imóveis mais compatíveis
- **Filtros tradicionais** — preço, cidade, tipo de imóvel, número de quartos
- **Cadastro de imóveis** — com descrição, fotos, preço, localização
- **Sistema de interesse** — buscadores demonstram interesse e enviam mensagem ao anunciante
- **Painel do anunciante** — gerencie seus imóveis e veja quem demonstrou interesse
- **Autenticação simples** — login com email/senha (bcrypt + JWT)

## 🛠️ Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.10+ com FastAPI |
| Banco de dados | SQLite via SQLAlchemy |
| Frontend | HTML + Jinja2 + Tailwind CSS (CDN) |
| IA / Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Autenticação | bcrypt + JWT (cookie httponly) |
| Upload de imagens | Salvo localmente em `static/uploads/` |

## 🚀 Como Rodar

### 1. Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### 2. Instalar dependências

```bash
cd marketplace
pip install -r requirements.txt
```

> ⚠️ Na primeira execução, o modelo `all-MiniLM-L6-v2` (~80MB) será baixado automaticamente pela biblioteca `sentence-transformers`.

### 3. Configurar variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite se necessário (a configuração padrão já funciona)
```

### 4. Popular o banco com dados de exemplo (opcional, mas recomendado)

```bash
python seed_data.py
```

Isso cria 3 usuários de teste e 10 imóveis fictícios com embeddings já gerados.

**Usuários de teste:**
| Email | Senha | Tipo |
|---|---|---|
| maria@email.com | 123456 | Corretor |
| joao@email.com | 123456 | Proprietário |
| ana@email.com | 123456 | Imobiliária |

### 5. Rodar o servidor

```bash
uvicorn app.main:app --reload
```

Acesse: **http://localhost:8000**

## 📁 Estrutura do Projeto

```
marketplace/
├── app/
│   ├── main.py              # App FastAPI (ponto de entrada)
│   ├── config.py             # Configurações (.env)
│   ├── database.py           # Engine SQLAlchemy + sessão
│   ├── models.py             # Modelos: Usuario, Imovel, Imagem, Interesse
│   ├── schemas.py            # Schemas Pydantic (validação)
│   ├── auth.py               # Bcrypt + JWT
│   ├── embeddings.py         # Sentence-transformers + busca por cosseno
│   └── routes/
│       ├── auth_routes.py    # Login, cadastro, logout
│       ├── imovel_routes.py  # CRUD de imóveis
│       └── busca_routes.py   # Home + busca semântica
├── templates/                # Templates Jinja2
├── static/                   # CSS, JS, uploads
├── seed_data.py              # Dados de exemplo
├── requirements.txt          # Dependências
└── README.md
```

## 🧠 Como Funciona a Busca por IA

1. **Ao cadastrar um imóvel**, o sistema combina título + descrição + tipo + localização em um texto e gera um **vetor de embedding** (384 dimensões) usando o modelo `all-MiniLM-L6-v2`.

2. **Ao buscar**, o texto digitado pelo usuário é convertido no mesmo espaço vetorial.

3. **Similaridade de cosseno** é calculada entre o vetor da busca e cada vetor dos imóveis, retornando os mais semelhantes com um **score de match (%)**.

4. Filtros tradicionais (preço, quartos, cidade) são aplicados **antes** da busca semântica, reduzindo os candidatos.

## 📝 Licença

Projeto acadêmico — uso livre para fins educacionais.
