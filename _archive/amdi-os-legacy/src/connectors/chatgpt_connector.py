"""
ChatGPT Connector (OpenAI)
===========================

Connector for OpenAI's ChatGPT models via the OpenAI API or compatible endpoint.

Supports:
    - gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    - Any OpenAI-compatible API (Azure, local server)
    - Both real API calls and dry-run mode for testing
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .connector_base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorResponse,
    ConnectionStatus,
)
from .exceptions import (
    AuthenticationError,
    ConnectorError,
    InvalidResponseError,
    RateLimitError,
    TokenLimitError,
)


class ChatGPTConnector(BaseConnector):
    """
    ChatGPT connector (OpenAI-compatible).
    """

    AGENT_NAME = "chatgpt"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, config: ConnectorConfig) -> None:
        self.base_url = config.endpoint or self.DEFAULT_BASE_URL
        self._session: Any = None
        self._openai: Any = None
        self._openai_client: Any = None
        super().__init__(config)

    def _validate_config(self) -> None:
        if not self.config.api_key and not self.config.endpoint:
            # Allow dry-run without API key
            self.status = ConnectionStatus.DISCONNECTED
            return
        try:
            # Try to use the openai library if available
            import openai
            self._openai = openai
            self._openai_client = None
        except ImportError:
            self._openai = None
            self._openai_client = None

    def _call(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> ConnectorResponse:
        # token check
        total_tokens = sum(self.count_tokens(m["content"]) for m in messages)
        total_tokens += self.config.max_tokens
        self._check_token_budget(total_tokens)

        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        # Try real OpenAI client
        if self._openai is not None and self.config.api_key:
            try:
                return self._call_openai(messages, temperature, max_tokens)
            except Exception as exc:
                raise ConnectorError(f"OpenAI call failed: {exc}") from exc
        # Dry-run / mock mode
        return self._mock_response(messages, total_tokens)

    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ConnectorResponse:
        try:
            client = self._openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.base_url,
                timeout=self.config.timeout,
            )
            t0 = time.time()
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=self.config.top_p,
            )
            latency = (time.time() - t0) * 1000
            choice = response.choices[0]
            text = choice.message.content or ""
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }
            return ConnectorResponse(
                text=text,
                agent=self.AGENT_NAME,
                model=self.config.model,
                usage=usage,
                finish_reason=choice.finish_reason or "stop",
                latency_ms=latency,
                metadata={"endpoint": self.base_url},
                raw=response,
                success=True,
            )
        except self._openai.AuthenticationError as exc:
            raise AuthenticationError(f"Authentication failed: {exc}") from exc
        except self._openai.RateLimitError as exc:
            raise RateLimitError(f"Rate limit hit: {exc}") from exc
        except self._openai.APIError as exc:
            raise ConnectorError(f"OpenAI API error: {exc}") from exc

    def _mock_response(
        self,
        messages: List[Dict[str, str]],
        total_tokens: int,
    ) -> ConnectorResponse:
        """Dry-run response for testing without API key."""
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        t0 = time.time()
        text = (
            f"[DRY-RUN ChatGPT response]\n"
            f"Model: {self.config.model}\n"
            f"User input length: {len(last_user)} chars\n"
            f"Echo (first 200 chars):\n{last_user[:200]}"
        )
        # simulate small latency
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
            finish_reason="stop",
            latency_ms=latency,
            metadata={"dry_run": True},
            success=True,
        )

    def count_tokens(self, text: str) -> int:
        """Approximate token count (words × 4/3)."""
        return max(1, int(len(text.split()) / 0.75))