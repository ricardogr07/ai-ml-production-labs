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
COPY labs/03-fastmcp-portfolio-tools ./labs/03-fastmcp-portfolio-tools

RUN uv sync --frozen --package fastmcp-portfolio-tools

EXPOSE 8080

CMD ["uv", "run", "--package", "fastmcp-portfolio-tools", \
     "fastmcp", "run", \
     "--transport", "streamable-http", \
     "--port", "8080", \
     "labs/03-fastmcp-portfolio-tools/src/fastmcp_portfolio_tools/server.py"]
