"""
Tests for PROT-FINAL-05: Workload Sandboxing & LLM Isolation
Covers DEP-TEST-009, DEP-TEST-010, DEP-TEST-014
"""

import os
import glob
import tempfile
import pytest

from src.ingestion.secure_parser import (
    SecureDocumentParser,
    ParserResourceExceededError,
    ParserTimeoutError,
)
from src.llm_service.isolated_adapter import (
    IsolatedLLMAdapter,
    ProviderSecurityViolation,
)


def test_dep_009_untrusted_document_parser_isolation():
    """DEP-TEST-009: Parser isolates workload, enforces limits, and completely wipes scratch directory."""
    parser = SecureDocumentParser(max_file_size_bytes=1024, max_pages=10, timeout_seconds=1.0)
    tenant_id = "tenant-safe-1"
    
    # Normal execution
    content = b"%PDF-1.4 Minimal test PDF content"
    ok, err, res = parser.parse_document("test.pdf", content, tenant_id=tenant_id)
    assert ok
    assert err is None
    assert res["macros_stripped"] is True

    # Verify no scratch directory was left behind
    temp_dir = tempfile.gettempdir()
    matching_dirs = glob.glob(os.path.join(temp_dir, f"aegis_scratch_{tenant_id}_*"))
    assert len(matching_dirs) == 0, f"Leaked scratch directories: {matching_dirs}"

    # Over-sized content is rejected
    big_content = b"A" * 2048
    ok_big, err_big, _ = parser.parse_document("big.pdf", big_content, tenant_id=tenant_id)
    assert not ok_big
    assert "exceeds parser ceiling" in err_big

    # Timeout enforcement
    ok_timeout, err_timeout, _ = parser.parse_document(
        "slow.pdf", content, tenant_id=tenant_id, simulated_delay=2.0
    )
    assert not ok_timeout
    assert "exceeded timeout limit" in err_timeout


def test_dep_010_llm_provider_key_never_exposed():
    """DEP-TEST-010: LLM provider keys remain server-side; client attempts to inject keys are denied."""
    adapter = IsolatedLLMAdapter()

    # Client cannot supply their own API key
    with pytest.raises(ProviderSecurityViolation, match="Client-supplied provider credentials are strictly prohibited"):
        adapter.execute_completion(
            tenant_id="tenant-x",
            user_prompt="Analyze this financial clause",
            client_supplied_key="sk-malicious-user-key",
        )

    # Client cannot redirect outbound LLM traffic to arbitrary untrusted endpoint
    with pytest.raises(ProviderSecurityViolation, match="not in the approved provider network allowlist"):
        adapter.execute_completion(
            tenant_id="tenant-x",
            user_prompt="Analyze this financial clause",
            custom_endpoint="https://attacker-controlled-proxy.com/v1",
        )

    # Valid completion does NOT leak server API key in response
    res = adapter.execute_completion(tenant_id="tenant-x", user_prompt="Analyze this")
    assert res["status"] == "COMPLETED"
    assert "sk-" not in str(res)
    assert "sk-live" not in str(res)


def test_dep_014_worker_crash_failure_isolation():
    """DEP-TEST-014: Worker crash cleans up scratchpad and fails safely without corrupting state."""
    parser = SecureDocumentParser()
    tenant_id = "tenant-crash-test"

    ok, err, res = parser.parse_document(
        "crash.pdf",
        b"%PDF-1.4 crash payload",
        tenant_id=tenant_id,
        simulated_crash=True,
    )
    assert not ok
    assert "Simulated worker SIGKILL/OOM crash" in err
    assert res is None

    # Verify scratchpad was wiped even after crash
    temp_dir = tempfile.gettempdir()
    matching = glob.glob(os.path.join(temp_dir, f"aegis_scratch_{tenant_id}_*"))
    assert len(matching) == 0
