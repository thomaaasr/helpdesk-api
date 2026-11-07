# Etapa 1: instala as dependências com o uv.
FROM python:3.14-slim AS construcao

COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# Etapa 2: imagem final, sem o uv e só com o necessário para rodar.
FROM python:3.14-slim

RUN useradd --create-home app

WORKDIR /app
COPY --from=construcao /app/.venv ./.venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"

USER app
EXPOSE 8000

# Aplica as migrações e sobe a API. O Render informa a porta na variável PORT.
CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --port ${PORT:-8000}"]
