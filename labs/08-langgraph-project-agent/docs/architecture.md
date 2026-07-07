# Lab 08: Architecture

## Component diagram

```mermaid
graph TD
    Settings["Settings\n(BaseLabSettings)"]
    Graph["StateGraph\n(graph.py, linear)"]
    State["ProjectState\n(typed Pydantic state)"]
    Nodes["Node functions\n(nodes.py)"]
    Heuristics["Deterministic heuristics\n(LLM_PROVIDER=none)"]
    LLM["llm.py\nstructured-output nodes"]
    Factory["get_chat_model()\n(lru_cache factory)"]
    Ollama["ChatOllama\n(local or dockerized,\njson_schema decoding)"]
    Anthropic["ChatAnthropic\n(claude-opus-4-8)"]

    State --> Graph
    Graph --> Nodes
    Settings --> Nodes
    Nodes -->|"provider none"| Heuristics
    Nodes -->|"provider ollama/anthropic"| LLM
    LLM --> Factory
    Factory -->|"LLM_PROVIDER=ollama"| Ollama
    Factory -->|"LLM_PROVIDER=anthropic"| Anthropic
```

## Graph flow

```mermaid
sequenceDiagram
    participant C as CLI (__main__.py)
    participant G as compiled_graph
    participant N as nodes.py
    participant L as llm.py (provider != none)

    C->>G: invoke(ProjectState(project_idea))
    G->>N: classify_project_type
    N->>L: llm_classify -> ClassifyResult
    G->>N: score_against_portfolio_thesis
    N->>L: llm_score -> ThesisScoreResult (0..1)
    G->>N: identify_missing_artifacts
    N->>L: llm_missing_artifacts -> MissingArtifactsResult
    G->>N: generate_implementation_plan
    N->>L: llm_plan -> PlanResult
    G->>N: return_scorecard (always deterministic)
    G-->>C: scorecard dict
    C-->>C: assert keys, print JSON, exit code
```

## Design notes

**Explicit workflow over black-box agent**

The graph is a fixed, linear `StateGraph` whose nodes each perform one typed
transformation on `ProjectState`. There is no tool loop and no model-driven
control flow: the LLM is used per node as a structured-output function, which
keeps behavior testable and the failure surface per node.

**Three provider tiers behind one dispatch**

`LLM_PROVIDER` selects the tier at the node boundary. `none` (default) runs
keyword heuristics with zero dependencies, which keeps unit tests hermetic
and the CLI usable offline. `ollama` and `anthropic` share one code path:
`get_chat_model()` returns a LangChain chat model and every node calls
`.with_structured_output(PydanticModel)`, so responses are validated objects,
not parsed strings. The heuristics were kept rather than deleted so the
deterministic tier remains a permanent regression baseline.

**Ollama structured output via constrained decoding**

`ChatOllama` defaults to tool calling for structured output, which small
local models (phi3.5, tinyllama) do not support. The ollama branch passes
`method="json_schema"`, using Ollama's constrained decoding so any model
emits schema-valid JSON. The Anthropic branch uses the default tool-based
path, which claude-opus-4-8 handles natively.

**Configuration**

`Settings` extends the shared `BaseLabSettings` and reads both the repo-root
`.env` and the lab-local `.env` (lab-local wins). `ANTHROPIC_API_KEY` flows
from either file through `Settings` into the factory, falling back to the
process environment; empty values are treated as unset.

**Deployment surfaces**

Local: CLI via `python -m langgraph_project_agent`, doubling as the smoke
test. CI per PR: unit tests in the tox gates plus an e2e job against the
Anthropic API. Manual dispatch: Terraform deploys a one-shot agent container
(Azure Container Instance, key as secure env var) whose logs CI asserts, and
an Ollama ACI that integration tests run against; both are destroyed at the
end of every run.
