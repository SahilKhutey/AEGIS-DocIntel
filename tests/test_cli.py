"""
AEGIS-DocIntel — Command Line Interface (CLI) Test Suite
========================================================
Validates CLI argument parsing, environment variable propagation,
command dispatching (ingest, query, batch, export, serve), and error handling.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.cli import (
    get_llm_config,
    main,
    run_batch,
    run_export,
    run_ingest,
    run_query,
    run_serve,
)


def test_get_llm_config_defaults(monkeypatch):
    """Verify default LLM configuration when env vars are unset."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    config = get_llm_config()
    assert config["llm_provider"] == "openai"
    assert config["llm_model"] == "gpt-4o-mini"
    assert config["llm_api_key"] == ""


def test_get_llm_config_reads_env(monkeypatch):
    """Verify get_llm_config reads environment variables."""
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("LLM_API_KEY", "sk-ant-test-key-12345")

    config = get_llm_config()
    assert config["llm_provider"] == "anthropic"
    assert config["llm_model"] == "claude-3-5-sonnet-20241022"
    assert config["llm_api_key"] == "sk-ant-test-key-12345"


def test_cli_help_exits_zero(monkeypatch, capsys):
    """Verify --help argument prints usage and exits cleanly with 0."""
    monkeypatch.setattr(sys, "argv", ["aegis-cli", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "AEGIS-MIOS CLI Tool" in captured.out
    assert "Available commands" in captured.out


def test_cli_no_args_prints_help(monkeypatch, capsys):
    """Verify calling CLI with no arguments prints help."""
    monkeypatch.setattr(sys, "argv", ["aegis-cli"])
    main()
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()


@pytest.mark.asyncio
async def test_run_ingest_missing_file(capsys):
    """Verify run_ingest handles non-existent file by printing error and exiting with code 1."""
    with pytest.raises(SystemExit) as excinfo:
        await run_ingest("non_existent_file_path_12345.pdf")
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


@pytest.mark.asyncio
async def test_run_ingest_valid_file(capsys):
    """Verify run_ingest processes an existing text fixture and records .amdi_last_doc."""
    sample_file = "tests/fixtures/sample.txt"
    await run_ingest(sample_file)
    captured = capsys.readouterr()
    assert "Ingestion successful!" in captured.out
    assert Path(".amdi_last_doc").exists()
    last_doc = Path(".amdi_last_doc").read_text(encoding="utf-8").strip()
    assert len(last_doc) > 0


@pytest.mark.asyncio
async def test_run_query_execution(capsys):
    """Verify run_query executes against last ingested doc."""
    await run_query("What is the revenue?", doc_id=None)
    captured = capsys.readouterr()
    assert "Executing query:" in captured.out
    assert "--- Answer ---" in captured.out
    assert "Confidence:" in captured.out


@pytest.mark.asyncio
async def test_run_batch_execution(capsys):
    """Verify run_batch processes fixture directory."""
    await run_batch("tests/fixtures", "*.txt")
    captured = capsys.readouterr()
    assert "Starting batch processing" in captured.out
    assert "Batch processing completed!" in captured.out


@pytest.mark.asyncio
async def test_run_export_execution(capsys):
    """Verify run_export ingests, queries, and exports to agent."""
    sample_file = "tests/fixtures/sample.txt"
    with patch("src.workflows.export_workflow.get_connector") as mock_get_conn:
        mock_conn = AsyncMock()
        mock_conn.send = AsyncMock(return_value={"status": "success", "content": "Exported response"})
        mock_get_conn.return_value = mock_conn

        await run_export(sample_file, "Summarize performance", agent="chatgpt")

    captured = capsys.readouterr()
    assert "Ingesting sample.txt for agent export..." in captured.out
    assert "--- Export Result ---" in captured.out


def test_run_serve_invokes_uvicorn():
    """Verify run_serve imports uvicorn and starts the FastAPI app."""
    with patch("uvicorn.run") as mock_uvicorn_run:
        run_serve()
        assert mock_uvicorn_run.called
        args, kwargs = mock_uvicorn_run.call_args
        assert kwargs.get("port") == 8000
        assert kwargs.get("host") == "0.0.0.0"


def test_cli_main_subcommand_dispatch(monkeypatch):
    """Verify main() properly dispatches to each subcommand."""
    # 1. Test ingest dispatch
    with patch("src.cli.run_ingest", new_callable=AsyncMock) as mock_ingest:
        monkeypatch.setattr(sys, "argv", ["aegis-cli", "ingest", "test.pdf"])
        main()
        assert mock_ingest.called

    # 2. Test query dispatch
    with patch("src.cli.run_query", new_callable=AsyncMock) as mock_query:
        monkeypatch.setattr(sys, "argv", ["aegis-cli", "query", "What is X?", "--doc-id", "doc123"])
        main()
        assert mock_query.called

    # 3. Test batch dispatch
    with patch("src.cli.run_batch", new_callable=AsyncMock) as mock_batch:
        monkeypatch.setattr(sys, "argv", ["aegis-cli", "batch", "my_dir", "--pattern", "*.txt"])
        main()
        assert mock_batch.called

    # 4. Test export dispatch
    with patch("src.cli.run_export", new_callable=AsyncMock) as mock_export:
        monkeypatch.setattr(sys, "argv", ["aegis-cli", "export", "doc.txt", "Question?", "claude"])
        main()
        assert mock_export.called

    # 5. Test serve dispatch
    with patch("src.cli.run_serve") as mock_serve:
        monkeypatch.setattr(sys, "argv", ["aegis-cli", "serve"])
        main()
        assert mock_serve.called
