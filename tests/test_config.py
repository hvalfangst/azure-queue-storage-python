"""Tests for the StorageAccountConfiguration pydantic-settings model."""
import os
import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class _MinimalConfig(BaseSettings):
    """Isolated copy of the config model so tests don't depend on module-level state."""
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
    )
    CONNECTION_STRING: str
    QUEUE_NAME: str


def test_config_loads_from_env(monkeypatch):
    monkeypatch.setenv("CONNECTION_STRING", "my-connection-string")
    monkeypatch.setenv("QUEUE_NAME", "my-queue")

    cfg = _MinimalConfig()

    assert cfg.CONNECTION_STRING == "my-connection-string"
    assert cfg.QUEUE_NAME == "my-queue"


def test_config_missing_connection_string(monkeypatch):
    monkeypatch.delenv("CONNECTION_STRING", raising=False)
    monkeypatch.setenv("QUEUE_NAME", "my-queue")

    with pytest.raises(ValidationError):
        _MinimalConfig()


def test_config_missing_queue_name(monkeypatch):
    monkeypatch.setenv("CONNECTION_STRING", "my-connection-string")
    monkeypatch.delenv("QUEUE_NAME", raising=False)

    with pytest.raises(ValidationError):
        _MinimalConfig()


def test_config_ignores_extra_env_vars(monkeypatch):
    monkeypatch.setenv("CONNECTION_STRING", "conn")
    monkeypatch.setenv("QUEUE_NAME", "q")
    monkeypatch.setenv("SOME_OTHER_VAR", "irrelevant")

    cfg = _MinimalConfig()  # should not raise
    assert cfg.CONNECTION_STRING == "conn"
