"""
AEGIS-DocIntel / AMDI-OS — LangChain & LlamaIndex Retriever Adapters
====================================================================
Exposes AMDIOrchestrator / AMDIRetriever as a standard LangChain Retriever
and LlamaIndex Retriever adapter.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.core.orchestrator import AMDIOrchestrator
from src.core.document_object import DocumentObject, DocumentFormat


class AMDIRetrieverAdapter:
    """
    Standard LangChain / LlamaIndex compatible retriever adapter for AEGIS-DocIntel.
    Allows seamless integration into LCEL pipelines (e.g. `retriever | prompt | llm`).
    """

    def __init__(
        self,
        orchestrator: Optional[AMDIOrchestrator] = None,
        tenant_id: str = "default",
        top_k: int = 10,
    ) -> None:
        self.orchestrator = orchestrator or AMDIOrchestrator()
        self.tenant_id = tenant_id
        self.top_k = top_k

    async def aget_relevant_documents(
        self,
        query: str,
        doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously retrieves relevant document chunks matching query.
        Returns a list of dicts formatted as LangChain Document objects:
        {'page_content': text, 'metadata': {...}}
        """
        res = await self.orchestrator.query(
            query,
            doc_id=doc_id,
            tenant_id=self.tenant_id,
        )

        documents = []
        if isinstance(res, dict):
            answer = res.get("answer", "")
            documents.append({
                "page_content": answer,
                "metadata": {
                    "tenant_id": self.tenant_id,
                    "doc_id": doc_id,
                    "query": query,
                    "fused_scores": res.get("fused_scores", {}),
                }
            })
        return documents

    def get_relevant_documents(
        self,
        query: str,
        doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for aget_relevant_documents."""
        import asyncio
        return asyncio.run(self.aget_relevant_documents(query, doc_id=doc_id))
