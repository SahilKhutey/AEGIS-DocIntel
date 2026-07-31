"""
AMDI-OS — Configuration
========================
Loaded from environment variables + config/settings.yaml.
"""
from __future__ import annotations
import os
from functools import lru_cache
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_SETTINGS_CONFIG = True
except ImportError:
    from pydantic import BaseSettings, Field  # type: ignore
    HAS_SETTINGS_CONFIG = False


class AMDISettings(BaseSettings):
    if HAS_SETTINGS_CONFIG:
        model_config = SettingsConfigDict(
            env_prefix="AMDI_",
            env_file=".env",
            case_sensitive=False,
            extra="ignore",
        )
    else:
        class Config:
            env_prefix = "AMDI_"
            env_file = ".env"
            case_sensitive = False
    # App
    env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me"

    # API
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Storage
    sqlite_path: str = "data/amdi.db"
    duckdb_path: str = "data/amdi.duckdb"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # LLM
    llm_provider: str = "mock"
    llm_model: str = "gpt-4o"
    llm_endpoint: str = ""
    llm_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # Models
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_dim: int = 1024
    reranker_model: str = "BAAI/bge-reranker-large"

    # Compute
    device: str = "cpu"
    ocr_engine: str = "tesseract"

    # Context
    max_context_tokens: int = 4096
    target_context_tokens: int = 1500
    top_k: int = 12

    # Upload
    max_file_size_mb: int = 100


@lru_cache
def get_settings() -> AMDISettings:
    return AMDISettings()


settings = get_settings()
