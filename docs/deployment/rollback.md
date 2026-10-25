# AEGIS-DocIntel — Rollback Runbook

This document specifies the standard procedure to roll back an AEGIS-DocIntel release in case of critical defects, schema migration failure, or degraded operational metrics.

---

## 1. Rollback Criteria

Initiate an immediate rollback if any of the following occur within 30 minutes of deployment:
- Error rate (`5xx`) exceeds 1% of total API traffic.
- Readiness probe (`/readiness`) fails persistently for > 3 minutes.
- Schema migration aborts or corrupts persistent storage.
- PII redaction or tenant isolation tests fail in smoke verification.

---

## 2. Container Rollback Procedure

For Kubernetes or container-based deployments:

```bash
# 1. Inspect recent deployment history
kubectl rollout history deployment/aegis-docintel

# 2. Roll back to the previous stable revision
kubectl rollout undo deployment/aegis-docintel

# 3. Monitor rollout status
kubectl rollout status deployment/aegis-docintel

# 4. Verify readiness probe passes
curl -f http://<internal-ip>:8000/readiness
```

For Docker Compose or single-host deployments:

```bash
# 1. Stop current container
docker stop aegis-service

# 2. Restart previous stable container tag
docker run -d --name aegis-service -v aegis_data:/app/data aegis-docintel:v1.0.0-stable
```

---

## 3. Database State Rollback Procedure

When rolling back across schema revisions (e.g., reverting from v2 to v1):

1. **Stop Traffic:** Divert traffic or scale replicas to 0 to prevent concurrent writes.
2. **Restore Pre-Migration Snapshot:**
   ```bash
   cp /app/data/backups/documents_pre_migration.db /app/data/documents.db
   ```
3. **Verify Restored Database Integrity:**
   ```bash
   sqlite3 /app/data/documents.db "PRAGMA integrity_check;"
   sqlite3 /app/data/documents.db "SELECT count(*) FROM documents;"
   ```
4. **Restart Service:** Restart containers and verify readiness probe.

---

## 4. Post-Rollback Verification Checklist

- [ ] `GET /health` returns HTTP 200 with status `healthy`.
- [ ] `GET /readiness` returns HTTP 200 with persistent database marked `ok`.
- [ ] Sample document ingestion completes without error.
- [ ] Sample document retrieval and context query succeed.
- [ ] Post-incident review ticket created with logs and root cause analysis.
