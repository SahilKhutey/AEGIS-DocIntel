"""
Unit tests for LLMInterface provider wiring, mock fallback, and real LLM invocation paths.
Validates:
- Default mock provider returns structured mock response and parses citations
- Mock streaming yields tokens asynchronously
- Real provider configuration (e.g. openai, anthropic) initializes correct model_id
- Fallback to mock when real provider requested but no backends available
- Native AsyncOpenAI / litellm invocation path mock
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from src.engines.llm.llm_interface import LLMInterface, LLMResponse


@dataclass
class DummyContext:
    messages: list
    source_map: dict
    table_count: int = 0


@pytest.mark.asyncio
async def test_llm_interface_mock_provider():
    llm = LLMInterface(llm_provider="mock", model="mock-model")
    ctx = DummyContext(
        messages=[{"role": "user", "content": "What is the revenue?"}],
        source_map={1: "elem-1", 2: "elem-2"},
        table_count=1,
    )
    resp = await llm.reason("What is the revenue?", ctx, hits=None, tables=None)
    assert isinstance(resp, LLMResponse)
    assert "[MOCK]" in resp.answer
    assert "[1]" in resp.answer
    assert "[2]" in resp.answer
    assert [c["ref"] for c in resp.citations] == [1, 2]
    assert resp.grounded is True
    assert resp.model == "mock"


@pytest.mark.asyncio
async def test_llm_interface_mock_streaming():
    llm = LLMInterface(llm_provider="mock")
    ctx = DummyContext(messages=[], source_map={})
    tokens = []
    async for token in llm.stream_reason("Test question", ctx, hits=None):
        tokens.append(token)
    streamed_text = "".join(tokens)
    assert "[MOCK STREAM]" in streamed_text


@pytest.mark.asyncio
async def test_llm_interface_real_provider_litellm():
    pytest.importorskip("litellm")
    llm = LLMInterface(llm_provider="openai", model="gpt-4o", api_key="sk-test-key")
    assert llm._provider == "openai"
    assert llm._model == "gpt-4o"
    assert llm._api_key == "sk-test-key"

    ctx = DummyContext(
        messages=[{"role": "user", "content": "Test prompt"}],
        source_map={1: "elem-1"},
    )

    mock_completion_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Real AI answer referencing [1]."
    mock_completion_resp.choices = [mock_choice]
    mock_completion_resp.usage.prompt_tokens = 15
    mock_completion_resp.usage.completion_tokens = 25

    with patch("src.engines.llm.llm_interface.litellm.acompletion", new=AsyncMock(return_value=mock_completion_resp)) as mock_acomplete:
        resp = await llm.reason("Test prompt", ctx, hits=None, tables=None)
        assert resp.answer == "Real AI answer referencing [1]."
        assert [c["ref"] for c in resp.citations] == [1]
        assert resp.grounded is True
        assert resp.input_tokens == 15
        assert resp.output_tokens == 25
        mock_acomplete.assert_awaited_once()


@pytest.mark.asyncio
async def test_llm_interface_fallback_to_mock_when_no_backend():
    with patch("src.engines.llm.llm_interface._LITELLM_AVAILABLE", False):
        with patch.dict("sys.modules", {"openai": None}):
            llm = LLMInterface(llm_provider="anthropic", model="claude-3-opus")
            assert llm._provider == "mock"
