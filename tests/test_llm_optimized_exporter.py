'''
AEGIS-DocIntel / AMDI-OS — LLM Token-Optimized Exporter Test Suite
===================================================================
Verifies hyper-dense Markdown and minified JSON export formatting,
token budget capping, and REST API endpoint.
'''
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.export.universal_exporter import UniversalExportObject
from src.export.llm_optimized_exporter import LLMTokenOptimizedExporter, LLMExportConfig
from src.ael.token_budget import count_tokens
from src.main import app

client = TestClient(app)


def test_llm_optimized_exporter_markdown_direct():
    ueo = UniversalExportObject(
        system="You are an expert analyst.",
        summary="Quarterly revenue grew by 25% year-over-year.",
        context="Company revenue reached $10M.\n\nProfit margin expanded to 18%.\n\n\nOperational expenses decreased.",
        citations=[{"doc_id": "Doc10K", "page": 4, "text": "Snippet text"}],
        metadata={"filename": "report.pdf"},
    )

    cfg = LLMExportConfig(max_tokens=4000, format_type="markdown", compression_level="high")
    exporter = LLMTokenOptimizedExporter(config=cfg)
    md_output = exporter.export(ueo)

    assert "> **Context Summary**:" in md_output
    assert "### System:" in md_output
    assert "### Content" in md_output
    assert "[Doc10K:p4]" in md_output
    assert count_tokens(md_output) <= 4000


def test_llm_optimized_exporter_json_direct():
    ueo = UniversalExportObject(
        system="System prompt instruction.",
        summary="Short summary.",
        context="Full document context text goes here.",
        citations=[{"doc_id": "D1", "page": 2}],
        metadata={"author": "AEGIS"},
    )

    cfg = LLMExportConfig(max_tokens=2000, format_type="json", compact_keys=True)
    exporter = LLMTokenOptimizedExporter(config=cfg)
    json_output = exporter.export(ueo)

    assert '"sys":' in json_output
    assert '"ctx":' in json_output
    assert '"sum":' in json_output
    assert '"cits":' in json_output
    assert "\n" not in json_output  # Verify minified single line
    assert count_tokens(json_output) <= 2000


def test_llm_optimized_exporter_budget_truncation():
    long_text = "Word " * 1000  # ~1000 tokens
    ueo = UniversalExportObject(system="Sys", context=long_text, summary="Sum")

    cfg = LLMExportConfig(max_tokens=200, format_type="markdown")
    exporter = LLMTokenOptimizedExporter(config=cfg)
    truncated_output = exporter.export(ueo)

    assert "[Context Truncated to fit Token Budget]" in truncated_output
    assert count_tokens(truncated_output) <= 250


def test_api_export_llm_optimized_endpoint():
    resp = client.post(
        "/v1/advanced/export/llm-optimized",
        json={
            "system_prompt": "Perform legal risk analysis.",
            "context_text": "Clause 1: Liability limit is $1,000,000.\nClause 2: Indemnification applies.",
            "max_tokens": 1000,
            "format_type": "markdown",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["format_type"] == "markdown"
    assert data["tokens_used"] <= 1000
    assert "exported_content" in data
