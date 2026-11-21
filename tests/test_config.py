"""Tests for application settings."""

import pytest

from app.config import Settings


def test_defaults_load(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "LLM_PROVIDER",
        "MODEL_NAME",
        "CONFIDENCE_THRESHOLD",
        "MAX_BODY_CHARS",
        "REQUEST_TIMEOUT_S",
        "MAX_RETRIES",
        "CONCURRENCY",
        "DEFAULT_INPUT_PATH",
        "DEFAULT_OUTPUT_DIR",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.LLM_PROVIDER == "gemini"
    assert settings.MODEL_NAME == ""
    assert settings.CONFIDENCE_THRESHOLD == 0.75
    assert settings.MAX_BODY_CHARS == 2000
    assert settings.REQUEST_TIMEOUT_S == 20
    assert settings.MAX_RETRIES == 3
    assert settings.CONCURRENCY == 4
    assert settings.DEFAULT_INPUT_PATH == "candidate/tickets.csv"
    assert settings.DEFAULT_OUTPUT_DIR == "outputs"


def test_environment_overrides_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", "test-model")
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.80")
    monkeypatch.setenv("MAX_BODY_CHARS", "500")
    monkeypatch.setenv("REQUEST_TIMEOUT_S", "10")
    monkeypatch.setenv("MAX_RETRIES", "2")
    monkeypatch.setenv("CONCURRENCY", "8")
    monkeypatch.setenv("DEFAULT_INPUT_PATH", "custom.csv")
    monkeypatch.setenv("DEFAULT_OUTPUT_DIR", "custom-output")

    settings = Settings.from_env()

    assert settings.LLM_PROVIDER == "openai"
    assert settings.MODEL_NAME == "test-model"
    assert settings.CONFIDENCE_THRESHOLD == 0.80
    assert settings.MAX_BODY_CHARS == 500
    assert settings.REQUEST_TIMEOUT_S == 10
    assert settings.MAX_RETRIES == 2
    assert settings.CONCURRENCY == 8
    assert settings.DEFAULT_INPUT_PATH == "custom.csv"
    assert settings.DEFAULT_OUTPUT_DIR == "custom-output"


def test_invalid_threshold_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "1.2")

    with pytest.raises(ValueError, match="CONFIDENCE_THRESHOLD"):
        Settings.from_env()
