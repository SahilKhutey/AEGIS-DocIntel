"""
src/engines/intelligence/service.py
===================================
Document intelligence coordinator orchestrating fact extraction, normalization,
provenance persistence, cross-document comparison, and conflict detection.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from src.engines.intelligence.comparison import (
    CrossTenantComparisonError,
    DocumentComparator,
)
from src.engines.intelligence.conflict_detection import ConflictDetector
from src.engines.intelligence.contracts import (
    ConflictReport,
    DocumentComparisonResult,
    ExtractedFact,
    ExtractionResult,
    ExtractionSchema,
)
from src.engines.intelligence.entity_resolution import EntityResolver
from src.engines.intelligence.fact_extractor import FactExtractor
from src.engines.intelligence.fact_store import FactStore

log = logging.getLogger("aegis.intelligence.service")


class DocumentIntelligenceService:
    """
    Unified intelligence coordinator providing extraction, entity resolution,
    fact persistence, cross-document comparison, and conflict detection.
    """

    def __init__(
        self,
        fact_store: Optional[FactStore] = None,
        extractor: Optional[FactExtractor] = None,
        resolver: Optional[EntityResolver] = None,
        comparator: Optional[DocumentComparator] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ) -> None:
        self.store = fact_store or FactStore()
        self.resolver = resolver or EntityResolver()
        self.extractor = extractor or FactExtractor()
        self.comparator = comparator or DocumentComparator(resolver=self.resolver)
        self.conflict_detector = conflict_detector or ConflictDetector(resolver=self.resolver)

    def extract_and_persist(
        self,
        tenant_id: str,
        document_id: str,
        passages: Sequence[Dict[str, Any]],
        schema_name: str = "contract_terms",
        custom_schema: Optional[ExtractionSchema] = None,
        subject: Optional[str] = None,
        document_version: int = 1,
    ) -> ExtractionResult:
        """
        Extract structured facts from document passages and atomically persist them.
        """
        result = self.extractor.extract_document_facts(
            tenant_id=tenant_id,
            document_id=document_id,
            passages=passages,
            schema_name=schema_name,
            custom_schema=custom_schema,
            subject=subject,
        )

        if result.facts:
            effective_schema_name = (
                custom_schema.schema_name if custom_schema else schema_name
            )
            effective_schema_version = (
                custom_schema.schema_version if custom_schema else 1
            )
            self.store.store_extraction_run(
                tenant_id=tenant_id,
                document_id=document_id,
                schema_name=effective_schema_name,
                facts=result.facts,
                document_version=document_version,
                schema_version=effective_schema_version,
                status=result.status,
            )

        return result

    def extract_from_orchestrator(
        self,
        tenant_id: str,
        document_id: str,
        orchestrator: Any,
        schema_name: str = "contract_terms",
        custom_schema: Optional[ExtractionSchema] = None,
        subject: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Gather passages from AMDIOrchestrator and extract facts.
        """
        passages: List[Dict[str, Any]] = []

        if orchestrator is not None:
            # 1. Check orchestrator elements
            elements = []
            if hasattr(orchestrator, "get_document_elements"):
                try:
                    elements = orchestrator.get_document_elements(document_id, tenant_id=tenant_id)
                except TypeError:
                    elements = orchestrator.get_document_elements(document_id)

            for el in elements:
                content = getattr(el, "content", "")
                el_id = getattr(el, "element_id", f"el-{len(passages)}")
                page = getattr(el, "page", None)
                if content:
                    passages.append({"chunk_id": el_id, "text": content, "page_number": page})

            # 2. Check context builder chunks if no elements found
            if not passages and hasattr(orchestrator, "context_builder"):
                builder = orchestrator.context_builder
                if hasattr(builder, "get_chunks"):
                    chunks = builder.get_chunks(document_id)
                    for c in chunks:
                        passages.append({
                            "chunk_id": getattr(c, "chunk_id", f"chk-{len(passages)}"),
                            "text": getattr(c, "content", getattr(c, "text", "")),
                            "page_number": getattr(c, "page_number", None),
                        })

        if not passages:
            # Empty fallback if document has no elements
            return ExtractionResult(
                status="failed",
                document_id=document_id,
                tenant_id=tenant_id,
                errors=(f"No textual passages found for document {document_id}",),
                schema_name=schema_name,
            )

        return self.extract_and_persist(
            tenant_id=tenant_id,
            document_id=document_id,
            passages=passages,
            schema_name=schema_name,
            custom_schema=custom_schema,
            subject=subject,
        )

    def get_document_facts(
        self,
        tenant_id: str,
        document_id: str,
        attribute: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """Retrieve persisted facts for a document."""
        return self.store.get_facts_by_document(
            tenant_id=tenant_id,
            document_id=document_id,
            attribute=attribute,
        )

    def compare_documents(
        self,
        tenant_id: str,
        left_doc_id: str,
        right_doc_id: str,
        attributes: Optional[List[str]] = None,
    ) -> DocumentComparisonResult:
        """
        Compare persisted facts between two documents for the specified tenant.
        """
        left_facts = self.store.get_facts_by_document(tenant_id=tenant_id, document_id=left_doc_id)
        right_facts = self.store.get_facts_by_document(tenant_id=tenant_id, document_id=right_doc_id)

        return self.comparator.compare_facts(
            tenant_id=tenant_id,
            left_doc_id=left_doc_id,
            left_facts=left_facts,
            right_doc_id=right_doc_id,
            right_facts=right_facts,
            target_attributes=attributes,
        )

    def detect_conflicts(
        self,
        tenant_id: str,
        document_ids: Optional[Sequence[str]] = None,
        subject: Optional[str] = None,
    ) -> List[ConflictReport]:
        """
        Inspect documents for contradictory facts within the specified tenant.
        """
        if document_ids:
            facts = self.store.get_facts_for_documents(tenant_id=tenant_id, document_ids=document_ids)
        elif subject:
            facts = self.store.get_facts_by_subject(tenant_id=tenant_id, subject=subject)
        else:
            # Query all facts for tenant
            conn = self.store._get_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM extracted_facts WHERE tenant_id = ? ORDER BY created_at ASC",
                    (tenant_id,),
                ).fetchall()
                facts = [self.store._row_to_fact(r) for r in rows]
            finally:
                if self.store.db_path != ":memory:":
                    conn.close()

        return self.conflict_detector.detect_conflicts(
            tenant_id=tenant_id,
            facts=facts,
            target_subject=subject,
        )
