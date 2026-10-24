# AEGIS-DocIntel — Backup & Restore Runbook

This runbook outlines backup strategies, recovery objectives, and step-by-step restoration procedures for AEGIS-DocIntel's persistent storage.

---

## 1. Recovery Objectives

- **Recovery Point Objective (RPO):** < 1 hour (periodic hourly snapshots) or < 24 hours (daily cold backup).
- **Recovery Time Objective (RTO):** < 15 minutes to restore state and pass readiness probes.

---

## 2. Backup Methods

AEGIS-DocIntel stores document metadata, extraction states, and raw document bytes in SQLite. Two backup procedures are supported:

### A. Online Non-Blocking Backup (Recommended)

SQLite supports online snapshots without stopping the application or risking partial-write corruption using `VACUUM INTO`:

```bash
# Execute non-blocking online backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
sqlite3 /app/data/documents.db "VACUUM INTO '/app/data/backups/documents_backup_${TIMESTAMP}.db';"
```

### B. Cold Backup (Service Stopped)

1. Stop the AEGIS service to ensure all write transactions are flushed.
2. Copy database and write-ahead log (WAL) files:
   ```bash
   cp /app/data/documents.db* /backup/destination/
   ```

---

## 3. Automated Backup Cron Job

Add the following entry to crontab for hourly online backups with 7-day retention:

```cron
0 * * * * sqlite3 /app/data/documents.db "VACUUM INTO '/app/data/backups/backup_$(date +\%F_\%H).db';"
0 2 * * * find /app/data/backups/ -name "backup_*.db" -mtime +7 -delete
```

---

## 4. Disaster Recovery & Restoration Procedure

To restore from a backup file:

1. **Halt Application Service:**
   ```bash
   docker stop aegis-service
   ```
2. **Archive Current Corrupted Database (for forensics):**
   ```bash
   mv /app/data/documents.db /app/data/documents_corrupt_$(date +%s).db
   ```
3. **Restore Backup Snapshot:**
   ```bash
   cp /app/data/backups/backup_target.db /app/data/documents.db
   ```
4. **Validate Database Integrity:**
   ```bash
   sqlite3 /app/data/documents.db "PRAGMA integrity_check;"
   # Expected output: ok
   ```
5. **Start Application Service & Verify Readiness:**
   ```bash
   docker start aegis-service
   curl -f http://localhost:8000/readiness
   ```
