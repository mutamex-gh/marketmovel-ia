# MarketMóvel IA — API REST

API REST (JSON) do marketplace de imóveis **MarketMóvel IA**, feita com **FastAPI + SQLAlchemy + SQLite** e autenticação **JWT Bearer**.

## Como rodar

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Linux/Mac: cp .env.example .env
uvicorn app.main:app --reload
```

- API: `http://localhost:8000/api/v1`
- Documentação interativa (Swagger): `http://localhost:8000/docs`
- Admin padrão (criado automaticamente): `admin@marketmovel.com.br` / `admin`

## Resources (7)

| Resource | Endpoints | Regras de acesso |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | público / token |
| Usuários | `GET/POST /usuarios`, `GET/PUT/DELETE /usuarios/{id}` | listar/criar: admin · ver/editar/excluir: o próprio ou admin · mudar papel: admin |
| Tipos de Usuário | `GET/POST /tipos-usuario`, `GET/PUT/DELETE /tipos-usuario/{id}` | GET público · escrita: admin |
| Imóveis | `GET/POST /imoveis`, `GET /imoveis/busca?q=` (IA), `GET /imoveis/meus`, `GET/PUT/DELETE /imoveis/{id}` | GET público · criar: logado · editar/excluir: dono ou admin |
| Imagens | `GET/POST /imoveis/{id}/imagens`, `DELETE /imoveis/{id}/imagens/{imagem_id}` | GET público · upload/excluir: dono ou admin |
| Interesses | `GET/POST /interesses`, `GET /interesses/recebidos`, `GET/PUT/DELETE /interesses/{id}` | logado · editar: autor · excluir: autor ou admin |
| Favoritos | `GET/POST /favoritos`, `DELETE /favoritos/{id}` | logado · cada um só os seus |

## Segurança

- **Autenticação**: senha com hash **bcrypt**; login devolve token **JWT** (HS256, 24h). Envie em `Authorization: Bearer <token>`. Sem token / token inválido → **401**.
- **Autorização**: papel `admin` x usuário comum, e regra de **dono do recurso** → **403** quando não permitido.
- **Persistência**: SQLAlchemy ORM com SQLite (`marketplace.db`); trocar para PostgreSQL só mudando `DATABASE_URL` no `.env`.

## Código da API

```
app/api/
  __init__.py            # agrupa os routers em /api/v1
  deps.py                # autenticação (JWT Bearer) e autorização (admin / dono)
  schemas_api.py         # validação Pydantic de entrada e saída
  auth_api.py  usuarios_api.py  tipos_usuario_api.py
  imoveis_api.py  imagens_api.py  interesses_api.py  favoritos_api.py
```

## Coleção Postman / Insomnia

`postman/MarketMovel-IA.postman_collection.json` — 54 requisições em 8 pastas, com testes automáticos de status e
salvamento automático de tokens/IDs. Importe no Postman (ou no Insomnia: *Import > From File*) e rode as pastas em ordem
(ou com o *Collection Runner*). No upload de imagem, selecione o arquivo `postman/imovel_teste.jpg` no campo `arquivos`.

