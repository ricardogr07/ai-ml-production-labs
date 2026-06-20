from __future__ import annotations

import pytest

from finetune_project_classifier.dataset import LABELS, LABEL_TO_ID, ID_TO_LABEL, SAMPLES


@pytest.mark.unit
def test_label_maps_are_consistent() -> None:
    assert len(LABELS) == len(LABEL_TO_ID) == len(ID_TO_LABEL)
    for label in LABELS:
        assert ID_TO_LABEL[LABEL_TO_ID[label]] == label


@pytest.mark.unit
def test_all_samples_have_valid_labels() -> None:
    for text, label in SAMPLES:
        assert label in LABELS, f"Unknown label: {label}"
        assert len(text) > 0


@pytest.mark.unit
def test_dataset_covers_all_labels() -> None:
    covered = {label for _, label in SAMPLES}
    assert covered == set(LABELS)
