# Lab 05: Architecture

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI (app.py)
    participant S as SummarizeService
    participant O as OllamaClient
    participant L as Ollama Daemon

    C->>F: POST /summarize { text, model, max_tokens }
    F->>S: summarize(request)
    S->>S: Build prompt string
    S->>O: generate(model, prompt, max_tokens)
    O->>L: POST /api/generate { model, prompt, stream: false }
    L-->>O: { response: "..." }
    O-->>S: summary string
    S-->>F: SummarizeResponse { summary, model, latency_ms }
    F-->>C: 200 OK { summary, model, latency_ms }
```

Error paths:

- Ollama not running: `ConnectError` in `OllamaClient` is caught in `SummarizeService` and raised as HTTP 503.
- Ollama too slow: `TimeoutException` is raised as HTTP 504.
- Invalid request body: Pydantic validation fails before the route handler runs, returning HTTP 422.

## Layer Diagram

```mermaid
graph TD
    subgraph HTTP Layer
        A[app.py\nFastAPI routes\nGET /health\nPOST /summarize]
    end

    subgraph Service Layer
        B[service.py\nSummarizeService\npure async business logic\nerror translation]
    end

    subgraph Client Layer
        C[ollama_client.py\nOllamaClient\nhttpx async HTTP\nOllama /api/generate]
    end

    subgraph Config Layer
        D[config.py\nOllamaLabSettings\nenv var binding\npydantic-settings]
    end

    subgraph Shared
        E[production_labs_shared\nBaseLabSettings\nHealthResponse\nconfigure_logging]
    end

    A --> B
    B --> C
    C --> D
    A --> E
    D --> E
```

## Technology Choices

**FastAPI**: Async-first routing with automatic OpenAPI docs and Pydantic request/response validation.
Chosen over Flask because it handles `async def` route handlers natively, which matters here since
`OllamaClient.generate` is async.

**httpx (async)**: Async HTTP client that integrates cleanly with `async/await`. The synchronous
`requests` library would block the event loop during the Ollama call, degrading concurrency under load.

**Pydantic v2**: Schema validation at the boundary. `SummarizeRequest` enforces `min_length=1` on
`text` and `ge=1, le=2048` on `max_tokens` before the handler is ever called, keeping service.py
free of defensive checks.

**pydantic-settings**: Reads `OLLAMA_BASE_URL`, `OLLAMA_DEFAULT_MODEL`, and `OLLAMA_TIMEOUT_SECONDS`
from environment variables (or `.env` file). Allows the same image to point at different Ollama
instances across local, Docker, and Azure deployments without a rebuild.

**Ollama**: Runs open-weight models (phi3.5, tinyllama) locally via a REST API. No cloud API key
required. The FastAPI wrapper adds production concerns: structured logging, health endpoint,
Pydantic validation, and HTTP error translation.
