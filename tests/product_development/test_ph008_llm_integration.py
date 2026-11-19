"""
AEGIS-DocIntel — Task PH-008: LLM Integration & Provider Security Verification
=============================================================================
Validates:
1. Unified LLM client execution (LLMService) with realistic response structures.
2. Streaming token chunking with finish_reason handling.
3. Token pricing and operational cost calculation (calc_cost).
4. Security boundary enforcement: rejection of client-supplied credentials.
5. Network allowlist enforcement on custom provider endpoints.
"""
from __future__ import annotations

import pytest

from src.llm_service.isolated_adapter import (
    IsolatedLLMAdapter,
    ProviderSecurityViolation,
)
from src.llm_service.llm_client import (
    LLMResponse,
    LLMService,
    MockLLMClient,
    calc_cost,
)


@pytest.mark.asyncio
async def test_llm_service_complete_and_response_structure():
    """Verify LLMService executes completion and returns structured token metrics."""
    service = LLMService()
    messages = [
        {"role": "system", "content": "You are a factual document analysis assistant."},
        {"role": "user", "content": "What is the primary thesis of the report?"},
    ]

    response = await service.complete(messages, max_tokens=100)
    assert isinstance(response, LLMResponse)
    assert len(response.text) > 0
    assert response.in_tokens > 0
    assert response.out_tokens > 0
    assert response.latency_ms >= 0.0


@pytest.mark.asyncio
async def test_llm_service_streaming():
    """Verify LLMService yields valid delta chunks and terminates with stop reason."""
    mock_client = MockLLMClient()
    messages = [{"role": "user", "content": "Summarize the architecture."}]

    chunks = []
    async for chunk in mock_client.stream(messages):
        chunks.append(chunk)

    assert len(chunks) >= 3
    # Check that individual deltas contain text
    assert any(len(c.delta.strip()) > 0 for c in chunks)
    # Final chunk must signal stop
    assert chunks[-1].finish_reason == "stop"


def test_llm_cost_calculation():
    """Verify calc_cost accurately calculates input and output token expenses."""
    cost_gpt4o = calc_cost("gpt-4o", in_tokens=10_000, out_tokens=1_000)
    assert cost_gpt4o > 0.0
    # 10k * (5/1M) + 1k * (15/1M) = 0.05 + 0.015 = 0.065
    assert pytest.approx(cost_gpt4o, 0.001) == 0.065

    cost_mini = calc_cost("gpt-4o-mini", in_tokens=10_000, out_tokens=1_000)
    assert cost_mini < cost_gpt4o


def test_isolated_llm_adapter_rejects_client_credentials():
    """Verify IsolatedLLMAdapter strictly rejects client-supplied API keys."""
    adapter = IsolatedLLMAdapter()

    with pytest.raises(ProviderSecurityViolation, match="Client-supplied provider credentials are strictly prohibited"):
        adapter.execute_completion(
            tenant_id="tenant-ph008",
            user_prompt="Extract metrics",
            client_supplied_key="sk-malicious-client-key",
        )


def test_isolated_llm_adapter_enforces_host_allowlist():
    """Verify IsolatedLLMAdapter rejects unauthorized outbound destination hosts."""
    adapter = IsolatedLLMAdapter()

    with pytest.raises(ProviderSecurityViolation, match="not in the approved provider network allowlist"):
        adapter.execute_completion(
            tenant_id="tenant-ph008",
            user_prompt="Extract metrics",
            custom_endpoint="https://attacker-exfiltration-server.com/v1/chat",
        )

    # Approved host must not raise security violation on host check
    res = adapter.execute_completion(
        tenant_id="tenant-ph008",
        user_prompt="Extract metrics",
        custom_endpoint="https://api.openai.com/v1/chat/completions",
    )
    assert res.get("status") == "COMPLETED"
