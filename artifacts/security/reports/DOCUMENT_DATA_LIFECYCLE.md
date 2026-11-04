# AEGIS-DocIntel — Document Data Lifecycle & Cascading Deletion Specification

> **Document ID**: `DOCUMENT_DATA_LIFECYCLE.md`  
> **Work Item**: WP-07.04  
> **Status**: **ACTIVE & ENFORCED**  

---

## 1. Lifecycle State Machine

```
ACTIVE
  ↓
DELETE_REQUESTED
  ↓
ACCESS_BLOCKED (Immediate 404 to all callers)
  ↓
DERIVATIVES_REMOVED (Extracted OCR, page layouts, tables)
  ↓
INDEXES_AND_CACHES_CLEARED (FAISS vectors, BM25 inverted index, semantic cache)
  ↓
STORAGE_REMOVED (Raw binary PDF files in object storage)
  ↓
VERIFICATION (Probe all targets; must verify zero residual data)
  ↓
DELETED (Durable tombstone recorded)
```

---

## 2. Storage Targets & Deletion Actions

| Target ID | Storage Subsystem | Stored Artifacts | Deletion Mechanism | Verification Probe |
| :--- | :--- | :--- | :--- | :--- |
| `TARGET-DB` | SQLite Relational DB | Document metadata, status, metrics | Record purged / tombstone logged | Query returns `None` |
| `TARGET-OBJ` | Object / File Storage | Raw input PDF binaries | File unlinked (`unlink()`) | File exists probe returns `False` |
| `TARGET-DER` | Derived Processing Store | OCR text, JSON layouts, table HTML | Derived folder purged | Read probe returns `None` |
| `TARGET-VEC` | Vector Store (FAISS) | Embedding vectors & chunk metadata | `vstore.delete(doc_id)` | Vector search returns 0 vectors |
| `TARGET-LEX` | Lexical Search Index | Inverted BM25 tokens | Inverted postings removed | Keyword query returns 0 hits |
| `TARGET-CCH` | Semantic Cache | Query response caches | `cache.invalidate_doc(doc_id)` | Cache lookup returns `None` |
| `TARGET-QUE` | Job Queue | In-flight or pending jobs | Job status -> `CANCELLED` | Worker aborts execution |

---

## 3. Tombstone Policy & Post-Restore Reconciliation

When an older database backup is restored, records that were deleted prior to the incident must not silently resurrect.
- **Tombstone Registry**: High-durability append-only record tracking `doc_id`, `tenant_id`, `deleted_at`, `sha256_hash`.
- **Post-Restore Reconciliation**: Upon system startup following database restoration, the tombstone reconciler runs across the restored database, immediately removing any resurrected records matching active tombstones.
