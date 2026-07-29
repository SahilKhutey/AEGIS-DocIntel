"""
Unit tests for LlamaIndex Framework Adapter (Task H-2).
"""

import pytest
from src.core.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator
from src.connectors.llamaindex_adapter import AegisLlamaIndexReader, AegisLlamaIndexRetriever


@pytest.mark.asyncio
async def test_llamaindex_reader():
    orchestrator = AMDIOrchestrator()
    try:
        reader = AegisLlamaIndexReader(orchestrator=orchestrator)
        doc = DocumentObject(
            filename="monograph_section.txt",
            raw_bytes=b"AEGIS-DocIntel LlamaIndex Integration Test Document.\nSection 1 details.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-llamaindex",
        )

        nodes = await reader.aload_data(doc, tenant_id="tenant-llamaindex")
        assert len(nodes) > 0
        assert "text" in nodes[0]
        assert nodes[0]["extra_info"]["tenant_id"] == "tenant-llamaindex"
    finally:
        await orchestrator.close()


@pytest.mark.asyncio
async def test_llamaindex_retriever():
    orchestrator = AMDIOrchestrator()
    try:
        doc = DocumentObject(
            filename="query_doc.txt",
            raw_bytes=b"The quick brown fox jumps over the lazy dog.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-retriever",
        )
        stats = await orchestrator.ingest(doc)
        doc_id = stats["doc_id"]

        retriever = AegisLlamaIndexRetriever(orchestrator=orchestrator, tenant_id="tenant-retriever")
        nodes = await retriever.aretrieve("What did the fox jump over?", doc_id=doc_id)

        assert len(nodes) > 0
        assert "node" in nodes[0]
        assert "score" in nodes[0]
        assert nodes[0]["score"] == 1.0
    finally:
        await orchestrator.close()
