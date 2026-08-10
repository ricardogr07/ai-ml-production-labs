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
COPY labs/10-mlflow-classifier-api ./labs/10-mlflow-classifier-api

RUN uv sync --frozen --package mlflow-classifier-api

# Non-root before the training layer, not after: the image ships a tracking
# store, and MLflow's sqlalchemy backend opens the sqlite file read-write even
# to read, so the runtime user has to own it. Training as `app` gets that for
# free and leaves the artifact tree unwritable by anyone else.
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

# Bake a trained model so the cloud image serves on first request: Azure
# Container Apps has no persistent volume, and the alias would otherwise
# resolve to nothing until someone shelled in to train.
# ponytail: reproducible only because the training data is synthetic and
# seeded (rng.default_rng(42)). Real data needs a mounted store or a tracking
# server; docker-compose.yml already takes the mounted-store path locally.
RUN uv run --frozen --package mlflow-classifier-api python labs/10-mlflow-classifier-api/scripts/train.py

EXPOSE 8000

# --frozen: a plain `uv run` re-resolves at container start, which can install
# a different dependency set than `uv sync --frozen` just baked.
CMD ["uv", "run", "--frozen", "--package", "mlflow-classifier-api", "uvicorn", "mlflow_classifier_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
