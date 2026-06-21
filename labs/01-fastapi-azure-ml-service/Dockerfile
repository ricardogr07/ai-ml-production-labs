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
COPY labs/01-fastapi-azure-ml-service ./labs/01-fastapi-azure-ml-service

RUN uv sync --frozen --package fastapi-azure-ml-service

EXPOSE 8000

CMD ["uv", "run", "--package", "fastapi-azure-ml-service", "uvicorn", "fastapi_azure_ml_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
