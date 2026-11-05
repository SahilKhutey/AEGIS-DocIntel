# AEGIS-DocIntel — Operational Disaster Recovery Runbook

> **Document ID**: `DISASTER_RECOVERY_RUNBOOK.md`  
> **Work Item**: WP-07.06  
> **Status**: **ACTIVE & ENFORCED**  

---

## 1. Trigger Conditions
- Catastrophic database corruption or hardware disk failure.
- Accidental catastrophic deletion requiring point-in-time recovery.
- Cloud region outage requiring restoration into a secondary failover environment.

---

## 2. Step-by-Step Restoration Procedure

### Step 1: Provision Isolated Clean Recovery Environment
```bash
# Ensure target clean directory is created
mkdir -p /opt/aegis/recovery/{data,storage,backups}
```

### Step 2: Retrieve and Decrypt Validated Snapshot
- Pull the latest hourly database snapshot and document archive matching target timestamp.
- Decrypt archive using KMS key.
- Verify archive SHA-256 integrity hash against the manifest.

### Step 3: Verify Database File Integrity Prior to Boot
```bash
sqlite3 /opt/aegis/recovery/data/aegis_restored.db "PRAGMA integrity_check;"
# Must return "ok"
```

### Step 4: Apply Deletion Tombstone Reconciliation
- Load tombstone registry (`tombstones.jsonl`).
- Run `TombstoneReconciler` to purge any documents that were deleted after the backup was created.

### Step 5: Start Service & Execute Operational Smoke Suite
1. Verify database connectivity: document count matches manifest.
2. Verify original files: sample SHA-256 checksums match.
3. Verify authentication: valid JWT authenticates; invalid rejected.
4. Verify tenant isolation: Tenant A cannot access Tenant B resources.
5. Verify retrieval & QA query: sample golden question answers correctly with valid citation.
6. Verify report generation: comparative report renders without errors.

### Step 6: Update DNS & Traffic Routing
- Switch reverse proxy / load balancer traffic to the recovered service instance.
- Log recovery audit event `system.disaster_recovery_complete` with RPO and RTO metrics.
