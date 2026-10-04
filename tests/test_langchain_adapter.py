"""
Tests for AMDIRetrieverAdapter in src.connectors.langchain_adapter.
"""

from __future__ import annotations

import pytest
from src.connectors.langchain_adapter import AMDIRetrieverAdapter
from src.core.orchestrator import AMDIOrchestrator
from src.models.document_object import DocumentObject, DocumentFormat


@pytest.mark.asyncio
async def test_langchain_retriever_adapter_aget_relevant_documents():
    orchestrator = AMDIOrchestrator()
    try:
        doc = DocumentObject(
            filename="test_langchain.txt",
            raw_bytes=b"LangChain adapter test content for AEGIS DocIntel.",
            format=DocumentFormat.TEXT,
            tenant_id="tenant-lc",
        )
        stats = await orchestrator.ingest(doc)
        doc_id = stats["doc_id"]

        adapter = AMDIRetrieverAdapter(
            orchestrator=orchestrator,
            tenant_id="tenant-lc",
            top_k=5,
        )

        docs = await adapter.aget_relevant_documents(
            "What is this test about?",
            doc_id=doc_id,
        )

        assert len(docs) > 0
        assert "page_content" in docs[0]
        assert docs[0]["metadata"]["tenant_id"] == "tenant-lc"
    finally:
        await orchestrator.close()
