FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY shared ./shared
COPY labs/02-azure-functions-text-classifier ./labs/02-azure-functions-text-classifier

RUN uv sync --frozen --package azure-functions-text-classifier

FROM mcr.microsoft.com/azure-functions/python:4-python3.12

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /home/site/wwwroot

# Copy venv site-packages (third-party deps) to the Azure Functions .python_packages path
# (auto-prepended to sys.path by the Azure Functions host)
COPY --from=builder /build/.venv/lib/python3.12/site-packages \
                    .python_packages/lib/site-packages

# Copy workspace package source directly: the venv editable install only has a .pth pointer
# to /build/shared/src which will not exist at runtime
COPY shared/src .python_packages/lib/site-packages/

COPY labs/02-azure-functions-text-classifier/src/azure_functions_text_classifier \
     ./azure_functions_text_classifier

COPY labs/02-azure-functions-text-classifier/host.json ./

RUN printf 'from azure_functions_text_classifier.function_app import app\n' > function_app.py
