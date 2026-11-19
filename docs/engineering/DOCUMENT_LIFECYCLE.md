# AEGIS-DocIntel Document Lifecycle Specification

**Document Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-10 (Section 3.2)  
**Status:** Canonical Engineering Specification  
**Classification:** Internal Core Architecture  

---

## 1. Executive Summary

This specification establishes the single, authoritative document lifecycle state model for AEGIS-DocIntel. To eliminate race conditions, unobservable failure modes, and inconsistent status reporting across microservices, this state machine is strictly enforced across backend APIs, storage drivers, background workers, and frontend user interfaces.

---

## 2. Canonical State Machine Graph

The document lifecycle progresses through deterministic phases: ingestion, validation, queuing, extraction, structural parsing, normalization, indexing, and serving, followed by archival or cryptographically verified cascading erasure.

```
                  +--------------+
                  |   UPLOADED   |
                  +-------+------+
                          |
                          v
                  +-------+------+
                  |  VALIDATING  |--------> REJECTED (Terminal)
                  +-------+------+
                          |
                          v
                  +-------+------+
                  |   ACCEPTED   |
                  +-------+------+
                          |
                          v
                  +-------+------+
                  |    QUEUED    | <------------------------------------+
                  +-------+------+                                      |
                          |                                             |
                          v                                             |
                  +-------+------+                                      |
                  |  EXTRACTING  |--------> EXTRACTION_FAILED (Retry) --+
                  +-------+------+                                      |
                          |                                             |
                          v                                             |
                  +-------+------+                                      |
                  |   PARSING    |--------> PARSING_FAILED (Retry) -----+
                  +-------+------+                                      |
                          |                                             |
                          v                                             |
                  +-------+------+                                      |
                  | NORMALIZING  |                                      |
                  +-------+------+                                      |
                          |                                             |
                          v                                             |
                  +-------+------+                                      |
                  |   INDEXING   |--------> INDEXING_FAILED (Retry) ----+
                  +-------+------+
                          |
                          v
                  +-------+------+
                  |    READY     | <----------+
                  +---+-------+--+            |
                      |       |               |
                      |       +----> ARCHIVED +
                      v
             DELETION_PENDING
                      |
                      v
               DELETED (Terminal)
```

---

## 3. State Definitions and Semantics

| State | Category | Description | Permitted Next States |
| :--- | :--- | :--- | :--- |
| `UPLOADED` | Ingestion | Raw bytes received and registered in temporary staging buffer. | `VALIDATING`, `DELETION_PENDING` |
| `VALIDATING` | Intake Gate | Magic bytes, SHA-256 integrity, mime-types, and size limits verified. | `ACCEPTED`, `REJECTED`, `DELETION_PENDING` |
| `REJECTED` | Terminal Error | File failed intake criteria (corrupt, encrypted, malware signature, exceeds quota). | *None* (Terminal) |
| `ACCEPTED` | Ingestion | File metadata registered, durable record created, ready for scheduling. | `QUEUED`, `DELETION_PENDING` |
| `QUEUED` | Orchestration | Processing job placed on durable FIFO tenant-isolated queue. | `EXTRACTING`, `DELETION_PENDING` |
| `EXTRACTING` | Core Pipeline | Raw text and layout geometry being extracted via PyMuPDF or OCR. | `PARSING`, `EXTRACTION_FAILED`, `DELETION_PENDING` |
| `EXTRACTION_FAILED`| Recoverable Error | Extraction worker failed; eligible for exponential backoff retry. | `QUEUED`, `DELETION_PENDING` |
| `PARSING` | Core Pipeline | Recovering hierarchical sections, headings, table cells, and Kahn DAG order. | `NORMALIZING`, `PARSING_FAILED`, `DELETION_PENDING` |
| `PARSING_FAILED` | Recoverable Error | Parser crash or schema validation error; eligible for retry. | `QUEUED`, `DELETION_PENDING` |
| `NORMALIZING` | Core Pipeline | Cleaning text, normalizing quantities, standardizing Unicode, generating chunks. | `INDEXING`, `INDEXING_FAILED`, `DELETION_PENDING` |
| `INDEXING` | Core Pipeline | Computing dense embeddings, generating BM25 tokens, building vector graph. | `READY`, `INDEXING_FAILED`, `DELETION_PENDING` |
| `INDEXING_FAILED` | Recoverable Error | Vector indexer write failure or memory exhaustion; eligible for retry. | `QUEUED`, `DELETION_PENDING` |
| `READY` | Serving | Fully indexed, grounded evidence available, queryable by intelligence engine. | `ARCHIVED`, `DELETION_PENDING`, `QUEUED` (Reindex) |
| `ARCHIVED` | Storage | Cold-tier storage; excluded from active query retrieval. | `READY`, `DELETION_PENDING` |
| `DELETION_PENDING` | Decommission | Marked for cascading erasure across vector db, SQLite, cache, and disk. | `DELETED` |
| `DELETED` | Terminal State | Cryptographic overwrite verified, all records and vectors purged. | *None* (Terminal) |

---

## 4. Transition Audit Ledger Requirements

Every state change must atomically append an immutable record to the lifecycle audit ledger (`LifecycleTransitionRecord`):

```json
{
  "document_id": "doc_9c2a1e...",
  "tenant_id": "tenant_enterprise_01",
  "previous_state": "INDEXING",
  "new_state": "READY",
  "job_id": "job_7f8a12...",
  "stage": "vector_indexing",
  "timestamp": "2026-11-19T10:30:00.000Z",
  "duration_ms": 342.5,
  "attempt_number": 1,
  "sanitized_error_code": null,
  "diagnostic_ref": null,
  "pipeline_version": "1.1.0",
  "artifact_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### Security & Privacy Log Guarantees
1. **Zero Content Storage:** Raw document text, extracted paragraphs, and prompt payloads MUST NEVER be recorded in operational logs.
2. **Zero Credential Exposure:** API keys, authorization bearer tokens, and encryption secrets MUST be stripped before ledger serialization.
3. **Diagnostic References Only:** Error details must be referenced via opaque diagnostic identifiers (`diagnostic_ref`), never raw internal stack traces.
