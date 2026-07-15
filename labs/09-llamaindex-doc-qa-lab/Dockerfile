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
COPY labs/09-llamaindex-doc-qa-lab ./labs/09-llamaindex-doc-qa-lab

RUN uv sync --frozen --package llamaindex-doc-qa-lab

# Pre-warm the HuggingFace embedding model cache at build time, so ACA
# scale-to-zero cold starts don't re-download it on every first request.
# --frozen here too: a plain `uv run` re-resolves and silently reinstalls the
# full CUDA build of torch over the CPU-only one `uv sync --frozen` just installed.
RUN uv run --frozen --package llamaindex-doc-qa-lab python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8000

CMD ["uv", "run", "--frozen", "--package", "llamaindex-doc-qa-lab", "uvicorn", "llamaindex_doc_qa_lab.app:app", "--host", "0.0.0.0", "--port", "8000"]
