"""
aegis.security.tenant.isolation_guard
====================================
Multi-Tenant Isolation Validation Engine:
- In-memory multi-tenant store simulating Document metadata, raw files,
  vector search, semantic cache, background jobs, reports, citations, and audit events.
- Validates that cross-tenant access produces controlled 404 / 403 or empty search results.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


class TenantIsolationStore:
    """Multi-tenant simulation store managing isolated tenant partitions."""

    def __init__(self) -> None:
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.files: Dict[str, bytes] = {}  # storage_path -> bytes
        self.vector_records: List[Dict[str, Any]] = []
        self.cache_entries: Dict[str, Dict[str, Any]] = {}  # tenant_id -> {key -> val}
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.reports: Dict[str, Dict[str, Any]] = {}
        self.audit_events: List[Dict[str, Any]] = []

    def populate_synthetic_fixtures(self) -> None:
        """Populates synthetic Tenant Alpha and Tenant Beta fixtures."""
        # Tenant Alpha
        self.documents["doc-a1"] = {
            "doc_id": "doc-a1",
            "tenant_id": "tenant_alpha",
            "title": "Alpha Q1 Strategy",
            "content": "Secret Roadmap. Marker: TENANT_ALPHA_SECRET_MARKER_7319",
            "owner_id": "user-a1",
        }
        self.files["storage/tenant_alpha/doc-a1.pdf"] = b"%PDF-1.4 Alpha Secret Bytes 7319"
        self.vector_records.append({
            "vector_id": "vec-a1",
            "tenant_id": "tenant_alpha",
            "doc_id": "doc-a1",
            "embedding": [0.1, 0.9, -0.2],
            "text": "Secret Alpha Strategic Plan TENANT_ALPHA_SECRET_MARKER_7319",
        })
        self.cache_entries.setdefault("tenant_alpha", {})["query:strategy"] = {
            "answer": "Alpha Strategy Overview",
            "marker": "TENANT_ALPHA_SECRET_MARKER_7319",
        }
        self.jobs["job-a1"] = {
            "job_id": "job-a1",
            "tenant_id": "tenant_alpha",
            "doc_id": "doc-a1",
            "status": "COMPLETED",
        }
        self.reports["rep-a1"] = {
            "report_id": "rep-a1",
            "tenant_id": "tenant_alpha",
            "title": "Alpha Performance Report",
            "summary": "Alpha summary 7319",
        }
        self.audit_events.append({
            "event_id": "ev-a1",
            "tenant_id": "tenant_alpha",
            "action": "doc.ingest",
            "resource_id": "doc-a1",
        })

        # Tenant Beta
        self.documents["doc-b1"] = {
            "doc_id": "doc-b1",
            "tenant_id": "tenant_beta",
            "title": "Beta Financial Statement",
            "content": "Beta Earnings. Marker: TENANT_BETA_SECRET_MARKER_8426",
            "owner_id": "user-b1",
        }
        self.files["storage/tenant_beta/doc-b1.pdf"] = b"%PDF-1.4 Beta Secret Bytes 8426"
        self.vector_records.append({
            "vector_id": "vec-b1",
            "tenant_id": "tenant_beta",
            "doc_id": "doc-b1",
            "embedding": [0.8, -0.1, 0.5],
            "text": "Secret Beta Financial Earnings TENANT_BETA_SECRET_MARKER_8426",
        })
        self.cache_entries.setdefault("tenant_beta", {})["query:earnings"] = {
            "answer": "Beta Earnings Overview",
            "marker": "TENANT_BETA_SECRET_MARKER_8426",
        }
        self.jobs["job-b1"] = {
            "job_id": "job-b1",
            "tenant_id": "tenant_beta",
            "doc_id": "doc-b1",
            "status": "COMPLETED",
        }
        self.reports["rep-b1"] = {
            "report_id": "rep-b1",
            "tenant_id": "tenant_beta",
            "title": "Beta Audit Report",
            "summary": "Beta summary 8426",
        }
        self.audit_events.append({
            "event_id": "ev-b1",
            "tenant_id": "tenant_beta",
            "action": "doc.ingest",
            "resource_id": "doc-b1",
        })

    def get_document(self, tenant_id: str, doc_id: str) -> Tuple[Optional[Dict[str, Any]], int, str]:
        doc = self.documents.get(doc_id)
        if not doc or doc.get("tenant_id") != tenant_id:
            # Anti-IDOR: Return 404 rather than disclosing document existence
            return None, 404, "Document not found"
        return doc, 200, "Found"

    def download_file(self, tenant_id: str, doc_id: str) -> Tuple[Optional[bytes], int, str]:
        doc, code, reason = self.get_document(tenant_id, doc_id)
        if not doc:
            return None, code, reason
        path = f"storage/{tenant_id}/{doc_id}.pdf"
        data = self.files.get(path)
        if not data:
            return None, 404, "File not found"
        return data, 200, "Success"

    def search_documents(self, tenant_id: str, query: str) -> List[Dict[str, Any]]:
        results = []
        for doc in self.documents.values():
            if doc.get("tenant_id") == tenant_id and query.lower() in doc.get("content", "").lower():
                results.append(doc)
        return results

    def vector_search(self, tenant_id: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        # Pre-filter by tenant_id
        tenant_vectors = [v for v in self.vector_records if v.get("tenant_id") == tenant_id]
        # In a real engine, cosine calculation; here return top_k of filtered set
        return tenant_vectors[:top_k]

    def get_cache_response(self, tenant_id: str, cache_key: str) -> Optional[Dict[str, Any]]:
        return self.cache_entries.get(tenant_id, {}).get(cache_key)

    def get_report(self, tenant_id: str, report_id: str) -> Tuple[Optional[Dict[str, Any]], int, str]:
        rep = self.reports.get(report_id)
        if not rep or rep.get("tenant_id") != tenant_id:
            return None, 404, "Report not found"
        return rep, 200, "Found"

    def delete_document(self, tenant_id: str, doc_id: str) -> Tuple[bool, int, str]:
        doc, code, reason = self.get_document(tenant_id, doc_id)
        if not doc:
            return False, code, reason
        self.documents.pop(doc_id, None)
        self.files.pop(f"storage/{tenant_id}/{doc_id}.pdf", None)
        self.vector_records = [v for v in self.vector_records if v.get("doc_id") != doc_id]
        return True, 200, "Deleted"

    def get_job(self, tenant_id: str, job_id: str) -> Tuple[Optional[Dict[str, Any]], int, str]:
        job = self.jobs.get(job_id)
        if not job or job.get("tenant_id") != tenant_id:
            return None, 404, "Job not found"
        return job, 200, "Found"

    def get_audit_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.audit_events if e.get("tenant_id") == tenant_id]

    def resolve_citation(self, tenant_id: str, doc_id: str) -> Tuple[bool, str]:
        doc, code, _ = self.get_document(tenant_id, doc_id)
        if not doc:
            return False, "Citation target document not found in tenant scope"
        return True, "Citation verified"

    def execute_worker_job(self, worker_tenant_context: str, job_id: str) -> Tuple[bool, str]:
        job = self.jobs.get(job_id)
        if not job:
            return False, "Job not found"
        if job.get("tenant_id") != worker_tenant_context:
            return False, "Security violation: Worker tenant context does not match job tenant scope"
        return True, "Job processed"
