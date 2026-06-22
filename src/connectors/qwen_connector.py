"""
Qwen Connector (Alibaba DashScope)
====================================

Connector for Alibaba's Qwen models via the DashScope API.
Supports OpenAI-compatible mode.
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


class QwenConnector(BaseConnector):
    """Alibaba Qwen connector."""

    AGENT_NAME = "qwen"
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self, config: ConnectorConfig) -> None:
        self.base_url = config.endpoint or self.DEFAULT_BASE_URL
        super().__init__(config)

    def _validate_config(self) -> None:
        try:
            import openai
            self._openai = openai
        except ImportError:
            self._openai = None
        try:
            import dashscope
            self._dashscope = dashscope
        except ImportError:
            self._dashscope = None

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
                return self._call_openai_compat(
                    messages, temperature, max_tokens
                )
            except Exception as exc:
                raise ConnectorError(f"Qwen call failed: {exc}") from exc
        return self._mock_response(messages, total_tokens)

    def _call_openai_compat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ConnectorResponse:
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
            "completion_tokens": getattr(
                response.usage, "completion_tokens", 0
            ),
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
            f"[DRY-RUN Qwen response]\n"
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