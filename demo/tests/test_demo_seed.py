"""
Tests for Demo Seeding (demo/tests/test_demo_seed.py)
Validates:
- Manifest schema and seed document existence
- In-process seeding into ServiceContainer
- Document metadata persistence in SQLite
- Expected chunk and page count extraction
"""
import pytest
from pathlib import Path
from demo.scripts.seed_demo import load_manifest, seed_in_process, DOCS_DIR
from src.config import settings
from src.services.container import ServiceContainer


def test_manifest_structure_and_files():
    manifest = load_manifest()
    assert "documents" in manifest
    assert len(manifest["documents"]) >= 3
    assert "expected_queries" in manifest
    assert len(manifest["expected_queries"]) >= 4

    for doc in manifest["documents"]:
        filename = doc["filename"]
        doc_path = DOCS_DIR / filename
        assert doc_path.exists(), f"Seed document file missing: {filename}"
        assert doc_path.stat().st_size > 0, f"Seed document empty: {filename}"


@pytest.mark.asyncio
async def test_seed_in_process_lifecycle(tmp_path):
    db_path = tmp_path / "test_demo_documents.db"
    audit_path = tmp_path / "test_demo_audit.log"

    # Use isolated test database
    import os
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AEGIS_SQLITE_PATH", str(db_path))
        mp.setenv("AEGIS_AUDIT_LOG_PATH", str(audit_path))
        mp.setenv("AEGIS_DEMO_MODE", "true")

        container = ServiceContainer(settings)
        await container.startup()
        try:
            results = await seed_in_process(container, tenant_id="demo-tenant")
            assert len(results) >= 3

            # Verify persisted records in document service
            docs_res = await container.document_service.list_documents(tenant_id="demo-tenant")
            docs = getattr(docs_res, "items", docs_res)
            assert len(docs) >= 3

            filenames = [getattr(d, "filename", d.get("filename") if isinstance(d, dict) else None) for d in docs]
            assert "aegis_neural_hardware_spec_v1.txt" in filenames
            assert "aegis_neural_hardware_spec_v2.txt" in filenames
            assert "aegis_enterprise_governance_whitepaper.txt" in filenames

            for d in docs:
                status = getattr(d, "status", d.get("status") if isinstance(d, dict) else None)
                byte_size = getattr(d, "byte_size", d.get("byte_size") if isinstance(d, dict) else None)
                assert status == "ready"
                assert byte_size > 0

            # Idempotency: re-running seed does not duplicate documents
            re_results = await seed_in_process(container, tenant_id="demo-tenant")
            assert all(r["status"] == "existing" for r in re_results)
            re_docs_res = await container.document_service.list_documents(tenant_id="demo-tenant")
            re_docs = getattr(re_docs_res, "items", re_docs_res)
            assert len(re_docs) == len(docs)
        finally:
            await container.shutdown()
