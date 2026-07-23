"""
Unit tests for the Export Engine.
"""

from __future__ import annotations

import os
import tempfile
import pytest
import numpy as np

from src.export import (
    ExportEngine,
    ExportReport,
    JSONExporter,
    JSONConfig,
    MarkdownExporter,
    MarkdownConfig,
    YAMLExporter,
    YAMLConfig,
    UniversalExporter,
    UniversalExportObject,
    AgentFormatter,
    format_citation,
    format_table,
    format_metadata,
    ExportTokenBudget,
    TokenAllocator,
    ExportVerifier,
    VerificationResult,
    ExportEngineError,
    InvalidContextError,
    FormatError,
    VerificationError,
)


@pytest.fixture
def sample_ueo() -> UniversalExportObject:
    """Create a sample UniversalExportObject for testing."""
    return UniversalExportObject(
        system="You are a helpful document assistant.",
        context="AEGIS-DocIntel is an agentic AI document intelligence system.",
        summary="AEGIS-DocIntel processes documents using advanced engines.",
        citations=[
            {"doc_id": "doc1", "page": 2, "section": "Introduction", "excerpt": "AEGIS-DocIntel is agentic."}
        ],
        metadata={"author": "AMDI Team", "doc_type": "manual"},
        tables=[
            {"headers": ["Metric", "Value"], "rows": [["Accuracy", 0.99], ["Latency", "5ms"]]}
        ],
        confidence=0.95,
        total_tokens=150,
    )


def test_formatters() -> None:
    # 1. format_citation
    citation = {"doc_id": "doc1", "page": 3, "section": "Overview", "excerpt": "Sample text."}
    assert format_citation(citation, style="bracketed") == "[doc1, p.3, §Overview] Sample text."
    assert format_citation(citation, style="footnote") == "¹ doc1, p.3"
    assert format_citation(citation, style="inline") == "(doc1, p.3)"
    
    # 2. format_table
    table = {
        "headers": ["A", "B"],
        "rows": [[1, 2], [3, 4]]
    }
    rendered_table = format_table(table)
    assert "| A | B |" in rendered_table
    assert "| 1 | 2 |" in rendered_table

    # 3. format_metadata
    meta = {"a": 1, "b": {"c": 2}}
    rendered_meta = format_metadata(meta)
    assert "a: 1" in rendered_meta
    assert "  c: 2" in rendered_meta


def test_json_exporter(sample_ueo: UniversalExportObject) -> None:
    exporter = JSONExporter(JSONConfig(pretty=True))
    json_str = exporter.export(sample_ueo)
    assert '"system": "You are a helpful document assistant."' in json_str
    assert '"confidence": 0.95' in json_str

    d = exporter.export_dict(sample_ueo)
    assert d["system"] == sample_ueo.system
    assert d["confidence"] == 0.95


def test_markdown_exporter(sample_ueo: UniversalExportObject) -> None:
    exporter = MarkdownExporter(MarkdownConfig(heading_level=1))
    md_str = exporter.export(sample_ueo)
    assert "# AMDI-OS Context Export" in md_str
    assert "## System" in md_str
    assert "## Summary" in md_str
    assert "## Content" in md_str
    assert "## Tables" in md_str
    assert "## Citations" in md_str
    assert "## Metadata" in md_str


def test_yaml_exporter(sample_ueo: UniversalExportObject) -> None:
    exporter = YAMLExporter()
    yaml_str = exporter.export(sample_ueo)
    assert "system:" in yaml_str
    assert "confidence: 0.95" in yaml_str


def test_token_budget_and_allocator() -> None:
    # 1. Budget creation
    budget = ExportTokenBudget.for_agent("chatgpt-4o")
    assert budget.max_tokens == 128_000
    assert budget.effective_limit() == int(128_000 * 0.95)
    assert budget.fits(100)
    assert not budget.fits(130_000)

    # 2. Allocator scaling
    allocator = TokenAllocator(budget)
    # Total fits within budget (limit is 121,600)
    res_fit = allocator.allocate(500, 1000, 5000, 1000)
    assert res_fit.content_budget == budget.content_budget

    # Total exceeds budget, force scaling down content
    huge_content = 200_000
    res_scale = allocator.allocate(500, 1000, huge_content, 1000)
    assert res_scale.content_budget < budget.content_budget


def test_universal_exporter_and_formatting(sample_ueo: UniversalExportObject) -> None:
    exporter = UniversalExporter()
    
    # 1. Build UEO
    ueo = exporter.build_ueo(
        system="sys",
        context="ctx",
        summary="sum",
        confidence=0.8,
    )
    assert ueo.system == "sys"
    assert ueo.context == "ctx"
    assert ueo.summary == "sum"
    assert ueo.confidence == 0.8

    # 2. Citation Extraction
    citations_raw = "[doc1, p.4, §Intro] excerpt text\n[doc2, p.10] another snippet"
    citations = exporter._extract_citations(citations_raw)
    assert len(citations) == 2
    assert citations[0]["doc_id"] == "doc1"
    assert citations[0]["page"] == 4
    assert citations[0]["section"] == "Intro"
    assert citations[0]["excerpt"] == "excerpt text"

    # 3. Agent Formats
    formatter = AgentFormatter()
    
    chatgpt_pay = formatter.format_for_agent(sample_ueo, "chatgpt")
    assert "system" in chatgpt_pay
    assert "context" in chatgpt_pay
    assert "citations" in chatgpt_pay

    gemini_pay = formatter.format_for_agent(sample_ueo, "gemini")
    assert "text" in gemini_pay
    assert "tables" in gemini_pay
    assert "graphs" in gemini_pay

    claude_pay = formatter.format_for_agent(sample_ueo, "claude")
    assert "summary" in claude_pay
    assert "context" in claude_pay
    assert "relationships" in claude_pay

    deepseek_pay = formatter.format_for_agent(sample_ueo, "deepseek")
    assert "system" in deepseek_pay
    assert "content" in deepseek_pay

    qwen_pay = formatter.format_for_agent(sample_ueo, "qwen")
    assert "system" in qwen_pay
    assert "context" in qwen_pay
    assert "metadata" in qwen_pay


def test_export_verifier(sample_ueo: UniversalExportObject) -> None:
    verifier = ExportVerifier(min_confidence=0.6)
    
    # 1. Valid UEO
    res = verifier.verify(sample_ueo)
    assert res.is_valid
    assert "system_present" in res.checks_passed
    assert "context_present" in res.checks_passed

    # 2. Low Confidence UEO
    low_conf_ueo = UniversalExportObject(
        system="sys", context="ctx", confidence=0.3
    )
    res_low = verifier.verify(low_conf_ueo)
    assert not res_low.is_valid
    assert "low_confidence" in res_low.checks_failed

    with pytest.raises(VerificationError):
        verifier.verify_or_raise(low_conf_ueo)

    # 3. Hallucination Heuristics (High confidence + extremely low content)
    halluc_ueo = UniversalExportObject(
        system="sys", context="short", confidence=0.95
    )
    res_halluc = verifier.verify(halluc_ueo)
    assert "high_confidence_low_content" in res_halluc.warnings


def test_export_engine_e2e(sample_ueo: UniversalExportObject) -> None:
    engine = ExportEngine(version="1.0.0", default_agent="chatgpt")
    
    # 1. get_token_budget
    budget = engine.get_token_budget("chatgpt-4o")
    assert budget.max_tokens == 128_000
    
    # 2. export_ueo E2E
    report = engine.export_ueo(
        sample_ueo,
        formats=["json", "markdown", "yaml", "ueo"],
        agents=["chatgpt", "gemini"],
        verify=True,
    )
    assert isinstance(report, ExportReport)
    assert report.verification.is_valid
    assert "json" in report.formats
    assert "markdown" in report.formats
    assert "yaml" in report.formats
    assert "ueo" in report.formats
    assert "chatgpt" in report.agent_payloads
    assert "gemini" in report.agent_payloads

    report_dict = report.to_dict()
    assert report_dict["formats"] == ["json", "markdown", "yaml", "ueo"]
    assert report_dict["ueo"]["confidence"] == 0.95

    # 3. export_to_files
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = engine.export_to_files(sample_ueo, output_dir=tmpdir, base_name="test_ctx")
        assert "json" in paths
        assert "markdown" in paths
        assert "yaml" in paths
        assert os.path.exists(paths["json"])
        assert os.path.exists(paths["markdown"])
        assert os.path.exists(paths["yaml"])
