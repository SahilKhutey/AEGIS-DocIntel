import pytest
import asyncio
from src.core.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_init():
    orchestrator = AMDIOrchestrator()
    assert orchestrator is not None
    await orchestrator.close()


@pytest.mark.asyncio
async def test_ingest_text_document():
    orchestrator = AMDIOrchestrator()
    try:
        doc = DocumentObject(
            filename="test.txt",
            raw_bytes=b"This is the first paragraph.\n\nThis is the second paragraph with more content.",
            format=DocumentFormat.TEXT
        )
        stats = await orchestrator.ingest(doc)
        
        assert stats is not None
        assert "doc_id" in stats
        assert stats["filename"] == "test.txt"
        assert stats["pages"] == 1
        assert stats["elements"] == 2
        assert "ingestion_ms" in stats
        assert "compression_pct" in stats
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_query_after_ingest():
    orchestrator = AMDIOrchestrator()
    try:
        doc = DocumentObject(
            filename="info.txt",
            raw_bytes=b"AEGIS-DocIntel is a state-of-the-art system designed for document analysis.",
            format=DocumentFormat.TEXT
        )
        stats = await orchestrator.ingest(doc)
        doc_id = stats["doc_id"]
        
        # Test query
        res = await orchestrator.query("What is AEGIS-DocIntel?", doc_id=doc_id)
        
        assert res is not None
        assert "answer" in res
        assert len(res["answer"]) > 0
        assert "confidence" in res
        assert 0.0 <= res["confidence"] <= 1.0
        assert "query_type" in res
        assert "weights_used" in res
        
        # Verify weights sum to 1.0
        weights = res["weights_used"]
        assert len(weights) > 0
        assert pytest.approx(sum(weights.values()), abs=1e-3) == 1.0
        
        assert "grounded" in res
        assert res["grounded"] is True
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_close_no_error():
    orchestrator = AMDIOrchestrator()
    await orchestrator.close()
    # Second close should be a safe no-op
    await orchestrator.close()
