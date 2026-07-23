"""
Unit tests for the AI Agent Connectors.
"""

from __future__ import annotations

import pytest

from src.connectors import (
    get_connector,
    ConnectorFactory,
    ConnectorConfig,
    ConnectorResponse,
    ConnectionStatus,
    AgentTokenBudget,
    ResponseParser,
    ParsedResponse,
    TokenLimitError,
)


@pytest.fixture
def mock_ueo() -> object:
    """Create a mock UniversalExportObject for testing."""
    class MockUEO:
        system = "You are a research assistant."
        context = "AMDI-OS processes document structures mathematically."
        summary = "AMDI-OS summary."
        citations = [
            {"doc_id": "doc1", "excerpt": "extracted fact"}
        ]
        metadata = {"doc_type": "PDF"}
    return MockUEO()


def test_token_budget_specs() -> None:
    # 1. ChatGPT-4o budget
    budget_gpt = AgentTokenBudget.for_agent("chatgpt-4o")
    assert budget_gpt.max_context_tokens == 128_000
    assert budget_gpt.max_output_tokens == 16_384
    assert budget_gpt.safety_margin == 1_000
    assert budget_gpt.effective_limit() == 128_000 - 1_000 - 16_384

    # 2. Gemini budget
    budget_gemini = AgentTokenBudget.for_agent("gemini")
    assert budget_gemini.max_context_tokens == 1_000_000

    # 3. Local default
    budget_local = AgentTokenBudget.for_agent("local")
    assert budget_local.max_context_tokens == 8_192


def test_response_parser() -> None:
    parser = ResponseParser()
    
    text = (
        "Here is the answer [doc_1, p.5]. Section details:\n"
        "# Section 1\n"
        "This is details for section 1.\n"
        "Confidence: 95.5%\n"
        "# References\n"
        "- Citation 1\n"
        "- Citation 2"
    )
    
    parsed = parser.parse(text)
    assert parsed.text == text
    
    # Check citations
    assert len(parsed.citations) == 1
    assert parsed.citations[0]["doc_id"] == "doc_1"
    assert parsed.citations[0]["page"] == 5
    
    # Check sections
    assert "Section 1" in parsed.sections
    assert parsed.sections["Section 1"] == "This is details for section 1.\nConfidence: 95.5%"
    
    # Check confidence
    assert parsed.confidence == 0.955
    
    # Check references
    assert len(parsed.references) == 2
    assert parsed.references[0] == "Citation 1"
    assert parsed.references[1] == "Citation 2"


def test_connector_factory() -> None:
    # Factory create
    config = ConnectorConfig(model="chatgpt-4o")
    conn = ConnectorFactory.create("chatgpt", config)
    assert conn.AGENT_NAME == "chatgpt"

    # get_connector helper
    conn_helper = get_connector("gemini", model="gemini-1.5-flash")
    assert conn_helper.AGENT_NAME == "gemini"
    assert conn_helper.config.model == "gemini-1.5-flash"


def test_agent_connectors_dry_run(mock_ueo: object) -> None:
    # 1. ChatGPT
    gpt = get_connector("chatgpt", model="chatgpt-4o")
    resp_gpt = gpt.query("Hello ChatGPT")
    assert resp_gpt.success
    assert "[DRY-RUN ChatGPT response]" in resp_gpt.text
    assert resp_gpt.model == "chatgpt-4o"

    # ChatGPT send_ueo
    resp_ueo = gpt.send_ueo(mock_ueo, question="Compare layouts.")
    assert resp_ueo.success
    assert "Question: Compare layouts." in resp_ueo.text
    
    # 2. Gemini
    gemini = get_connector("gemini", model="gemini-1.5-pro")
    resp_gemini = gemini.query("Hello Gemini")
    assert resp_gemini.success
    assert "[DRY-RUN Gemini response]" in resp_gemini.text

    # 3. Claude
    claude = get_connector("claude", model="claude-3.5-sonnet")
    resp_claude = claude.query_with_context(question="Is it correct?", context="Context info.")
    assert resp_claude.success
    assert "[DRY-RUN Claude response]" in resp_claude.text
    assert "Context:\nContext info." in resp_claude.text

    # 4. DeepSeek
    ds = get_connector("deepseek", model="deepseek-chat")
    resp_ds = ds.query("Hello DeepSeek")
    assert resp_ds.success
    assert "[DRY-RUN DeepSeek response]" in resp_ds.text

    # 5. Qwen
    qwen = get_connector("qwen", model="qwen-2.5")
    resp_qwen = qwen.query("Hello Qwen")
    assert resp_qwen.success
    assert "[DRY-RUN Qwen response]" in resp_qwen.text


def test_local_connector() -> None:
    # 1. Ollama server type detection
    conn_ollama = get_connector("local", endpoint="http://localhost:11434", model="llama3")
    assert conn_ollama.server_type == "ollama"
    
    resp_oll = conn_ollama.query("Hello local ollama")
    assert resp_oll.success
    assert "[DRY-RUN Local response]" in resp_oll.text
    assert "Server Type: ollama" in resp_oll.text

    # 2. OpenAI-compatible local server
    conn_compat = get_connector("local", endpoint="http://localhost:1234/v1", model="mistral")
    assert conn_compat.server_type == "openai_compat"
    
    resp_comp = conn_compat.query("Hello compat local")
    assert resp_comp.success
    assert "Server Type: openai_compat" in resp_comp.text


def test_connector_token_budget_error() -> None:
    # Create budget for local model (limit is 8,192)
    conn = get_connector("local", model="local")
    
    # Sending a query that exceeds the budget
    huge_prompt = "word " * 10000
    with pytest.raises(TokenLimitError):
        conn.query(huge_prompt)
