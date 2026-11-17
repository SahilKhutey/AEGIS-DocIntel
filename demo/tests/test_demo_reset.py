"""
Tests for Demo Reset and Tenant Isolation (demo/tests/test_demo_reset.py)
Validates:
- Ephemeral user uploads are wiped during demo reset
- Manifest seed documents are restored to pristine ready state
- Reset operation is strictly scoped to demo-tenant (never touches other tenants)
"""
import pytest
from demo.scripts.reset_demo import execute_demo_reset
from demo.scripts.seed_demo import _extract_items, _get_attr
from src.config import settings
from src.services.container import ServiceContainer


@pytest.mark.asyncio
async def test_demo_reset_lifecycle_and_tenant_boundary(tmp_path):
    db_path = tmp_path / "test_reset_documents.db"
    audit_path = tmp_path / "test_reset_audit.log"

    import os
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AEGIS_SQLITE_PATH", str(db_path))
        mp.setenv("AEGIS_AUDIT_LOG_PATH", str(audit_path))
        mp.setenv("AEGIS_DEMO_MODE", "true")

        container = ServiceContainer(settings)
        await container.startup()
        try:
            doc_service = container.document_service

            # 1. Ingest an ephemeral document as demo-tenant
            ephemeral_doc = await doc_service.ingest(
                file_bytes=b"Temporary user uploaded test file for evaluation.\n\nSection two with sufficient elements.",
                filename="visitor_scratch_upload.txt",
                content_type="text/plain",
                tenant_id="demo-tenant",
            )
            ephemeral_id = getattr(ephemeral_doc, "doc_id", ephemeral_doc.get("doc_id") if isinstance(ephemeral_doc, dict) else None)

            # 2. Ingest a document for an isolated enterprise tenant
            foreign_doc = await doc_service.ingest(
                file_bytes=b"Confidential enterprise operational blueprint.\n\nSection two with detailed security topology.",
                filename="enterprise_blueprint.txt",
                content_type="text/plain",
                tenant_id="enterprise-tenant-alpha",
            )
            foreign_id = getattr(foreign_doc, "doc_id", foreign_doc.get("doc_id") if isinstance(foreign_doc, dict) else None)

            # 3. Execute demo reset
            restored_count = await execute_demo_reset(container, tenant_id="demo-tenant")
            assert restored_count >= 3

            # 4. Verify demo-tenant documents
            demo_res = await doc_service.list_documents(tenant_id="demo-tenant")
            demo_items = _extract_items(demo_res)
            demo_filenames = [_get_attr(d, "filename") for d in demo_items]

            # Ephemeral visitor upload must be gone
            assert "visitor_scratch_upload.txt" not in demo_filenames

            # Seed documents must be restored
            assert "aegis_neural_hardware_spec_v1.txt" in demo_filenames
            assert "aegis_neural_hardware_spec_v2.txt" in demo_filenames
            assert "aegis_enterprise_governance_whitepaper.txt" in demo_filenames

            # 5. Verify enterprise tenant document was NOT affected by demo reset
            foreign_res = await doc_service.list_documents(tenant_id="enterprise-tenant-alpha")
            foreign_items = _extract_items(foreign_res)
            foreign_filenames = [_get_attr(d, "filename") for d in foreign_items]
            assert "enterprise_blueprint.txt" in foreign_filenames

        finally:
            await container.shutdown()
