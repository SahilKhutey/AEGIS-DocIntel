'''AMDI-OS Configuration.'''

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    name: str = 'amdi-os'
    version: str = '1.0.0'
    env: str = 'development'
    log_level: str = 'INFO'


class LLMConfig(BaseModel):
    provider: str = 'openai'
    model: str = 'gpt-4o-mini'
    api_key: str = ''
    base_url: str | None = None
    temperature: float = 0.1
    max_tokens: int = 4096


class StorageConfig(BaseModel):
    redis_url: str = 'redis://localhost:6379/0'
    enable_redis: bool = True


class EmbeddingConfig(BaseModel):
    model: str = 'BAAI/bge-large-en-v1.5'
    dimension: int = 1024
    device: str = 'cpu'


class AMDIConfig(BaseModel):
    max_context_tokens: int = 6000
    enable_mios_engines: bool = True
    enable_fusion: bool = True
    fusion_default_query: str = 'semantic'


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    llm: LLMConfig = LLMConfig()
    storage: StorageConfig = StorageConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    amdi: AMDIConfig = AMDIConfig()

    model_config = SettingsConfigDict(env_file='.env', env_nested_delimiter='__', extra='ignore')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    '''Get cached Settings instance, supporting environment variable overrides.'''
    s = Settings()
    if os.environ.get('LLM_API_KEY'):
        s.llm.api_key = os.environ['LLM_API_KEY']
    if os.environ.get('LLM_PROVIDER'):
        s.llm.provider = os.environ['LLM_PROVIDER']
    if os.environ.get('LLM_MODEL'):
        s.llm.model = os.environ['LLM_MODEL']
    return s
