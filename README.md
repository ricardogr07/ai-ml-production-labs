# AI/ML Production Labs

A monorepo of focused, production-shaped micro-labs proving concrete AI, ML, data science, and cloud engineering capabilities.

Each lab is small in scope and production-grade in discipline: typed code, tests, CI, Docker, infrastructure, and observability.

---

## Monorepo structure

```text
ai-ml-production-labs/
  shared/                          # Shared utilities (logging, health, config, telemetry)
  labs/
    01-fastapi-azure-ml-service/   # Containerized FastAPI service on Azure Container Apps
    02-azure-functions-text-classifier/
    03-fastmcp-portfolio-tools/
    04-cosmosdb-llm-eval-store/
    05-ollama-local-llm-api/
    06-cosmosdb-vector-memory-lab/
    07-rag-retrieval-strategy-lab/
    08-langgraph-project-agent/
    09-llamaindex-doc-qa-lab/
    10-mlflow-classifier-api/
    11-finetune-project-classifier/
    12-ml-drift-monitoring-lab/
    13-fastapi-opentelemetry-lab/
    14-portfolio-ai-production-capstone/
  docs/
    architecture-gallery.md
    lab-template.md
  infra/azure/
  scripts/
  .github/workflows/
```

---

## Tooling

| Tool | Purpose |
|---|---|
| Python 3.12 | Language |
| uv workspaces | Dependency management and monorepo packaging |
| tox + tox-uv | CI task runner |
| pytest | Testing |
| ruff | Linting and formatting |
| pyrefly | Type checking |
| bandit | Security scanning |
| pip-audit | Dependency vulnerability audit |
| pre-commit | Git hooks |
| Docker | Containerization |
| Azure Container Apps | Containerized service deployment |
| Azure Functions | Serverless deployment |
| Terraform | Infrastructure as code |

---

## Quick start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync all workspace packages
uv sync --all-packages

# Run quality gates
uv run tox -e lint,type,py312,security,audit

# Run a specific lab
uv run --package fastapi-azure-ml-service uvicorn fastapi_azure_ml_service.app:app --reload
```

---

## Labs

| Lab | Capability | Status |
|---|---|---|
| [01 FastAPI Azure ML Service](labs/01-fastapi-azure-ml-service/README.md) | Containerized FastAPI service on Azure Container Apps | Ready |
| [02 Azure Functions Text Classifier](labs/02-azure-functions-text-classifier/README.md) | Serverless Python inference endpoint | Ready |
| [03 FastMCP Portfolio Tools](labs/03-fastmcp-portfolio-tools/README.md) | MCP server with typed portfolio analysis tools | Ready |
| [04 Cosmos DB LLM Eval Store](labs/04-cosmosdb-llm-eval-store/README.md) | NoSQL model for LLM evaluation workflows | Ready |
| [05 Ollama Local LLM API](labs/05-ollama-local-llm-api/README.md) | FastAPI wrapper around local open-model LLM | Ready |
| [06 Cosmos DB Vector Memory Lab](labs/06-cosmosdb-vector-memory-lab/README.md) | Embedding storage and vector search | Ready |
| [07 RAG Retrieval Strategy Lab](labs/07-rag-retrieval-strategy-lab/README.md) | Compare retrieval strategies with metrics | Ready |
| [08 LangGraph Project Agent](labs/08-langgraph-project-agent/README.md) | Three-tier LLM agent workflow (deterministic, Ollama, Anthropic) on a state graph | Ready |
| [09 LlamaIndex Doc Q&A](labs/09-llamaindex-doc-qa-lab/README.md) | Containerized RAG over a Wikipedia corpus in Qdrant, generating with Ollama or Anthropic | Scaffold |
| [10 MLflow Classifier API](labs/10-mlflow-classifier-api/README.md) | Classical ML model trained, tracked, and served | Scaffold |
| [11 Fine-tuned Project Classifier](labs/11-finetune-project-classifier/README.md) | Fine-tune a small model with before/after metrics | Scaffold |
| [12 ML Drift Monitoring Lab](labs/12-ml-drift-monitoring-lab/README.md) | Detect data drift between reference and current data | Scaffold |
| [13 FastAPI OpenTelemetry Lab](labs/13-fastapi-opentelemetry-lab/README.md) | Traces, metrics, and structured logs for a FastAPI service | Scaffold |
| [14 Portfolio AI Production Capstone](labs/14-portfolio-ai-production-capstone/README.md) | Integrated production-shaped AI service | Scaffold |

---

## CI

Every pull request runs:

1. Dependency sync check
2. Formatting check (ruff)
3. Linting (ruff)
4. Type checking (pyrefly)
5. Unit and integration tests (pytest)
6. Coverage gate (≥ 60%, raised per lab as labs complete)
7. Security scan (bandit)
8. Dependency audit (pip-audit)
9. Docker build for deployable labs
10. Anthropic API e2e for lab 08 (skips when the secret is unavailable)

On demand, `integration-test.yml` (workflow dispatch) deploys a chosen lab to Azure with Terraform, runs its smoke and integration tests against the live deployment, and always tears the resources down, with a tag-based sweep as the safety net.

---

## Definition of done

A lab is done when:

- README explains what it proves
- Local setup works from clean clone
- Tests pass through tox
- Linting passes
- Type checks pass
- Docker image builds (if service-based)
- Smoke test exists
- Infra template exists (if cloud-based)
- CI workflow runs
- Results are documented
- Tradeoffs are documented
