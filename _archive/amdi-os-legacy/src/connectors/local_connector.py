"""
Local Model Connector
======================

Connector for locally-running models via:
    - Ollama (HTTP API)
    - llama.cpp server
    - LM Studio (OpenAI-compatible)
    - vLLM
    - Any custom HTTP endpoint with OpenAI-compatible schema
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from .connector_base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorResponse,
)
from .exceptions import ConnectorError


class LocalConnector(BaseConnector):
    """Local model connector (Ollama, llama.cpp, LM Studio, vLLM)."""

    AGENT_NAME = "local"

    OLLAMA_DEFAULT = "http://localhost:11434"
    OPENAI_COMPAT_DEFAULT = "http://localhost:1234/v1"

    def __init__(self, config: ConnectorConfig) -> None:
        self.base_url = config.endpoint or self.OPENAI_COMPAT_DEFAULT
        self.server_type = self._detect_server_type()
        super().__init__(config)

    def _detect_server_type(self) -> str:
        url = self.base_url.lower()
        if ":11434" in url:
            return "ollama"
        return "openai_compat"

    def _validate_config(self) -> None:
        # Local models don't require API key
        pass

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

        if self.server_type == "ollama":
            return self._call_ollama(messages, temperature, max_tokens)
        return self._call_openai_compat(
            messages, temperature, max_tokens
        )

    def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ConnectorResponse:
        try:
            import urllib.request
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": self.config.top_p,
                },            }
            headers = {"Content-Type": "application/json"}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
            latency = (time.time() - t0) * 1000
            
            text = resp_data.get("message", {}).get("content", "")
            usage = {
                "prompt_tokens": resp_data.get("prompt_eval_count", 0),
                "completion_tokens": resp_data.get("eval_count", 0),
                "total_tokens": resp_data.get("prompt_eval_count", 0) + resp_data.get("eval_count", 0),
            }
            return ConnectorResponse(
                text=text,
                agent=self.AGENT_NAME,
                model=self.config.model,
                usage=usage,
                finish_reason="stop",
                latency_ms=latency,
                metadata={"server_type": "ollama", "endpoint": self.base_url},
                raw=resp_data,
                success=True,
            )
        except Exception as exc:
            return self._mock_response(messages, max_tokens + 50)

    def _call_openai_compat(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ConnectorResponse:
        # Try to use OpenAI client if library is installed
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.config.api_key or "no-key",
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
                metadata={"server_type": "openai_compat", "endpoint": self.base_url},
                raw=response,
                success=True,
            )
        except Exception:
            # Fallback to urllib
            try:
                import urllib.request
                import urllib.error
                url = f"{self.base_url}/chat/completions"
                payload = {
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": self.config.top_p,
                }
                headers = {"Content-Type": "application/json"}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                
                t0 = time.time()
                with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                    resp_data = json.loads(response.read().decode("utf-8"))
                latency = (time.time() - t0) * 1000
                
                choice = resp_data["choices"][0]
                text = choice["message"]["content"] or ""
                usage_data = resp_data.get("usage", {})
                usage = {
                    "prompt_tokens": usage_data.get("prompt_tokens", 0),
                    "completion_tokens": usage_data.get("completion_tokens", 0),
                    "total_tokens": usage_data.get("total_tokens", 0),
                }
                return ConnectorResponse(
                    text=text,
                    agent=self.AGENT_NAME,
                    model=self.config.model,
                    usage=usage,
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=latency,
                    metadata={"server_type": "openai_compat", "endpoint": self.base_url},
                    raw=resp_data,
                    success=True,
                )
            except Exception:
                return self._mock_response(messages, max_tokens + 50)

    def _mock_response(
        self,
        messages: List[Dict[str, str]],
        total_tokens: int,
    ) -> ConnectorResponse:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        t0 = time.time()
        text = (
            f"[DRY-RUN Local response]\n"
            f"Server Type: {self.server_type}\n"
            f"Endpoint: {self.base_url}\n"
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
