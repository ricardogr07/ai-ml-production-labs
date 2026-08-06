#!/usr/bin/env python3
"""Train and log a severity classifier with MLflow."""

from __future__ import annotations

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from mlflow_classifier_api.config import settings
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

LABELS = ["low", "medium", "high", "critical"]


def generate_synthetic_data(n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {
            "error_count": rng.integers(0, 100, n),
            "latency_p95_ms": rng.uniform(10, 5000, n),
            "failed_jobs": rng.integers(0, 20, n),
            "deployment_recent": rng.choice([0, 1], n),
        }
    )
    data["severity"] = pd.cut(
        data["error_count"] + data["failed_jobs"] * 3,
        bins=[-1, 10, 30, 60, 200],
        labels=LABELS,
    ).astype(str)
    return data


def main() -> None:
    # Log to the same store the API serves from; both read the same setting, so
    # an operator who overrides MLFLOW_TRACKING_URI cannot split train from serve.
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    # Same experiment the API's latest-run lookup is scoped to.
    mlflow.set_experiment(settings.mlflow_experiment)
    df = generate_synthetic_data()
    features = df.drop("severity", axis=1)
    y = df["severity"]
    x_train, x_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)

    with mlflow.start_run():
        params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
        mlflow.log_params(params)

        model = RandomForestClassifier(**params)
        model.fit(x_train, y_train)

        preds = model.predict(x_test)
        report = classification_report(y_test, preds, output_dict=True)
        mlflow.log_metric("accuracy", report["accuracy"])

        # cloudpickle, not the 3.14 skops default: skops import scans
        # sys.modules and breaks when transformers is loaded without
        # torchvision (as in this repo's CPU-only test env).
        mlflow.sklearn.log_model(
            model,
            "severity_classifier",
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )
        print(classification_report(y_test, preds))


if __name__ == "__main__":
    main()
