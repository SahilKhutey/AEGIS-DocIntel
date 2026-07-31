"""
AEGIS-DocIntel — Centralized Configuration
==========================================
Pydantic Settings v2 loader with YAML + environment variable support.
Environment variables override YAML values using double-underscore notation.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ─────────────────────────────────────────────────────────────────
# Config Sub-schemas
# ─────────────────────────────────────────────────────────────────

class AppConfig(BaseModel):
    name: str = "aegis-docintel"
    version: str = "1.0.0"
    env: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    max_upload_mb: int = 200
    cors_origins: List[str] = ["*"]


class S3Config(BaseModel):
    endpoint: str
    access_key: str
    secret_key: str
    bucket_raw: str = "aegis-raw"
    bucket_derived: str = "aegis-derived"
    bucket_images: str = "aegis-images"
    region: str = "us-east-1"


class StorageConfig(BaseModel):
    s3: S3Config


class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "aegis"
    password: str = ""
    db: str = "aegis"
    pool_min: int = 5
    pool_max: int = 20

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_dsn(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379"
    max_connections: int = 100
    decode_responses: bool = True


class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    topic_ingest: str = "doc.ingest"
    topic_indexed: str = "doc.indexed"
    topic_failed: str = "doc.failed"
    topic_reindex: str = "doc.reindex"
    consumer_group: str = "aegis-workers"


class MilvusConfig(BaseModel):
    host: str = "localhost"
    port: int = 19530
    collection_text: str = "chunks_text"
    collection_visual: str = "chunks_visual"


class ElasticsearchConfig(BaseModel):
    hosts: List[str] = ["http://localhost:9200"]
    index: str = "aegis_chunks_bm25"
    username: str = ""
    password: str = ""


class EmbeddingsConfig(BaseModel):
    text_model: str = "BAAI/bge-large-en-v1.5"
    visual_model: str = "vidore/colpali"
    dimension: int = 1024
    batch_size: int = 32
    device: Literal["cuda", "cpu", "mps"] = "cpu"
    normalize: bool = True


class ChunkingConfig(BaseModel):
    strategy: Literal["hierarchical", "semantic", "sliding"] = "hierarchical"
    max_tokens: int = 800
    overlap: int = 100
    min_chunk_tokens: int = 50


class RetrievalConfig(BaseModel):
    bm25_top_k: int = 50
    dense_top_k: int = 50
    visual_top_k: int = 20
    rerank_top_k: int = 12
    final_k: int = 8
    reranker: str = "BAAI/bge-reranker-v2-m3"
    mmr_lambda: float = 0.7


class LLMConfig(BaseModel):
    provider: Literal["vllm", "openai", "anthropic", "google"] = "openai"
    model: str = "gpt-4o-mini"
    endpoint: str | None = None
    api_key: str | None = None
    max_input_tokens: int = 128_000
    max_output_tokens: int = 4096
    temperature: float = 0.1
    top_p: float = 0.95
    stream: bool = True


class CacheConfig(BaseModel):
    semantic_threshold: float = 0.95
    ttl_seconds: int = 3600
    max_size_gb: int = 8


class ObservabilityConfig(BaseModel):
    otlp_endpoint: str = "http://localhost:4317"
    metrics_port: int = 9090
    enable_tracing: bool = True
    enable_metrics: bool = True


# ─────────────────────────────────────────────────────────────────
# Root Settings
# ─────────────────────────────────────────────────────────────────

class Settings(BaseModel):
    """Root settings object — loaded from YAML + environment overrides."""
    app: AppConfig = AppConfig()
    api: ApiConfig = ApiConfig()
    storage: StorageConfig
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    kafka: KafkaConfig = KafkaConfig()
    milvus: MilvusConfig = MilvusConfig()
    elasticsearch: ElasticsearchConfig = ElasticsearchConfig()
    embeddings: EmbeddingsConfig = EmbeddingsConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    llm: LLMConfig = LLMConfig()
    cache: CacheConfig = CacheConfig()
    observability: ObservabilityConfig = ObservabilityConfig()


# ─────────────────────────────────────────────────────────────────
# Environment Variable Interpolation
# ─────────────────────────────────────────────────────────────────

_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


def _interpolate(value: object) -> object:
    """Recursively resolve ${VAR_NAME:default} syntax in YAML values."""
    if isinstance(value, str):
        def replacer(m: re.Match) -> str:
            var_name, default = m.group(1), m.group(2) or ""
            return os.environ.get(var_name, default)
        return _ENV_PATTERN.sub(replacer, value)
    elif isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


# ─────────────────────────────────────────────────────────────────
# Loader
# ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_settings(config_path: str = "config/settings.yaml") -> Settings:
    """Load and parse settings from YAML file with env variable substitution."""
    path = Path(config_path)
    if not path.exists():
        # Fallback: try relative to this file's location
        path = Path(__file__).parent.parent / config_path
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw = _interpolate(raw)

    return Settings(**raw)


# Global settings instance
try:
    settings = load_settings()
except Exception as e:
    # Allow import even without config file (for testing)
    import warnings
    warnings.warn(f"Could not load settings: {e}. Using defaults.")
    settings = Settings(
        storage=StorageConfig(
            s3=S3Config(
                endpoint="http://localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
            )
        )
    )
