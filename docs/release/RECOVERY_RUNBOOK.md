# AEGIS-DocIntel — Operational Recovery Runbook

## 1. Overview & Storage Architecture

AEGIS-DocIntel uses SQLite with Write-Ahead Logging (WAL) for persistent metadata, document records, and extraction results. The database path is configured via `AEGIS_SQLITE_PATH` (default: `data/documents.db`).

The storage engine ensures ACID compliance, crash safety, and consistency across service restarts.

> [!NOTE]
> Single-node SQLite deployments are suitable for controlled pilot operations. The platform is **not production-ready** for active-active multi-datacenter replication.

---

## 2. Backup Procedures

### 2.1 Automated Online Backup
To create a consistent, point-in-time snapshot of the database without stopping the service:

```bash
python scripts/backup_sqlite.py --db-path data/documents.db --backup-dir data/backups
```

This uses the SQLite Online Backup API, ensuring locks are managed safely without corrupting concurrent readers or writers.

### 2.2 Backup Integrity Verification
Every generated backup snapshot should be verified before archiving:

```bash
python -c "import sqlite3; con = sqlite3.connect('data/backups/documents_backup_latest.db'); print(con.execute('PRAGMA integrity_check;').fetchone()[0])"
```

A healthy backup must return:
```
ok
```

---

## 3. Disaster Recovery & Restoration Drill

When recovery from backup is required due to accidental deletion, filesystem failure, or data corruption:

### Step 1: Quiesce Ingestion Traffic
Stop the AEGIS-DocIntel container or application process to prevent new write attempts:
```bash
docker compose -f deploy/docker-compose.yml stop app
```

### Step 2: Quarantine Corrupt State
Move the damaged database file aside to preserve forensic evidence:
```bash
mv data/documents.db "data/documents.db.corrupt.$(date +%s)"
```

### Step 3: Restore Verified Snapshot
Copy the most recent verified backup file to the target path:
```bash
cp data/backups/documents_backup_latest.db data/documents.db
```

### Step 4: Verify Restored Database
Run the integrity check on the restored database file:
```bash
python -c "import sqlite3; con = sqlite3.connect('data/documents.db'); res = con.execute('PRAGMA integrity_check;').fetchone()[0]; assert res == 'ok'; print('Database verified successfully.')"
```

### Step 5: Start Service & Execute Health Verification
Restart the application container:
```bash
docker compose -f deploy/docker-compose.yml up -d app
```

Verify service readiness:
```bash
curl -f http://localhost:8000/v1/health
```

---

## 4. Ingestion Idempotency & Failure Cleanup

1. **Duplicate Request Handling**: Clients submitting uploads with an `Idempotency-Key` header receive the cached response if the identical payload was previously processed, preventing duplicated chunk entries.
2. **Aborted Upload Cleanup**: Ingestion pipelines run in isolated transactions. If document parsing fails mid-stream, changes are rolled back automatically, preventing orphaned chunks or corrupt partial document states.
