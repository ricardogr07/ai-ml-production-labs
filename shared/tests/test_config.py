from __future__ import annotations

import pytest

from production_labs_shared.config import BaseLabSettings


@pytest.mark.unit
def test_base_lab_settings_defaults() -> None:
    settings = BaseLabSettings()

    assert settings.environment == "local"
    assert settings.log_level == "INFO"
    assert settings.otel_service_name == "ai-ml-production-lab"
    assert settings.otel_exporter_otlp_endpoint == ""


@pytest.mark.unit
def test_base_lab_settings_override_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = BaseLabSettings()

    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
