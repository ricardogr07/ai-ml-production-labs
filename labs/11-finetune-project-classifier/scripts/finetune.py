from __future__ import annotations

import json

from datasets import Dataset
from finetune_project_classifier.config import settings
from finetune_project_classifier.dataset import LABEL_TO_ID, LABELS, SAMPLES
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


def main() -> None:
    texts, labels = zip(*SAMPLES, strict=True)
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=0.33, random_state=42, stratify=labels
    )
    tokenizer = AutoTokenizer.from_pretrained(
        settings.base_model, revision=settings.base_model_revision
    )

    def encode(row):
        return tokenizer(row["text"], truncation=True, max_length=128)

    train = Dataset.from_dict(
        {"text": list(train_texts), "labels": [LABEL_TO_ID[x] for x in train_labels]}
    ).map(encode, batched=True)
    test = Dataset.from_dict(
        {"text": list(test_texts), "labels": [LABEL_TO_ID[x] for x in test_labels]}
    ).map(encode, batched=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        settings.base_model,
        revision=settings.base_model_revision,
        num_labels=len(LABELS),
        id2label=dict(enumerate(LABELS)),
        label2id=LABEL_TO_ID,
    )

    def compute_metrics(eval_prediction):
        predictions, labels = eval_prediction
        return {"accuracy": float((predictions.argmax(axis=-1) == labels).mean())}

    args = TrainingArguments(
        output_dir=str(settings.model_dir / "runs"),
        num_train_epochs=2,
        per_device_train_batch_size=4,
        learning_rate=5e-5,
        logging_strategy="no",
        save_strategy="no",
        report_to=[],
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train,
        eval_dataset=test,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )
    baseline_metrics = trainer.evaluate()
    trainer.train()
    metrics = trainer.evaluate()
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(settings.model_dir)
    tokenizer.save_pretrained(settings.model_dir)
    (settings.model_dir / "metrics.json").write_text(
        json.dumps(
            {
                "baseline_accuracy": baseline_metrics.get("eval_accuracy", 0.0),
                "fine_tuned_accuracy": metrics.get("eval_accuracy", 0.0),
                "samples": len(SAMPLES),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2, default=float))


if __name__ == "__main__":
    main()
