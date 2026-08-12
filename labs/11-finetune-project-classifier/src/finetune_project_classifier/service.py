from __future__ import annotations

import threading
from typing import Any

from finetune_project_classifier.config import settings
from finetune_project_classifier.errors import ModelNotReadyError
from finetune_project_classifier.schemas import ProjectRequest, ProjectResponse

_cache: tuple[Any, Any, str] | None = None
_lock = threading.Lock()


def reset_model_cache() -> None:
    global _cache
    with _lock:
        _cache = None


def load_model() -> tuple[Any, Any, str]:
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                if not (settings.model_dir / "config.json").exists():
                    raise ModelNotReadyError(
                        f"No fine-tuned model at {settings.model_dir}; "
                        "run scripts/finetune.py first."
                    )
                from transformers import AutoModelForSequenceClassification, AutoTokenizer

                _cache = (
                    AutoTokenizer.from_pretrained(settings.model_dir),
                    AutoModelForSequenceClassification.from_pretrained(settings.model_dir),
                    "local",
                )
    return _cache


def predict(request: ProjectRequest) -> ProjectResponse:
    import torch

    tokenizer, model, version = load_model()
    encoded = tokenizer(request.description, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        probabilities = torch.softmax(model(**encoded).logits, dim=-1)[0]
    index = int(probabilities.argmax())
    return ProjectResponse(
        label=model.config.id2label[index],
        confidence=float(probabilities[index]),
        model_version=version,
    )
