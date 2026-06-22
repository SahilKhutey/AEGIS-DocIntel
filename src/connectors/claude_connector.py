"""
Claude Connector (Anthropic)
=============================

Connector for Anthropic's Claude models.

Supports:
    - claude-3.5-sonnet (200K tokens)
    - claude-3-opus (200K tokens)
    - claude-3-haiku
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .connector_base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorResponse,
)
from .exceptions import (
    AuthenticationError,
    ConnectorError,
    RateLimitError,
)


class ClaudeConnector(BaseConnector):
    """Anthropic Claude connector."""

    AGENT_NAME = "claude"
    DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"

    def __init__(self, config: ConnectorConfig) -> None:
        self.endpoint = config.endpoint or self.DEFAULT_ENDPOINT
        super().__init__(config)

    def _validate_config(self) -> None:
        try:
            import anthropic
            self._anthropic = anthropic
            self._client = None
        except ImportError:
            self._anthropic = None
            self._client = None

    def _call(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> ConnectorResponse:
        # Claude expects: separate system param + user/assistant messages
        system_prompt = ""
        user_messages: List[Dict[str, str]] = []
        for m in messages:
            if m["role"] == "system":
                system_prompt += m["content"] + "\n"
            else:
                user_messages.append({"role": m["role"], "content": m["content"]})
        if not user_messages:
            raise ConnectorError("No user messages provided.")
        total_tokens = sum(self.count_tokens(m["content"]) for m in messages)
        total_tokens += self.config.max_tokens
        self._check_token_budget(total_tokens)

        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        if self._anthropic is not None and self.config.api_key:
            try:
                return self._call_real(
                    system_prompt,
                    user_messages,
                    temperature,
                    max_tokens,
                )
            except Exception as exc:
                raise ConnectorError(f"Claude call failed: {exc}") from exc
        return self._mock_response(
            system_prompt, user_messages, total_tokens
        )

    def _call_real(
        self,
        system_prompt: str,
        user_messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ConnectorResponse:
        client = self._anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
        )
        t0 = time.time()
        response = client.messages.create(
            model=self.config.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are a helpful assistant.",
            messages=user_messages,
            temperature=temperature,
            top_p=self.config.top_p,
        )
        latency = (time.time() - t0) * 1000
        text_parts = [
            block.text
            for block in response.content
            if hasattr(block, "text")
        ]
        text = "\n".join(text_parts)
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": (
                response.usage.input_tokens + response.usage.output_tokens
            ),
        }
        finish = str(response.stop_reason) if response.stop_reason else "stop"
        return ConnectorResponse(
            text=text,
            agent=self.AGENT_NAME,
            model=self.config.model,
            usage=usage,
            finish_reason=finish,
            latency_ms=latency,
            metadata={"endpoint": self.endpoint},
            raw=response,
            success=True,
        )

    def _mock_response(
        self,
        system_prompt: str,
        user_messages: List[Dict[str, str]],
        total_tokens: int,
    ) -> ConnectorResponse:
        t0 = time.time()
        last_user = (
            user_messages[-1]["content"] if user_messages else ""
        )
        text = (
            f"[DRY-RUN Claude response]\n"
            f"Model: {self.config.model}\n"
            f"Long-context support: 200K tokens\n"
            f"Echo (first 200 chars):\n{last_user[:200]}"
        )
        time.sleep(0.01)
        latency = (time.time() - t0) * 1000
        return ConnectorResponse(
            text=text,
            agent=self.AGENT_NAME,
            model=self.config.model,
            usage={
                "prompt_tokens": total_tokens,
                "completion_tokens": 100,
                "total_tokens": total_tokens + 100,
            },
            finish_reason="end_turn",
            latency_ms=latency,
            metadata={"dry_run": True},
            success=True,
        )

    def count_tokens(self, text: str) -> int:
        """Approximate Claude token count."""
        return max(1, int(len(text) / 3.5))