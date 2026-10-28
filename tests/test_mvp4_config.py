"""
tests/test_mvp4_config.py
=========================
Unit tests for runtime configuration and environment safety invariants.
"""

from __future__ import annotations

import pytest
from src.core.runtime_config import RuntimeConfig


def test_default_config_is_valid(monkeypatch):
    monkeypatch.delenv("AEGIS_ENV", raising=False)
    monkeypatch.delenv("AEGIS_ENVIRONMENT", raising=False)
    monkeypatch.delenv("AEGIS_REQUEST_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("AEGIS_MAX_REQUEST_BYTES", raising=False)
    monkeypatch.delenv("AEGIS_MAX_QUESTION_CHARS", raising=False)
    monkeypatch.delenv("AEGIS_MAX_TOP_K", raising=False)
    monkeypatch.delenv("AEGIS_RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("AEGIS_LOG_LEVEL", raising=False)

    config = RuntimeConfig.from_env()
    assert config.environment == "development"
    assert config.request_timeout_seconds == 60
    assert config.max_request_bytes == 1048576
    assert config.max_question_chars == 4000
    assert config.max_top_k == 20
    assert config.rate_limit_per_minute == 60
    assert config.log_level == "INFO"


def test_invalid_timeout_fails_fast(monkeypatch):
    monkeypatch.setenv("AEGIS_REQUEST_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValueError, match="must be positive"):
        RuntimeConfig.from_env()


def test_negative_timeout_fails_fast(monkeypatch):
    monkeypatch.setenv("AEGIS_REQUEST_TIMEOUT_SECONDS", "-10")
    with pytest.raises(ValueError, match="must be positive"):
        RuntimeConfig.from_env()


def test_non_int_timeout_fails_fast(monkeypatch):
    monkeypatch.setenv("AEGIS_REQUEST_TIMEOUT_SECONDS", "sixty")
    with pytest.raises(ValueError, match="must be an integer"):
        RuntimeConfig.from_env()


def test_invalid_environment_fails_fast(monkeypatch):
    monkeypatch.setenv("AEGIS_ENV", "unknown")
    with pytest.raises(ValueError, match="Unsupported environment"):
        RuntimeConfig.from_env()


def test_invalid_log_level_fails_fast(monkeypatch):
    monkeypatch.setenv("AEGIS_LOG_LEVEL", "TRACE")
    with pytest.raises(ValueError, match="Invalid log level"):
        RuntimeConfig.from_env()


def test_custom_valid_env_variables(monkeypatch):
    monkeypatch.setenv("AEGIS_ENV", "production")
    monkeypatch.setenv("AEGIS_REQUEST_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("AEGIS_MAX_REQUEST_BYTES", "2097152")
    monkeypatch.setenv("AEGIS_MAX_QUESTION_CHARS", "2000")
    monkeypatch.setenv("AEGIS_MAX_TOP_K", "10")
    monkeypatch.setenv("AEGIS_RATE_LIMIT_PER_MINUTE", "120")
    monkeypatch.setenv("AEGIS_LOG_LEVEL", "WARNING")

    config = RuntimeConfig.from_env()
    assert config.environment == "production"
    assert config.request_timeout_seconds == 45
    assert config.max_request_bytes == 2097152
    assert config.max_question_chars == 2000
    assert config.max_top_k == 10
    assert config.rate_limit_per_minute == 120
    assert config.log_level == "WARNING"
