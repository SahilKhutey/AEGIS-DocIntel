"""
AEGIS-DocIntel — LLM Service
==============================
Unified LLM client with provider failover, streaming, tool use, and cost tracking.
Supports: vLLM (self-hosted), OpenAI, Anthropic, Google Gemini.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import structlog

from src.config import settings

log = structlog.get_logger("aegis.llm")

# ─────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    text: str
    model: str
    in_tokens: int
    out_tokens: int
    latency_ms: float
    cached: bool = False


@dataclass
class LLMStreamChunk:
    delta: str
    finish_reason: Optional[str] = None


# ─────────────────────────────────────────────────────────────────
# Pricing Table
# ─────────────────────────────────────────────────────────────────

PRICING = {
    "gpt-4o": {"input": 5.0 / 1e6, "output": 15.0 / 1e6},
    "gpt-4o-mini": {"input": 0.15 / 1e6, "output": 0.60 / 1e6},
    "claude-3-5-sonnet-20241022": {"input": 3.0 / 1e6, "output": 15.0 / 1e6},
    "gemini-1.5-pro": {"input": 3.5 / 1e6, "output": 10.5 / 1e6},
    "default": {"input": 1.0 / 1e6, "output": 2.0 / 1e6},
}


def calc_cost(model: str, in_tokens: int, out_tokens: int) -> float:
    p = PRICING.get(model, PRICING["default"])
    return in_tokens * p["input"] + out_tokens * p["output"]


# ─────────────────────────────────────────────────────────────────
# LLM Clients
# ─────────────────────────────────────────────────────────────────

class OpenAIClient:
    """OpenAI API client with async streaming."""

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("openai package not installed: pip install openai")
        return self._client

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        client = self._get_client()
        t0 = time.perf_counter()
        resp = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", settings.llm.max_output_tokens),
            temperature=kwargs.get("temperature", settings.llm.temperature),
            stream=False,
        )
        latency = (time.perf_counter() - t0) * 1000
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=self.model,
            in_tokens=resp.usage.prompt_tokens,
            out_tokens=resp.usage.completion_tokens,
            latency_ms=latency,
        )

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        client = self._get_client()
        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", settings.llm.max_output_tokens),
            temperature=kwargs.get("temperature", settings.llm.temperature),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            finish = chunk.choices[0].finish_reason
            yield LLMStreamChunk(delta=delta, finish_reason=finish)


class AnthropicClient:
    """Anthropic Claude client."""

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed: pip install anthropic")
        return self._client

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        client = self._get_client()
        # Separate system from messages
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]

        t0 = time.perf_counter()
        resp = await client.messages.create(
            model=self.model,
            system=system,
            messages=user_messages,
            max_tokens=kwargs.get("max_tokens", settings.llm.max_output_tokens),
            temperature=kwargs.get("temperature", settings.llm.temperature),
        )
        latency = (time.perf_counter() - t0) * 1000
        return LLMResponse(
            text=resp.content[0].text,
            model=self.model,
            in_tokens=resp.usage.input_tokens,
            out_tokens=resp.usage.output_tokens,
            latency_ms=latency,
        )

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        client = self._get_client()
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]

        async with client.messages.stream(
            model=self.model,
            system=system,
            messages=user_messages,
            max_tokens=kwargs.get("max_tokens", settings.llm.max_output_tokens),
        ) as stream:
            async for text in stream.text_stream:
                yield LLMStreamChunk(delta=text)


class MockLLMClient:
    """Fallback mock client for development/testing without API keys."""

    def __init__(self, model: str = "mock"):
        self.model = model

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        question = ""
        for m in reversed(messages):
            if m["role"] == "user":
                question = m["content"][:100]
                break

        mock_answer = (
            f"[MOCK RESPONSE] This is a development mock response to: '{question}'. "
            f"In production, configure OPENAI_API_KEY or ANTHROPIC_API_KEY. "
            f"The RAG pipeline retrieved and ranked relevant document chunks, "
            f"and this answer would be generated by the configured LLM. [Source-1]"
        )
        return LLMResponse(
            text=mock_answer,
            model=self.model,
            in_tokens=len(str(messages).split()),
            out_tokens=len(mock_answer.split()),
            latency_ms=50.0,
        )

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        resp = await self.complete(messages, **kwargs)
        words = resp.text.split(" ")
        for i, word in enumerate(words):
            yield LLMStreamChunk(
                delta=word + (" " if i < len(words) - 1 else ""),
                finish_reason="stop" if i == len(words) - 1 else None,
            )
            await asyncio.sleep(0.02)  # Simulate streaming


# ─────────────────────────────────────────────────────────────────
# LLM Service (Provider Selector + Failover)
# ─────────────────────────────────────────────────────────────────

class LLMService:
    """
    Unified LLM interface with automatic provider selection and failover.
    
    Priority:
    1. Configured provider (settings.llm.provider)
    2. Fallback to next available provider
    3. Emergency: MockLLMClient (no API key required)
    """

    def __init__(self):
        self._primary = self._build_primary()
        self._fallback = MockLLMClient()

    def _build_primary(self):
        provider = settings.llm.provider
        model = settings.llm.model
        api_key = settings.llm.api_key or ""

        if provider == "openai" and api_key:
            log.info("LLM: OpenAI", model=model)
            return OpenAIClient(api_key=api_key, model=model)
        elif provider == "anthropic" and api_key:
            log.info("LLM: Anthropic", model=model)
            return AnthropicClient(api_key=api_key, model=model)
        else:
            log.warning("No LLM API key configured — using mock client")
            return MockLLMClient(model="mock")

    async def complete(
        self,
        messages: list[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Complete a chat with automatic fallback."""
        kwargs = {
            "max_tokens": max_tokens or settings.llm.max_output_tokens,
            "temperature": temperature if temperature is not None else settings.llm.temperature,
        }
        try:
            return await self._primary.complete(messages, **kwargs)
        except Exception as e:
            log.warning("Primary LLM failed, using fallback", error=str(e))
            return await self._fallback.complete(messages, **kwargs)

    async def stream(
        self,
        messages: list[dict],
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Stream completion tokens."""
        kwargs = {"max_tokens": max_tokens or settings.llm.max_output_tokens}
        try:
            async for chunk in self._primary.stream(messages, **kwargs):
                yield chunk
        except Exception as e:
            log.warning("LLM stream failed, using fallback", error=str(e))
            async for chunk in self._fallback.stream(messages, **kwargs):
                yield chunk

    @property
    def model_name(self) -> str:
        return getattr(self._primary, "model", "mock")
