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

    def __init__(self, config: Optional[ConnectorConfig] = None, **kwargs: Any) -> None:
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

    def get_native_format(self) -> Dict[str, Any]:
        """Convert connector configuration to native agent format representation."""
        return {
            "type": f"{self.AGENT_NAME}_messages",
            "model": self.config.model,
            "endpoint": self.config.endpoint,
        }

    def build_system_prompt(self, ueo: Any) -> str:
        """Construct a system prompt from UEO if available."""
        if hasattr(ueo, "metadata"):
            pages = getattr(ueo.metadata, "pages", 1)
            doc_type = getattr(ueo.metadata, "document_type", "Unknown")
            n_tables = getattr(getattr(ueo, "matrix", None), "n_tables", 0)
            citations = getattr(ueo, "citations", [])
            conf_obj = getattr(ueo, "confidence", None)
            conf = getattr(conf_obj, "overall", 1.0) if conf_obj else 1.0
            query_str = getattr(ueo, "query", "")
            return (
                f"You are a precise document intelligence assistant. The user has asked:\n\n"
                f"QUERY: {query_str}\n\n"
                f"You have been provided a structured Context Object (UEO) extracted by AEGIS-AMDI-OS containing:\n"
                f"- Document summary ({pages} pages, {doc_type})\n"
                f"- {n_tables} pre-processed tables with computed metrics\n"
                f"- {len(citations)} citations with confidence scores\n"
                f"- Overall confidence: {conf:.3f}\n\n"
                f"RULES:\n"
                f"1. Answer ONLY using the provided context.\n"
                f"2. For numerical questions, use the table's pre-computed metrics.\n"
                f"3. Reference sources using [page, section] notation.\n"
                f"4. If unsure, say \"I don't know\" rather than fabricate.\n"
                f"5. Match the user's language."
            )
        return "You are a precise document intelligence assistant."

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
        if hasattr(ueo, "system"):
            system_prompt = ueo.system
        else:
            system_prompt = self.build_system_prompt(ueo)

        user_parts: List[str] = []
        if getattr(ueo, "summary", None):
            user_parts.append(f"Summary:\n{ueo.summary}")
        elif getattr(ueo, "document_summary", None):
            doc_summary = ueo.document_summary
            abstract = getattr(doc_summary, "abstract", "")
            title = getattr(doc_summary, "title", "")
            if title or abstract:
                user_parts.append(f"Summary: {title}\n{abstract}")

        if getattr(ueo, "context", None):
            user_parts.append(f"Context:\n{ueo.context}")
        else:
            try:
                from src.ael.formats.markdown_exporter import MarkdownExporter
                md_context = MarkdownExporter.export(ueo)
                if md_context:
                    user_parts.append(f"Context:\n{md_context}")
            except Exception as exp_err:
                logger.warning(f"Markdown fallback export failed: {exp_err}")

        if getattr(ueo, "citations", None):
            cit_items = []
            for c in ueo.citations[:20]:
                if isinstance(c, dict):
                    cit_items.append(f"- {c.get('excerpt', c.get('snippet', str(c)))}")
                elif hasattr(c, "snippet"):
                    cit_items.append(f"- [p.{getattr(c, 'page', '?')}] {c.snippet}")
                else:
                    cit_items.append(f"- {c}")
            if cit_items:
                user_parts.append("Citations:\n" + "\n".join(cit_items))

        if getattr(ueo, "metadata", None):
            if isinstance(ueo.metadata, dict):
                meta_str = "\n".join(f"- {k}: {v}" for k, v in ueo.metadata.items())
                user_parts.append(f"Metadata:\n{meta_str}")
            elif hasattr(ueo.metadata, "__dict__"):
                meta_str = "\n".join(f"- {k}: {v}" for k, v in ueo.metadata.__dict__.items() if not k.startswith("_"))
                user_parts.append(f"Metadata:\n{meta_str}")

        if question is None:
            question = getattr(ueo, "query", None) or "Please analyze the provided context and provide a thorough response with citations."
        user_parts.append(f"\nQuestion: {question}")
        user_prompt = "\n\n".join(user_parts)
        return self.query(user_prompt, system_prompt=system_prompt, **kwargs)

    async def send(self, ueo: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Async send method for UEO integration (used by AEL and workflows).
        """
        question = getattr(ueo, "query", None) or kwargs.get("question")
        try:
            resp = self.send_ueo(ueo, question=question, **kwargs)
            res_dict: Dict[str, Any] = {
                "agent": resp.agent,
                "model": resp.model,
                "answer": resp.text,
                "input_tokens": resp.usage.get("prompt_tokens", 0) if resp.usage else 0,
                "output_tokens": resp.usage.get("completion_tokens", 0) if resp.usage else 0,
                "finish_reason": resp.finish_reason,
            }
            if not resp.success and resp.error:
                res_dict["error"] = resp.error
            return res_dict
        except Exception as exc:
            return {
                "agent": getattr(self, "AGENT_NAME", "unknown"),
                "model": getattr(self.config, "model", ""),
                "error": str(exc),
            }

    async def stream(self, ueo: Any, **kwargs: Any):
        """Stream response chunks (yields full answer in default implementation)."""
        res = await self.send(ueo, **kwargs)
        yield res.get("answer", "")

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