# Lab 10: Architecture

## Component diagram

```mermaid
graph TD
    Settings["Settings\n(BaseLabSettings)"]
    Train["scripts/train.py\n(fit + log + register + promote)"]
    Store["MLflow tracking store\n(sqlite: runs, metrics, registry)"]
    Artifacts["Artifact tree\n(mlruns/<experiment_id>)"]
    App["app.py\n(FastAPI: /health, /ready, /predict)"]
    Ready["readiness.py\n(check_model)"]
    Service["service.py\n(load_model, predict)"]
    Cache["_MODEL_CACHE\n(process-local, lock-guarded)"]
    Resolve["_resolve_and_load()"]

    Settings --> Train
    Settings --> Service
    Train --> Store
    Train --> Artifacts
    App --> Ready
    App --> Service
    Ready --> Service
    Service --> Cache
    Cache -->|"miss"| Resolve
    Resolve -->|"MODEL_URI pin"| Store
    Resolve -->|"models:/name@alias"| Store
    Resolve -->|"runs:/id/artifact"| Store
    Store --> Artifacts
```

## Predict flow

```mermaid
sequenceDiagram
    participant C as Client (POST /predict)
    participant A as app.py
    participant S as service.py
    participant K as _MODEL_CACHE
    participant M as MLflow store + artifacts

    C->>A: IncidentFeatures
    A->>S: predict(features)
    S->>K: load_model()
    alt cache hit
        K-->>S: (model, version)
    else cache miss
        S->>S: acquire _LOAD_LOCK, re-check
        S->>M: resolve MODEL_URI, else alias, else latest run
        M-->>S: artifact
        S->>S: verify feature order, label set, predict_proba
        S->>K: cache (model, version)
    end
    S->>S: build one-row frame in FEATURE_COLUMNS order
    S->>S: predict_proba, argmax
    S-->>A: SeverityResponse(severity, confidence, model_version)
    A-->>C: 200
    Note over A,S: ModelNotReady at any resolve or verify step maps to 503, never 500
```

## Design notes

**Train and serve share one setting, not one convention**

`train.py` and `service.py` both read `settings.mlflow_tracking_uri` and
`settings.mlflow_experiment`, so an operator who overrides `MLFLOW_TRACKING_URI`
moves both halves together. Splitting them is the failure mode this prevents:
training into one store while serving from another produces a successful
training run and a permanent 503, with nothing in either log saying why.

**Registry alias as the promotion boundary**

`train.py` registers each run as a new version of `severity-classifier` and
moves the `champion` alias to it. The API resolves
`models:/severity-classifier@champion` on every load, so promotion is what makes
a model live; retraining without moving the alias changes nothing that serves.
Promotion is unconditional here because the lab trains on a fixed seed. A real
pipeline gates it on the eval metric beating the incumbent, which is a
three-line change in `promote_latest_version` and no change at all on the
serving side. That asymmetry is the point of the alias.

**Lazy load, not import-time load**

The model resolves on first use, never at import. An empty tracking store is a
normal state (fresh volume, fresh deployment, before the first train), and an
import-time load turns it into a crash loop that hides the actual cause behind a
restarting container. Loading late means `/health` answers 200 and `/ready`
answers a 503 that names the missing piece.

The load is single-flight via double-checked locking: concurrent first requests
trigger one load rather than a thundering herd against the artifact store. The
cache holds only successes. A failed load is never cached, so an instance that
has only ever 503'd starts serving on the next request after a train, with no
restart. This is what the compose `train` one-off relies on.

**Resolution order and why the fallback exists**

`MODEL_URI`, then the registry alias, then the latest finished run in the
experiment.

`MODEL_URI` is the explicit escape hatch: pin an exact version
(`models:/severity-classifier/3`) or an exact run and skip the registry
entirely. Useful for rollback and for reproducing an incident against the model
that caused it.

The latest-run fallback keeps a store written before the registry existed
servable. It is scoped to `settings.mlflow_experiment` and filtered to
`status = 'FINISHED'`, so a crashed run and a newer run from an unrelated
experiment are both invisible to it. Without the scope, an unrelated experiment
in the same store would silently take over serving.

**Readiness is one dependency, checked by loading it**

`readiness()` calls the same `load_model()` the predict path calls, so `/ready`
cannot report healthy on a model `/predict` would fail to load. It returns a
per-dependency dict rather than raising, and the route maps a non-`ok` value to
503; the check function itself has no opinion about HTTP.

**Four ways to be unready, all one status code**

The load path rejects an artifact that is present but wrong, not just an absent
one:

| Condition | Message names |
|---|---|
| No registered alias and no finished run | the registry entry, or the experiment |
| `feature_names_in_` differs from `FEATURE_COLUMNS` | both column lists |
| `classes_` contains a label outside the four | the offending labels and the contract |
| No callable `predict_proba` | the missing method |

All four are `ModelNotReady`, all four surface as 503 with an actionable
message. A model trained on reordered columns would otherwise predict
confidently from misaligned features, which is worse than a 503: silently wrong
output that looks like a working service.

**Error messages never carry the tracking URI**

`ModelNotReady` messages reach unauthenticated callers, and a tracking URI can
carry credentials (`postgresql://user:pass@host/db`). So the messages name the
registry entry, the alias, or the experiment, and the generic load failure says
only "see server logs for the cause". The full exception, URI included, goes to
the log via `logger.exception`.

**Configuration**

`Settings` extends the shared `BaseLabSettings` and reads the repo-root `.env`
plus the lab-local one (lab-local wins). `protected_namespaces` is cleared so
the `model_uri` field name is allowed alongside pydantic's `model_` prefix.

| Variable | Default | Purpose |
|---|---|---|
| `MLFLOW_TRACKING_URI` | `sqlite:///mlflow.db` | Store both halves read. Relative, so run `train.py` and `uvicorn` from the same directory |
| `MLFLOW_EXPERIMENT` | `severity-classifier` | Scopes the latest-run fallback |
| `REGISTERED_MODEL_NAME` | `severity-classifier` | Registry entry trained into and served from |
| `MODEL_ALIAS` | `champion` | Alias promotion moves and serving resolves |
| `MODEL_URI` | unset | Exact pin; wins over the alias when set |

sqlite rather than a file store: MLflow put the file store in maintenance mode
in 3.14, and the model registry the serving path depends on requires a DB
backend.

**Deployment surfaces**

Local: `uv run` the trainer, then uvicorn, both against `./mlflow.db`.

Compose: a named volume at `/app/mlruns` holds the sqlite DB and the artifact
tree together, with training as a one-off service. The mount point is load
bearing. With a DB backend MLflow writes artifacts to
`<cwd>/mlruns/<experiment_id>`, so a volume anywhere else would share run
metadata between the two services but not the model files, and the API would 503
on a run that trained successfully.

Container image: trains at build time so the artifact ships inside. Azure
Container Apps has no persistent volume by default, so a non-baked image serves
503 until someone shells in and trains. Baking is honest here only because the
training data is synthetic and seeded; with real data the artifact has to come
from a mounted store or a tracking server.

Azure Container Apps: one container app on the shared environment, scale to
zero, image pulled from GHCR. Cost profile is the reason for scale-to-zero.
An idle replica count of zero means the lab costs nothing between demos, paying
only per request plus the shared environment, at the price of a cold start on
the first call after idle. That trade is right for a portfolio lab and wrong for
a latency-sensitive service, where a minimum replica of one would be the call.

CI per PR: the tox gates plus the lab Dockerfile build, which exercises the
build-time train on every change.
