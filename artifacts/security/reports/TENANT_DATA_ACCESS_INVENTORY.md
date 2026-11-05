# AEGIS-DocIntel — Tenant Data Access Inventory

> **Document ID**: `TENANT_DATA_ACCESS_INVENTORY.md`  
> **Work Item**: WP-07.02  
> **Status**: **VERIFIED**  

---

## 1. Resource Isolation Inventory

| Resource Type | Isolation Requirement | Storage Mechanism | Enforcement Gate |
| :--- | :--- | :--- | :--- |
| **Users & Memberships** | Tenant-scoped | Relational DB | Enforced by `tenant_id` foreign key. |
| **Documents (Metadata)** | Tenant-scoped | SQLite `documents` table | Mandatory `WHERE tenant_id = :authenticated_tenant_id`. |
| **Raw Binary Files** | Tenant-scoped | Object/File Storage | File path partitioned by tenant (`storage/{tenant_id}/{doc_id}`). |
| **Extracted Text / Layout** | Tenant-scoped | Derived Storage | Associated with document metadata scoped to tenant. |
| **Document Chunks** | Tenant-scoped | Document Service | Chunks retain parent `doc_id` and `tenant_id`. |
| **Vector Embeddings** | Partitioned / Pre-filtered | FAISS / Vector Index | Metadata filtering by `tenant_id` prior to nearest-neighbor return. |
| **Lexical Search Indexes** | Partitioned | BM25 Inverted Index | Corpus index filtered by `tenant_id` filter list. |
| **Semantic Cache** | Partitioned | Memory / Redis Cache | Cache key namespaced: `cache:{tenant_id}:{query_hash}`. |
| **Analysis Jobs** | Tenant-scoped | Job Repository | `JobRecord.tenant_id` validated on queue pull and worker execution. |
| **Generated Reports** | Tenant-scoped | Report Store | Report metadata contains `tenant_id`; pre-render scope checked. |
| **Citations & Provenance** | Tenant-scoped | Provenance Store | Citations resolving across tenant boundaries are rejected. |
| **Audit Events** | Tenant-scoped | Audit Log Store | Logs queried with strict `tenant_id` filter; zero cross-tenant leak. |
