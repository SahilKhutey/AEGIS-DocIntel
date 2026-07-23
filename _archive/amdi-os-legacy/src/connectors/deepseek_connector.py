"""
DeepSeek Connector
===================

Connector for DeepSeek models (chat + reasoner).

Supports:
    - deepseek-chat
    - deepseek-reasoner
    - OpenAI-compatible API
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from .connector_base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorResponse,
)
from .exceptions import ConnectorError


class DeepSeekConnector(BaseConnector):
    """DeepSeek connector (OpenAI-compatible)."""

    AGENT_NAME = "deepseek"
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, config: ConnectorConfig) -> None:
        self.base_url = config.endpoint or self.DEFAULT_BASE_URL
        super().__init__(config)

    def _validate_config(self) -> None:
        try:
            import openai
            self._openai = openai
        except ImportError:
            self._openai = None

    def _call(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> ConnectorResponse:
        total_tokens = sum(self.count_tokens(m["content"]) for m in messages)
        total_tokens += self.config.max_tokens
        self._check_token_budget(total_tokens)

        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        if self._openai is not None and self.config.api_key:
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
                    "prompt_tokens": getattr(
                        response.usage, "prompt_tokens", 0
                    ),
                    "completion_tokens": getattr(
                        response.usage, "completion_tokens", 0
                    ),
                    "total_tokens": getattr(
                        response.usage, "total_tokens", 0
                    ),
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
            except Exception as exc:
                raise ConnectorError(f"DeepSeek call failed: {exc}") from exc
        return self._mock_response(messages, total_tokens)

    def _mock_response(
        self,
        messages: List[Dict[str, str]],
        total_tokens: int,
    ) -> ConnectorResponse:
        t0 = time.time()
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        text = (
            f"[DRY-RUN DeepSeek response]\n"
            f"Model: {self.config.model}\n"
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
            finish_reason="stop",
            latency_ms=latency,
            metadata={"dry_run": True},
            success=True,
        )

    def count_tokens(self, text: str) -> int:
        return max(1, int(len(text.split()) / 0.75))