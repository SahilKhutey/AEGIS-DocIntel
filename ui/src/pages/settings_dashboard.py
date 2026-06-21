"""
Settings Dashboard
====================

System configuration: API keys, budgets, models, paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from backend.src.connectors import AGENT_SPECS
except ImportError:
    try:
        from src.connectors import AGENT_SPECS
    except ImportError:
        from connectors import AGENT_SPECS


@dataclass
class AgentSettings:
    """Settings for a single agent."""

    agent_name: str
    api_key_configured: bool = False
    api_key_masked: str = ""  # last 4 chars only
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "api_key_configured": self.api_key_configured,
            "api_key_masked": self.api_key_masked,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enabled": self.enabled,
        }


@dataclass
class SystemSettings:
    """System-wide settings."""

    storage_backend: str = "in_memory"
    cache_capacity: int = 1000
    cache_policy: str = "lru"
    promotion_policy: str = "hybrid"

    def to_dict(self) -> dict:
        return {
            "storage_backend": self.storage_backend,
            "cache_capacity": self.cache_capacity,
            "cache_policy": self.cache_policy,
            "promotion_policy": self.promotion_policy,
        }


@dataclass
class SettingsData:
    """Data for settings dashboard."""

    system: SystemSettings = field(default_factory=SystemSettings)
    agents: List[AgentSettings] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "system": self.system.to_dict(),
            "agents": [a.to_dict() for a in self.agents],
        }


class SettingsDashboard:
    """Settings dashboard backend API."""

    def __init__(self) -> None:
        self.system = SystemSettings()
        self.agents = {}
        for name, spec in AGENT_SPECS.items():
            if name.endswith("-default"):
                continue
            self.agents[name] = AgentSettings(
                agent_name=name,
                model=name,
                max_tokens=spec.get("max_output_tokens", 1024),
            )

    def get_settings(self) -> SettingsData:
        return SettingsData(
            system=self.system,
            agents=list(self.agents.values()),
        )

    def get_page_data(self) -> SettingsData:
        return self.get_settings()

    def update_system_settings(
        self,
        storage_backend: Optional[str] = None,
        cache_capacity: Optional[int] = None,
        cache_policy: Optional[str] = None,
        promotion_policy: Optional[str] = None,
    ) -> SystemSettings:
        if storage_backend is not None:
            self.system.storage_backend = storage_backend
        if cache_capacity is not None:
            self.system.cache_capacity = cache_capacity
        if cache_policy is not None:
            self.system.cache_policy = cache_policy
        if promotion_policy is not None:
            self.system.promotion_policy = promotion_policy
        return self.system

    def update_agent_settings(
        self,
        agent_name: str,
        enabled: Optional[bool] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> AgentSettings:
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentSettings(agent_name=agent_name)
        agent = self.agents[agent_name]
        if enabled is not None:
            agent.enabled = enabled
        if temperature is not None:
            agent.temperature = temperature
        if max_tokens is not None:
            agent.max_tokens = max_tokens
        if api_key is not None:
            agent.api_key_configured = True
            agent.api_key_masked = f"*{api_key[-4:]}" if len(api_key) >= 4 else "****"
        return agent
