FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY labs/11-finetune-project-classifier ./labs/11-finetune-project-classifier
RUN uv sync --frozen --package finetune-project-classifier
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app
RUN uv run --frozen --package finetune-project-classifier python labs/11-finetune-project-classifier/scripts/finetune.py
EXPOSE 8000
CMD ["uv", "run", "--frozen", "--package", "finetune-project-classifier", "uvicorn", "finetune_project_classifier.app:app", "--host", "0.0.0.0", "--port", "8000"]
