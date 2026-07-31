"""
AEGIS-DocIntel / AMDI-OS — LlamaIndex Framework Adapter (Task H-2).

Exposes AMDIOrchestrator and AEGIS document pipeline as standard LlamaIndex-compatible
Document Readers and Retrievers.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from src.core.orchestrator import AMDIOrchestrator
from src.core.document_object import DocumentObject, DocumentFormat


class AegisLlamaIndexReader:
    """
    LlamaIndex-compatible document loader for AEGIS-DocIntel documents.
    """

    def __init__(self, orchestrator: Optional[AMDIOrchestrator] = None):
        self.orchestrator = orchestrator or AMDIOrchestrator()

    async def aload_data(
        self,
        doc: DocumentObject,
        tenant_id: str = "default",
    ) -> List[Dict[str, Any]]:
        """
        Ingests document into orchestrator and returns LlamaIndex document representations.
        """
        stats = await self.orchestrator.ingest(doc)
        doc_id = stats.get("doc_id", doc.doc_id)
        elements = self.orchestrator.get_document_elements(doc_id, tenant_id=tenant_id)

        llama_docs = []
        for e in elements:
            llama_docs.append({
                "doc_id": getattr(e, "element_id", f"{doc_id}_elem"),
                "text": getattr(e, "content", ""),
                "extra_info": {
                    "doc_id": doc_id,
                    "tenant_id": tenant_id,
                    "page": getattr(e, "page", 1),
                    "type": getattr(getattr(e, "type", None), "value", "text"),
                }
            })
        return llama_docs


class AegisLlamaIndexRetriever:
    """
    LlamaIndex-compatible retriever adapter for AEGIS-DocIntel.
    """

    def __init__(
        self,
        orchestrator: Optional[AMDIOrchestrator] = None,
        tenant_id: str = "default",
        top_k: int = 10,
    ):
        self.orchestrator = orchestrator or AMDIOrchestrator()
        self.tenant_id = tenant_id
        self.top_k = top_k

    async def aretrieve(
        self,
        query: str,
        doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously retrieves matching node results for LlamaIndex query engine.
        Returns node-with-score dictionary representations.
        """
        res = await self.orchestrator.query(
            query,
            doc_id=doc_id,
            tenant_id=self.tenant_id,
            top_k=self.top_k,
        )

        nodes = []
        if isinstance(res, dict):
            answer = res.get("answer", "")
            nodes.append({
                "node": {
                    "id_": f"node_{doc_id or 'global'}",
                    "text": answer,
                    "metadata": {
                        "tenant_id": self.tenant_id,
                        "doc_id": doc_id,
                        "citations": res.get("citations", []),
                    },
                },
                "score": 1.0,
            })
        return nodes

    def retrieve(
        self,
        query: str,
        doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for aretrieve."""
        return asyncio.run(self.aretrieve(query, doc_id=doc_id))
