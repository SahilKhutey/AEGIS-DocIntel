# AEGIS-DocIntel — Disaster Recovery & Backup Policy

> **Document ID**: `BACKUP_POLICY.md`  
> **Work Item**: WP-07.06  
> **Status**: **ACTIVE & ENFORCED**  

---

## 1. Disaster Recovery Objectives

- **Recovery Point Objective (RPO)**: Maximum allowable data loss window = **1 hour (3600 seconds)**.
- **Recovery Time Objective (RTO)**: Maximum allowable service restoration window = **15 minutes (900 seconds)**.

---

## 2. Backup Strategy

1. **Database Snapshots**:
   - SQLite online non-blocking backup (`sqlite3.Connection.backup()`) in read-only transaction mode.
   - Immediate verification: Automated execution of `PRAGMA integrity_check` on the backup file prior to finalizing snapshot.
2. **Object Storage Replication**:
   - Original source PDF files replicated to offsite backup location with cryptographic SHA-256 manifest verification.
3. **Encryption & Key Management**:
   - AES-256 encryption at rest for backup archives.
   - Backup encryption keys are managed in a physically separate key-management hierarchy (KMS / Vault) and never stored beside backup volumes.
4. **Frequency & Retention**:
   - Full automated backup snapshots every 1 hour.
   - Retention: Hourly backups kept for 24 hours, daily backups kept for 30 days, monthly backups kept for 90 days.
