FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY labs/08-langgraph-project-agent ./labs/08-langgraph-project-agent

RUN uv sync --frozen --package langgraph-project-agent

ENTRYPOINT ["uv", "run", "--package", "langgraph-project-agent", "python", "-m", "langgraph_project_agent"]
CMD ["A FastAPI RAG service on Azure with pytest coverage and a Dockerfile"]
