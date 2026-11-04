"""
aegis.security.deletion.lifecycle
=================================
Complete Document Deletion Orchestrator & Tombstone Lifecycle Manager:
- Cascading deletion across Database, Object Storage, Derived Content,
  Vector Index, Search Index, Semantic Cache, and In-Flight Jobs.
- Durable deletion manifests tracking target verification.
- Post-restore tombstone reconciliation preventing data resurrection.
- Idempotent deletion retries.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Set, Tuple


class DeletionManifest:
    def __init__(self, deletion_id: str, document_id: str, tenant_id: str) -> None:
        self.deletion_id = deletion_id
        self.document_id = document_id
        self.tenant_id = tenant_id
        self.requested_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.status = "PENDING"
        self.targets = [
            "database_metadata",
            "object_storage",
            "extracted_text",
            "search_index",
            "vector_index",
            "semantic_cache",
            "job_queue",
        ]
        self.verification: Dict[str, bool] = {t: False for t in self.targets}


class DocumentDeletionOrchestrator:
    """Orchestrates multi-target deletion, verification, and tombstone reconciliation."""

    def __init__(self) -> None:
        # Multi-target storage simulation
        self.database: Dict[str, Dict[str, Any]] = {}
        self.object_storage: Dict[str, bytes] = {}
        self.extracted_text: Dict[str, str] = {}
        self.search_index: Dict[str, List[str]] = {}  # doc_id -> tokens
        self.vector_index: Dict[str, List[float]] = {}  # doc_id -> embedding
        self.semantic_cache: Dict[str, Dict[str, Any]] = {}  # doc_id -> cache_entry
        self.job_queue: Dict[str, Dict[str, Any]] = {}  # job_id -> job_record
        self.reports: Dict[str, Dict[str, Any]] = {}  # report_id -> report_record

        # Tombstone registry
        self.tombstones: Dict[str, Dict[str, Any]] = {}  # doc_id -> tombstone_record
        self.deletion_manifests: Dict[str, DeletionManifest] = {}

        # Simulators for failure injection
        self.target_outages: Set[str] = set()

    def register_document(
        self,
        doc_id: str,
        tenant_id: str,
        content: str,
        raw_bytes: bytes = b"%PDF-1.4 dummy",
        job_id: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> None:
        """Sets up document presence across all storage subsystems."""
        self.database[doc_id] = {
            "doc_id": doc_id,
            "tenant_id": tenant_id,
            "status": "ready",
            "title": f"Document {doc_id}",
        }
        self.object_storage[f"storage/{tenant_id}/{doc_id}.pdf"] = raw_bytes
        self.extracted_text[doc_id] = content
        self.search_index[doc_id] = content.lower().split()
        self.vector_index[doc_id] = [0.1, 0.2, 0.3]
        self.semantic_cache[doc_id] = {"query": "summary", "answer": content[:30]}

        if job_id:
            self.job_queue[job_id] = {
                "job_id": job_id,
                "doc_id": doc_id,
                "tenant_id": tenant_id,
                "status": "RUNNING",
            }
        if report_id:
            self.reports[report_id] = {
                "report_id": report_id,
                "doc_id": doc_id,
                "tenant_id": tenant_id,
                "status": "VALID",
            }

    def delete_document(
        self,
        caller_tenant_id: str,
        doc_id: str,
        caller_roles: Set[str],
    ) -> Tuple[bool, int, str]:
        """
        Executes complete cascading deletion.
        Returns (success, status_code, message).
        """
        # 1. Check authorization
        if not any(r in caller_roles for r in ("tenant_admin", "editor", "admin")):
            return False, 403, "Insufficient permissions to delete document"

        # 2. Check tenant scoping (Anti-IDOR)
        doc = self.database.get(doc_id)
        if not doc or doc.get("tenant_id") != caller_tenant_id:
            return False, 404, "Document not found"

        manifest_id = f"del-{doc_id}-{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
        manifest = DeletionManifest(manifest_id, doc_id, caller_tenant_id)
        self.deletion_manifests[manifest_id] = manifest

        # 3. Block access immediately
        manifest.status = "ACCESS_BLOCKED"
        doc["status"] = "DELETE_REQUESTED"

        # 4. Invalidate associated jobs in queue
        for j_id, job in list(self.job_queue.items()):
            if job.get("doc_id") == doc_id:
                job["status"] = "CANCELLED"
        manifest.verification["job_queue"] = True

        # 5. Invalidate dependent reports
        for r_id, rep in list(self.reports.items()):
            if rep.get("doc_id") == doc_id:
                rep["status"] = "INVALID_SOURCE_DELETED"

        # 6. Check target outages (Simulated storage failures)
        if "object_storage" in self.target_outages:
            manifest.status = "PENDING_FAILED_TARGET"
            return False, 500, "Deletion incomplete: Object storage target unavailable"

        # 7. Cascade removal across all storage subsystems
        # Target: object_storage
        self.object_storage.pop(f"storage/{caller_tenant_id}/{doc_id}.pdf", None)
        manifest.verification["object_storage"] = True

        # Target: extracted_text
        self.extracted_text.pop(doc_id, None)
        manifest.verification["extracted_text"] = True

        # Target: search_index
        self.search_index.pop(doc_id, None)
        manifest.verification["search_index"] = True

        # Target: vector_index
        self.vector_index.pop(doc_id, None)
        manifest.verification["vector_index"] = True

        # Target: semantic_cache
        self.semantic_cache.pop(doc_id, None)
        manifest.verification["semantic_cache"] = True

        # Target: database_metadata
        self.database.pop(doc_id, None)
        manifest.verification["database_metadata"] = True

        # 8. Record durable tombstone
        self.tombstones[doc_id] = {
            "doc_id": doc_id,
            "tenant_id": caller_tenant_id,
            "deleted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "deletion_id": manifest_id,
        }

        # 9. Verify all targets
        all_cleared = all(manifest.verification.values())
        if all_cleared:
            manifest.status = "DELETED"
            return True, 200, "Document and all associated derivatives successfully deleted"
        else:
            manifest.status = "PARTIALLY_DELETED"
            return False, 500, "Verification failed on one or more storage targets"

    def reconcile_after_restore(self, restored_database: Dict[str, Dict[str, Any]]) -> int:
        """
        Reconciles restored database against active tombstones.
        Purges any resurrected documents matching tombstones.
        """
        resurrected_count = 0
        for doc_id in list(restored_database.keys()):
            if doc_id in self.tombstones:
                restored_database.pop(doc_id, None)
                self.extracted_text.pop(doc_id, None)
                self.vector_index.pop(doc_id, None)
                self.search_index.pop(doc_id, None)
                resurrected_count += 1
        return resurrected_count
