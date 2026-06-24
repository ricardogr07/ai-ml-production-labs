FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY labs/05-ollama-local-llm-api ./labs/05-ollama-local-llm-api

RUN uv sync --frozen --package ollama-local-llm-api

EXPOSE 8000

CMD ["uv", "run", "--package", "ollama-local-llm-api", "uvicorn", "ollama_local_llm_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
