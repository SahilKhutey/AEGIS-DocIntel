# AEGIS-DocIntel — Retention & Deletion Tombstone Policy

> **Document ID**: `RETENTION_AND_TOMBSTONE_POLICY.md`  
> **Work Item**: WP-07.04  
> **Status**: **ACTIVE & ENFORCED**  

---

## 1. Tombstone Architecture

1. **Durable Tombstone Schema**:
   - `doc_id`: Unique identifier of the deleted document.
   - `tenant_id`: Scope of ownership.
   - `deleted_at`: UTC timestamp of verified deletion.
   - `deletion_manifest_id`: Correlation identifier for the deletion operation.
   - `sha256_hash`: Content hash to verify identity.
2. **Tombstone Retention Window**:
   - Tombstones are retained for a minimum of **90 days** (or the longest backup retention cycle plus 30 days buffer).
   - After the backup retention horizon has expired (all backups containing the pre-deletion document have aged out), tombstones may be safely archived.

---

## 2. Post-Restore Reconciliation Invariants

- **Invariant 1**: When restoring an older database backup, the application recovery sequence runs the `TombstoneReconciler` before accepting incoming network traffic.
- **Invariant 2**: Any document resurrected in the database that has a matching entry in the tombstone store is immediately removed from the primary database, search index, and vector store.
- **Invariant 3**: An audit event `doc.tombstone_reconciled` is logged for every purged resurrected record.
