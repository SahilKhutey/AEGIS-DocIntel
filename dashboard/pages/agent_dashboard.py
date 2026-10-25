"""
Agent Dashboard
================

Control panel for AI agent connectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from backend.src.connectors import (
        AGENT_SPECS,
        BaseConnector,
        ConnectorFactory,
        ConnectorResponse,
    )
except ImportError:
    try:
        from src.connectors import (
            AGENT_SPECS,
            BaseConnector,
            ConnectorFactory,
            ConnectorResponse,
        )
    except ImportError:
        from connectors import (
            AGENT_SPECS,
            BaseConnector,
            ConnectorFactory,
            ConnectorResponse,
        )


@dataclass
class AgentInfo:
    """Info about an AI agent."""

    name: str
    provider: str
    max_context_tokens: int
    max_output_tokens: int
    available: bool
    configured: bool
    total_requests: int = 0
    total_tokens: int = 0
    error_count: int = 0
    average_latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "max_context_tokens": self.max_context_tokens,
            "max_output_tokens": self.max_output_tokens,
            "available": self.available,
            "configured": self.configured,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count,
            "average_latency_ms": round(self.average_latency_ms, 2),
        }


@dataclass
class AgentViewData:
    """Agent dashboard data."""

    agents: List[AgentInfo] = field(default_factory=list)
    default_agent: str = "chatgpt"
    total_requests: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "agents": [a.to_dict() for a in self.agents],
            "default_agent": self.default_agent,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
        }


class AgentDashboard:
    """Agent dashboard backend API."""

    PROVIDER_MAP = {
        "chatgpt": "OpenAI",
        "gemini": "Google",
        "claude": "Anthropic",
        "deepseek": "DeepSeek",
        "qwen": "Alibaba",
        "local": "Local",
    }

    def __init__(self, default_agent: str = "chatgpt") -> None:
        self.default_agent = default_agent
        self.request_counts: Dict[str, int] = {}
        self.token_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.latency_sums: Dict[str, float] = {}

    def list_agents(self) -> List[AgentInfo]:
        """List all known agents."""
        agents: List[AgentInfo] = []
        for name, spec in AGENT_SPECS.items():
            if name.endswith("-default"):
                continue
            provider = self.PROVIDER_MAP.get(name, name)
            agents.append(
                AgentInfo(
                    name=name,
                    provider=provider,
                    max_context_tokens=spec["max_context_tokens"],
                    max_output_tokens=spec["max_output_tokens"],
                    available=True,
                    configured=False,
                    total_requests=self.request_counts.get(name, 0),
                    total_tokens=self.token_counts.get(name, 0),
                    error_count=self.error_counts.get(name, 0),
                    average_latency_ms=(
                        self.latency_sums[name] / max(self.request_counts[name], 1)
                        if name in self.latency_sums and self.request_counts.get(name, 0) > 0
                        else 0.0
                    ),
                )
            )
        return agents

    def record_request(
        self,
        agent_name: str,
        response: ConnectorResponse,
    ) -> None:
        self.request_counts[agent_name] = self.request_counts.get(agent_name, 0) + 1
        self.token_counts[agent_name] = self.token_counts.get(agent_name, 0) + response.usage.get("total_tokens", 0)
        if not response.success:
            self.error_counts[agent_name] = self.error_counts.get(agent_name, 0) + 1
        self.latency_sums[agent_name] = self.latency_sums.get(agent_name, 0.0) + response.latency_ms

    def get_view(self) -> AgentViewData:
        agents = self.list_agents()
        return AgentViewData(
            agents=agents,
            default_agent=self.default_agent,
            total_requests=sum(self.request_counts.values()),
            total_tokens=sum(self.token_counts.values()),
        )

    def send_test_query(
        self,
        agent_name: str,
        prompt: str,
        api_key: Optional[str] = None,
    ) -> ConnectorResponse:
        """Send a test query to an agent."""
        try:
            from backend.src.connectors import ConnectorConfig
        except ImportError:
            try:
                from src.connectors import ConnectorConfig
            except ImportError:
                from connectors import ConnectorConfig
        config = ConnectorConfig(
            api_key=api_key,
            model=agent_name,
            max_tokens=128,
            timeout=30.0,
        )
        connector = ConnectorFactory.create(agent_name, config=config)
        response = connector.query(prompt)
        self.record_request(agent_name, response)
        return response
