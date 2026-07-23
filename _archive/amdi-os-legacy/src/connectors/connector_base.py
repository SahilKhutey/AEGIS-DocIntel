"""
Base Connector Interface
========================

Abstract base class for all AI agent connectors.

Defines the standard interface:
    - send_ueo(ueo) → ConnectorResponse
    - query(prompt) → ConnectorResponse
    - get_status()  → ConnectionStatus
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .exceptions import (
    AuthenticationError,
    ConnectorError,
    InvalidResponseError,
    RateLimitError,
    TokenLimitError,
)
from .token_budget import AgentTokenBudget


class ConnectionStatus(Enum):
    """Connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class ConnectorConfig:
    """
    Connector configuration.

    Attributes
    ----------
    api_key : Optional[str]
        API key for the agent.
    model : str
        Model name.
    endpoint : Optional[str]
        Custom API endpoint.
    timeout : float
        Request timeout in seconds.
    max_retries : int
        Maximum retry attempts.
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum output tokens.
    top_p : float
        Top-p sampling.
    extra : Dict[str, Any]
        Additional agent-specific parameters.
    """

    api_key: Optional[str] = None
    model: str = "default"
    endpoint: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorResponse:
    """
    Unified response from any AI agent connector.

    Attributes
    ----------
    text : str
        Response text.
    agent : str
        Agent identifier.
    model : str
        Model used.
    usage : Dict[str, int]
        Token usage statistics.
    finish_reason : str
        Why the model stopped generating.
    latency_ms : float
        Response latency.
    metadata : Dict[str, Any]
        Additional metadata.
    raw : Optional[Any]
        Raw response object (for debugging).
    """

    text: str
    agent: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "agent": self.agent,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "latency_ms": round(self.latency_ms, 2),
            "metadata": self.metadata,
            "success": self.success,
            "error": self.error,
        }


class BaseConnector(abc.ABC):
    """
    Abstract base class for AI agent connectors.
    """

    AGENT_NAME: str = "base"

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.budget = AgentTokenBudget.from_config(config)
        self._validate_config()

    @abc.abstractmethod
    def _validate_config(self) -> None:
        """Validate connector-specific configuration."""

    @abc.abstractmethod
    def _call(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> ConnectorResponse:
        """
        Make the actual API call.
        """

    @abc.abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens for this agent's tokenizer."""

    def get_status(self) -> ConnectionStatus:
        return self.status

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> List[Dict[str, str]]:
        """Build standard message list."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ConnectorResponse:
        """Send a simple prompt."""
        messages = self._build_messages(
            system_prompt or "You are a helpful assistant.",
            prompt,
        )
        return self._call(messages, **kwargs)

    def query_with_context(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ConnectorResponse:
        """Send a question with context (RAG-style)."""
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
        return self.query(
            user_prompt,
            system_prompt=system_prompt,
            **kwargs,
        )

    def send_ueo(
        self,
        ueo: Any,
        question: Optional[str] = None,
        **kwargs,
    ) -> ConnectorResponse:
        """
        Send a UniversalExportObject.

        Parameters
        ----------
        ueo : UniversalExportObject
        question : Optional[str]
            Optional user question; defaults to "Summarize the context."
        """
        # build system + user from UEO
        system_prompt = ueo.system
        user_parts: List[str] = []
        if ueo.summary:
            user_parts.append(f"Summary:\n{ueo.summary}")
        if ueo.context:
            user_parts.append(f"Context:\n{ueo.context}")
        if ueo.citations:
            cit_str = "\n".join(
                f"- {c.get('excerpt', c.get('raw', str(c)))}"
                if isinstance(c, dict)
                else f"- {c}"
                for c in ueo.citations[:20]
            )
            user_parts.append(f"Citations:\n{cit_str}")
        if ueo.metadata:
            meta_str = "\n".join(f"- {k}: {v}" for k, v in ueo.metadata.items())
            user_parts.append(f"Metadata:\n{meta_str}")
        if question is None:
            question = "Please analyze the provided context and provide a thorough response with citations."
        user_parts.append(f"\nQuestion: {question}")
        user_prompt = "\n\n".join(user_parts)
        return self.query(user_prompt, system_prompt=system_prompt, **kwargs)

    def _check_token_budget(self, total_tokens: int) -> None:
        """Raise if total tokens exceed budget."""
        if total_tokens > self.budget.effective_limit():
            raise TokenLimitError(
                f"Request tokens ({total_tokens}) exceed budget "
                f"({self.budget.effective_limit()})."
            )

    def _retry_with_backoff(self, func, *args, **kwargs) -> ConnectorResponse:
        """Retry with exponential backoff."""
        import time
        last_exc: Optional[Exception] = None
        for attempt in range(self.config.max_retries):
            try:
                return func(*args, **kwargs)
            except RateLimitError as exc:
                last_exc = exc
                if attempt < self.config.max_retries - 1:
                    delay = (2 ** attempt) * 0.5
                    time.sleep(delay)
            except Exception:
                raise
        if last_exc:
            raise last_exc
        raise ConnectorError("Retries exhausted.")