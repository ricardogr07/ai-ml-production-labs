from __future__ import annotations

from fastapi_azure_ml_service.schemas import PredictRequest, PredictResponse


class PredictionService:
    """Deterministic rule-based scorer used as the lab boundary."""

    model_version = "rules-v0.1.0"

    def predict(self, request: PredictRequest) -> PredictResponse:
        text = request.text.lower()
        if any(kw in text for kw in ("error", "failed", "timeout", "crash", "outage")):
            return PredictResponse(
                label="incident",
                confidence=0.85,
                model_version=self.model_version,
            )
        if any(kw in text for kw in ("deploy", "release", "rollout", "migration")):
            return PredictResponse(
                label="deployment",
                confidence=0.75,
                model_version=self.model_version,
            )
        return PredictResponse(
            label="general",
            confidence=0.65,
            model_version=self.model_version,
        )
