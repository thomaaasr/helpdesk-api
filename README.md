# Help Desk API

![CI](https://github.com/thomaaasr/helpdesk-api/actions/workflows/ci.yml/badge.svg)

**Demo:** [helpdesk-api-ii2o.onrender.com/docs](https://helpdesk-api-ii2o.onrender.com/docs) (a primeira chamada pode levar cerca de 1 minuto, porque o servidor gratuito dorme quando fica parado)

API REST de chamados de TI, feita com **Python e FastAPI**. Controla o ciclo completo de um chamado: abertura, atendimento por um técnico, comentários, prazo de SLA conforme a prioridade e fechamento.

## Tecnologias

- **Python 3.14**, **FastAPI** e **Pydantic**
- **PostgreSQL**, **SQLAlchemy 2** e **Alembic** (migrações)
- **JWT** (PyJWT) e senhas com hash **Argon2**
- **pytest**, **Ruff** e **uv**
- **Docker**, **Docker Compose** e **GitHub Actions**

## Regras de negócio

- Quem se cadastra é sempre `solicitante`. O perfil `tecnico` só é dado por um comando no servidor.
- O solicitante vê apenas os próprios chamados. O técnico vê todos.
- Fluxo do chamado: `aberto` → `em_atendimento` → `resolvido` → `fechado`, sem pular etapas.
- Só um técnico assume um chamado, e só o técnico responsável marca como resolvido.
- Depois de resolvido, o solicitante ou um técnico fecha ou reabre o chamado.
- Chamado fechado não aceita edição nem comentário.
- Somente técnicos alteram a prioridade, e o prazo é recalculado.

| Prioridade | Prazo (horas corridas) |
| ---------- | ---------------------- |
| `critica`  | 4                      |
| `alta`     | 8                      |
| `media`    | 24                     |
| `baixa`    | 72                     |

## Rotas

| Método | Rota                         | Descrição                                                     |
| ------ | ---------------------------- | ------------------------------------------------------------- |
| POST   | `/auth/cadastro`             | Cria um usuário                                               |
| POST   | `/auth/login`                | Devolve o token JWT                                           |
| GET    | `/auth/eu`                   | Mostra o usuário logado                                       |
| POST   | `/chamados`                  | Abre um chamado                                               |
| GET    | `/chamados`                  | Lista com filtros (status, prioridade, atrasados) e paginação |
| GET    | `/chamados/{id}`             | Detalha um chamado                                            |
| PATCH  | `/chamados/{id}`             | Altera título, descrição ou prioridade                        |
| POST   | `/chamados/{id}/assumir`     | Técnico assume o chamado                                      |
| PATCH  | `/chamados/{id}/status`      | Resolve, fecha ou reabre                                      |
| POST   | `/chamados/{id}/comentarios` | Comenta no chamado                                            |
| GET    | `/chamados/{id}/comentarios` | Lista os comentários                                          |

A documentação interativa (Swagger) fica em `/docs`.

## Rodando com Docker

```bash
docker compose up --build
```

A API sobe em http://127.0.0.1:8000/docs, já com o PostgreSQL e as migrações aplicadas.

Para transformar um usuário em técnico:

```bash
docker compose exec api python -m app.auth.promover email@exemplo.com
```

## Rodando sem Docker

Precisa do [uv](https://docs.astral.sh/uv/) e de um PostgreSQL com os bancos `helpdesk` e `helpdesk_teste`.

```bash
uv sync
cp .env.example .env   # depois preencha a senha do banco e o JWT_SECRET
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

## Testes e qualidade

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Os testes usam um banco PostgreSQL separado, definido em `DATABASE_URL_TESTE`. O GitHub Actions roda tudo a cada push, incluindo as migrações e o build da imagem Docker.
