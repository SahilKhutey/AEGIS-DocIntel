"""
End-to-End Verification Harness Test (demo/tests/test_demo_e2e_verify.py)
Validates the complete Product Launch Edition demo experience:
- Health and readiness probes
- Demo session and guided tour configuration
- Seeded document catalog
- Ask AEGIS evidence RAG query and citation resolution
- Model abstention on unanswerable query (zero hallucination)
- Cross-document comparison & contradiction detection
- Tenant isolation boundaries
"""
import pytest
import httpx
from demo.scripts.seed_demo import seed_in_process
from demo.scripts.verify_demo import DemoVerifier
from src.config import settings
from src.main import create_app
from src.services.container import ServiceContainer


@pytest.mark.asyncio
async def test_launch_verification_e2e(tmp_path):
    db_path = tmp_path / "test_e2e_documents.db"
    audit_path = tmp_path / "test_e2e_audit.log"

    import os
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("AEGIS_SQLITE_PATH", str(db_path))
        mp.setenv("AEGIS_AUDIT_LOG_PATH", str(audit_path))
        mp.setenv("AEGIS_DEMO_MODE", "true")
        mp.setenv("AEGIS_DEMO_ALLOW_ANONYMOUS", "true")
        mp.setenv("AEGIS_ENVIRONMENT", "demo")

        app = create_app()
        container = ServiceContainer(settings)
        await container.startup()
        app.state.container = container
        app.state.orchestrator = container.rag_engine
        app.state.intelligence_service = container.intelligence_service

        try:
            # 1. Seed demo documents into container
            seeded = await seed_in_process(container, tenant_id="demo-tenant")
            assert len(seeded) >= 3

            # 2. Run DemoVerifier against the in-memory ASGI app
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                verifier = DemoVerifier(base_url="http://testserver")

                # Verify all steps
                await verifier._check_health(client)
                await verifier._check_demo_session(client)
                doc_map = await verifier._check_documents(client)
                assert len(doc_map) >= 3

                await verifier._check_queries(client, doc_map)
                await verifier._check_comparison(client, doc_map)
                await verifier._check_tenant_isolation(client)

                assert verifier.report["checks_failed"] == 0, f"Verification failed: {verifier.report['details']}"
                assert verifier.report["checks_passed"] >= 8

        finally:
            await container.shutdown()
