"""
Connector Factory
=================

Factory for instantiating AI agent connectors.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from .connector_base import BaseConnector, ConnectorConfig
from .chatgpt_connector import ChatGPTConnector
from .gemini_connector import GeminiConnector
from .claude_connector import ClaudeConnector
from .deepseek_connector import DeepSeekConnector
from .qwen_connector import QwenConnector
from .local_connector import LocalConnector


class ConnectorFactory:
    """Factory for creating connectors."""

    REGISTRY: Dict[str, Type[BaseConnector]] = {
        "chatgpt": ChatGPTConnector,
        "gemini": GeminiConnector,
        "claude": ClaudeConnector,
        "deepseek": DeepSeekConnector,
        "qwen": QwenConnector,
        "local": LocalConnector,
    }

    @classmethod
    def create(cls, agent_type: str, config: ConnectorConfig) -> BaseConnector:
        """Create a connector instance."""
        agent_lower = agent_type.lower()
        connector_class = cls.REGISTRY.get(agent_lower)
        if not connector_class:
            connector_class = LocalConnector
        return connector_class(config)


def get_connector(
    agent_type: str,
    config: Optional[ConnectorConfig] = None,
    **kwargs: Any,
) -> BaseConnector:
    """Convenience function to get a connector."""
    if config is None:
        config = ConnectorConfig(
            api_key=kwargs.get("api_key"),
            model=kwargs.get("model", "default"),
            endpoint=kwargs.get("endpoint"),
            timeout=kwargs.get("timeout", 60.0),
            max_retries=kwargs.get("max_retries", 3),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1024),
            top_p=kwargs.get("top_p", 1.0),
            extra=kwargs.get("extra", {}),
        )
    return ConnectorFactory.create(agent_type, config)
