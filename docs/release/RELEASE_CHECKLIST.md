# AEGIS-DocIntel — Release Qualification Checklist

This checklist defines the step-by-step procedure required prior to tagging or deploying any AEGIS-DocIntel release.

> [!WARNING]
> Do not bypass any gate. The platform is **not production-ready** for unverified deployment. Every command must exit with code 0 before proceeding to the subsequent stage.

---

## Stage 1: Pre-Release Governance & Configuration

Run all pre-flight integrity checks from the repository root:

- [ ] **Dependency Synchronization**: Ensure poetry and lock dependencies match:
  ```bash
  python scripts/check_dependency_sync.py
  ```

- [ ] **Documentation Claims Audit**: Verify truthfulness and rule compliance:
  ```bash
  python scripts/check_docs_claims.py
  ```

- [ ] **Evaluation Dataset Contract**: Validate dataset hashes, schema, and split sizes:
  ```bash
  python scripts/validate_mvp_dataset.py
  ```

- [ ] **Release Configuration Validation**: Verify runtime settings and security invariants:
  ```bash
  python scripts/validate_release_config.py --env production
  ```

---

## Stage 2: Automated Acceptance Suites

Run the full acceptance and evaluation suites:

- [ ] **Security Acceptance Suite**:
  ```bash
  pytest tests/security/ -q
  ```

- [ ] **Integration & Recovery Suite**:
  ```bash
  pytest tests/integration/ -q
  ```

- [ ] **Evaluation Quality Suite**:
  ```bash
  pytest tests/evaluation/ -q
  ```

- [ ] **Benchmark Quality Gates**:
  ```bash
  python evaluation/scripts/run_all.py --fail-under-gates
  ```

*Alternative: Run all Stage 1 and Stage 2 gates in one step via:*
```bash
python scripts/run_mvp_acceptance.py
```

---

## Stage 3: Deployment & Staging Smoke Test

- [ ] **Build Docker Image**:
  ```bash
  docker compose -f deploy/docker-compose.yml build
  ```

- [ ] **Launch Staging Stack**:
  ```bash
  docker compose -f deploy/docker-compose.yml up -d
  ```

- [ ] **Verify Service Readiness**:
  ```bash
  curl -fsS http://localhost:8000/v1/health || exit 1
  ```

- [ ] **Create Baseline Backup**:
  ```bash
  python scripts/backup_sqlite.py --db-path data/documents.db --backup-dir data/backups
  ```

---

## Stage 4: Rollback Procedure

In case of deployment failure or critical regression during verification:

1. **Stop Application Stack**:
   ```bash
   docker compose -f deploy/docker-compose.yml down
   ```
2. **Restore Database Snapshot**:
   Follow the restoration protocol documented in the [Operational Recovery Runbook](RECOVERY_RUNBOOK.md).
3. **Re-deploy Previous Stable Image**:
   Tag and deploy the prior known-good container image.
