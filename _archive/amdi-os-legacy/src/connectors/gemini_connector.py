"""
Gemini Connector (Google)
==========================

Connector for Google's Gemini models via the Google Generative AI API.

Supports:
    - gemini-1.5-pro (1M tokens)
    - gemini-1.5-flash (1M tokens)
    - Multimodal inputs (text + images + tables)
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


class GeminiConnector(BaseConnector):
    """Google Gemini connector."""

    AGENT_NAME = "gemini"
    DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: ConnectorConfig) -> None:
        self.endpoint = config.endpoint or self.DEFAULT_ENDPOINT
        self._client: Any = None
        super().__init__(config)

    def _validate_config(self) -> None:
        try:
            import google.generativeai as genai
            self._genai = genai
            if self.config.api_key:
                genai.configure(api_key=self.config.api_key)
                self._client = genai.GenerativeModel(self.config.model)
        except ImportError:
            self._genai = None
            self._client = None

    def _call(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> ConnectorResponse:
        # Convert messages to Gemini format
        # Gemini expects: system_instruction + history + final user message
        system_prompt = ""
        user_parts: List[str] = []
        for m in messages:
            if m["role"] == "system":
                system_prompt += m["content"] + "\n"
            elif m["role"] == "user":
                user_parts.append(m["content"])
        prompt = "\n".join(user_parts)
        total_tokens = self.count_tokens(prompt) + self.count_tokens(system_prompt)
        total_tokens += self.config.max_tokens
        self._check_token_budget(total_tokens)

        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        if self._client is not None and self.config.api_key:
            try:
                return self._call_real(
                    system_prompt, prompt, temperature, max_tokens
                )
            except Exception as exc:
                raise ConnectorError(f"Gemini call failed: {exc}") from exc
        return self._mock_response(prompt, total_tokens)

    def _call_real(
        self,
        system_prompt: str,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> ConnectorResponse:
        model = self._genai.GenerativeModel(
            model_name=self.config.model,
            system_instruction=system_prompt or None,
        )
        generation_config = self._genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=self.config.top_p,
        )
        t0 = time.time()
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        latency = (time.time() - t0) * 1000
        text = response.text if hasattr(response, "text") else ""
        usage_meta = getattr(response, "usage_metadata", None)
        usage = {}
        if usage_meta:
            usage = {
                "prompt_tokens": getattr(usage_meta, "prompt_token_count", 0),
                "completion_tokens": getattr(usage_meta, "candidates_token_count", 0),
                "total_tokens": getattr(usage_meta, "total_token_count", 0),
            }
        finish = "stop"
        if hasattr(response, "candidates") and response.candidates:
            finish = str(response.candidates[0].finish_reason)
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
        self, prompt: str, total_tokens: int
    ) -> ConnectorResponse:
        t0 = time.time()
        text = (
            f"[DRY-RUN Gemini response]\n"
            f"Model: {self.config.model}\n"
            f"Multimodal support: text + tables + images\n"
            f"Echo (first 200 chars):\n{prompt[:200]}"
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
        """Approximate Gemini token count."""
        try:
            if self._genai is not None and self.config.api_key:
                model = self._genai.GenerativeModel(self.config.model)
                return int(model.count_tokens(text).total_tokens)
        except Exception:
            pass
        return max(1, int(len(text) / 4))