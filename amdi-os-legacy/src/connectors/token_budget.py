"""
Agent Token Budgets
===================

Per-agent token limits and budget helpers.

Agent specs (max context tokens):
    ChatGPT-4o         128,000
    ChatGPT-4 Turbo    128,000
    ChatGPT-3.5         16,385
    Gemini 1.5 Pro   1,000,000
    Gemini 1.5 Flash 1,000,000
    Claude 3.5 Sonnet  200,000
    Claude 3 Opus      200,000
    DeepSeek-V3         64,000
    Qwen-2.5            32,768
    Local default        8,192
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .connector_base import ConnectorConfig


AGENT_SPECS: Dict[str, Dict[str, int]] = {
    "chatgpt": {
        "max_context_tokens": 128_000,
        "max_output_tokens": 16_384,
        "safety_margin": 1_000,
    },
    "chatgpt-4o": {
        "max_context_tokens": 128_000,
        "max_output_tokens": 16_384,
        "safety_margin": 1_000,
    },
    "chatgpt-4-turbo": {
        "max_context_tokens": 128_000,
        "max_output_tokens": 4_096,
        "safety_margin": 1_000,
    },
    "chatgpt-3.5-turbo": {
        "max_context_tokens": 16_385,
        "max_output_tokens": 4_096,
        "safety_margin": 500,
    },
    "gemini": {
        "max_context_tokens": 1_000_000,
        "max_output_tokens": 8_192,
        "safety_margin": 2_000,
    },
    "gemini-1.5-pro": {
        "max_context_tokens": 1_000_000,
        "max_output_tokens": 8_192,
        "safety_margin": 2_000,
    },
    "gemini-1.5-flash": {
        "max_context_tokens": 1_000_000,
        "max_output_tokens": 8_192,
        "safety_margin": 2_000,
    },
    "claude": {
        "max_context_tokens": 200_000,
        "max_output_tokens": 8_192,
        "safety_margin": 1_500,
    },
    "claude-3.5-sonnet": {
        "max_context_tokens": 200_000,
        "max_output_tokens": 8_192,
        "safety_margin": 1_500,
    },
    "claude-3-opus": {
        "max_context_tokens": 200_000,
        "max_output_tokens": 4_096,
        "safety_margin": 1_500,
    },
    "deepseek": {
        "max_context_tokens": 64_000,
        "max_output_tokens": 4_096,
        "safety_margin": 1_000,
    },
    "deepseek-chat": {
        "max_context_tokens": 64_000,
        "max_output_tokens": 4_096,
        "safety_margin": 1_000,
    },
    "qwen": {
        "max_context_tokens": 32_768,
        "max_output_tokens": 4_096,
        "safety_margin": 800,
    },
    "qwen-2.5": {
        "max_context_tokens": 32_768,
        "max_output_tokens": 4_096,
        "safety_margin": 800,
    },
    "local": {
        "max_context_tokens": 8_192,
        "max_output_tokens": 2_048,
        "safety_margin": 500,
    },
    "local-default": {
        "max_context_tokens": 8_192,
        "max_output_tokens": 2_048,
        "safety_margin": 500,
    },
}


@dataclass
class AgentTokenBudget:
    """Token budget for a specific agent."""

    agent_name: str
    max_context_tokens: int
    max_output_tokens: int
    safety_margin: int

    def effective_limit(self) -> int:
        return self.max_context_tokens - self.safety_margin - self.max_output_tokens

    def max_input(self) -> int:
        return self.effective_limit()

    @classmethod
    def from_config(cls, config: ConnectorConfig) -> "AgentTokenBudget":
        """Resolve budget from ConnectorConfig + model name."""
        spec = AGENT_SPECS.get(config.model, AGENT_SPECS.get("local"))
        return cls(
            agent_name=config.model,
            max_context_tokens=spec["max_context_tokens"],
            max_output_tokens=spec["max_output_tokens"],
            safety_margin=spec["safety_margin"],
        )

    @classmethod
    def for_agent(cls, agent: str) -> "AgentTokenBudget":
        spec = AGENT_SPECS.get(agent, AGENT_SPECS["local"])
        return cls(
            agent_name=agent,
            max_context_tokens=spec["max_context_tokens"],
            max_output_tokens=spec["max_output_tokens"],
            safety_margin=spec["safety_margin"],
        )