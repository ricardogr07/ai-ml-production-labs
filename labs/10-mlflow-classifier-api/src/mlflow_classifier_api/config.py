from __future__ import annotations

from pathlib import Path

from pydantic_settings import SettingsConfigDict

from production_labs_shared.config import BaseLabSettings

_LAB_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseLabSettings):
    # reads the CWD .env (repo root) plus the lab-local .env; lab-local wins.
    # protected_namespaces cleared so the model_uri field name is allowed.
    model_config = SettingsConfigDict(
        env_file=(".env", _LAB_ENV), extra="ignore", protected_namespaces=()
    )

    # sqlite, not a file store: MLflow put the file store in maintenance mode
    # in 3.14, and the model registry the serving path uses needs a DB backend.
    # CWD-relative, so run train.py and uvicorn from the same directory.
    mlflow_tracking_uri: str = "sqlite:///mlflow.db"
    # Training and serving share this experiment; the latest-run lookup is
    # scoped to it, so a newer run from an unrelated experiment is never served.
    mlflow_experiment: str = "severity-classifier"
    # Optional pin to an exact model (e.g. "runs:/<run_id>/severity_classifier");
    # unset means serve the latest finished run.
    model_uri: str | None = None


settings = Settings()
