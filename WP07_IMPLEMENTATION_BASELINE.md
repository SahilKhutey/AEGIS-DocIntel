# AEGIS-DocIntel — WP-07: Security & Reliability Implementation Baseline

> **Document ID**: `WP07_IMPLEMENTATION_BASELINE.md`  
> **Status**: **VERIFIED & ACCEPTED**  
> **Branch**: `wp-07-security-reliability`  
> **Canonical Baseline Anchor**: `7c05522643e503396795d99e381d201268ebe7fe` (`aegis-baseline-001`)  
> **Objective**: Comprehensive architectural discovery and baseline assessment of identity, authorization, tenant isolation, privacy protection, document lifecycle deletion, worker reliability, and disaster recovery.

---

## 1. Architectural Baseline Assessment

### 1.1 Authentication & Authorization Subsystem (WP-07.01)
- **Primary Authentication Mechanism**:
  - `src/api/auth.py`: Production-grade RS256 JWT validation using RSA public key cryptography (`AEGIS_JWT_PUBLIC_KEY` or `AEGIS_JWT_PUBLIC_KEY_PATH`).
  - Claims Enforcement: Required standard claims `exp`, `sub`, `tenant_id` (or `tid`), and optional `iss`, `aud`.
  - API Key Authentication: `X-API-Key` header with constant-time SHA-256 hash lookup against configured tenant key store.
  - Development Fallback: Explicit `AEGIS_ENVIRONMENT=development` gate allowing `dev-{tenant_id}` tokens and `aegis-dev-key`.
- **Identity & Security Context**:
  - `src/core/security_context.py`: Typed immutable `TenantContext` containing `tenant_id`, `principal_id`, `roles: frozenset[str]`, `authentication_method`, and `monthly_token_limit`.
  - Canonical Enterprise Roles: `viewer`, `editor`, `reviewer`, `review_admin`, `tenant_admin`, `platform_admin`, `admin`.
- **Centralized Server-Side Authorization**:
  - `src/core/authorization.py`:
    - `require_tenant_context(request)`: Fails closed with HTTP 401 if unauthenticated.
    - `require_roles(*allowed_roles)`: Fails closed with HTTP 403 if principal lacks authorized role.
    - `verify_resource_tenant(resource_tenant_id, context)`: Fail-closed anti-IDOR protection returning HTTP 404 rather than 403 on tenant mismatch, preventing resource existence enumeration.

### 1.2 Multi-Tenant Isolation Architecture (WP-07.02)
- **Tenant Context Derivation**:
  - Identity is strictly derived from the verified cryptographic JWT signature or API key hash at the server boundary. Client-supplied headers or request body parameters cannot override the server-derived `TenantContext`.
- **Data & Query Isolation**:
  - Relational Metadata: Every document record in SQLite contains a mandatory `tenant_id` column. Queries explicitly filter by `WHERE tenant_id = :tenant_id`.
  - Vector Store (`src/engines/vector_db/faiss_store.py`): Metadata indexed with `tenant_id`. Vector similarity search performs tenant filtering prior to score ranking.
  - Semantic Cache (`src/memory_engine/semantic_cache.py`): In-memory dictionary strictly partitioned by tenant ID (`_entries[tenant_id]`).
  - Background Operations: `JobRecord` in `src/operations/job_contracts.py` retains `tenant_id`. Handlers validate tenant context before processing.

### 1.3 Privacy & PII Detection Pipeline (WP-07.03)
- **Detection Architecture**:
  - `aegis-docprep/aegis_docprep/pii_redaction.py`: Multi-pattern scanner covering:
    - Social Security Numbers (`SSN_REGEX` with formatting validation)
    - Credit Cards (`CREDIT_CARD_REGEX` with Luhn mod-10 algorithm check)
    - Phone Numbers (E.164 and North American variants)
    - Email Addresses (`EMAIL_REGEX`)
    - API Secrets & Tokens (`sk-*`, `AKIA*`, `ASIA*`, `ghp_*`, `github_pat_*`)
    - Personal Names (Title-case entity heuristics with exclusion filters)
- **Policy Enforcement**:
  - Actions supported: `redact` (mask with `[REDACTED_...]`), `tokenize`, `flag_only`, `allow`.
  - Fail-Closed Gate: Catastrophic detector failures raise `PIIRedactionPolicyError`.
  - Telemetry Sanitization: `ComplianceReport.safe_summary()` reports aggregated category counts without logging raw sensitive string matches.
- **Benchmarked Quality**:
  - `evaluation/scripts/evaluate_privacy.py`: Verified Precision $\ge 0.85$, Recall $\ge 0.85$, and 0.0% sensitive secret leakage.

### 1.4 Document Lifecycle & Cascading Deletion (WP-07.04)
- **Current Deletion Path**:
  - `RealDocumentService.delete(doc_id, tenant_id)` in `src/services/container.py`.
  - Enforces tenant ownership match before deletion.
  - Cascades removal across:
    1. Primary document index (`_docs`) and relational database row.
    2. Vector database (`FAISSStore` removes corresponding embedding vectors).
    3. Semantic cache (`SemanticCache` invalidates cached queries referencing `doc_id`).
- **Gaps to Address in WP-07**:
  - Introduce formal, durable deletion manifest with explicit lifecycle stages:
    `ACTIVE -> DELETE_REQUESTED -> ACCESS_BLOCKED -> DERIVATIVES_REMOVED -> INDEXES_AND_CACHES_CLEARED -> STORAGE_REMOVED -> VERIFICATION -> DELETED`.
  - Implement durable deletion tombstones to prevent post-restore data resurrection.

### 1.5 Background Worker Reliability & Fault Tolerance (WP-07.05)
- **Worker Infrastructure**:
  - `src/operations/worker.py` (`JobWorker`):
    - Lease-based atomic claiming (`renew_lease`, default 120s window).
    - Asynchronous heartbeat renewal task (`_heartbeat_loop`).
    - Error classification: `PermanentJobError` (no retry) vs `TransientJobError` (exponential backoff).
  - `src/operations/retry_policy.py`: Bounded retries with randomized jitter.
  - `src/operations/job_repository.py`: Durable state transitions (`QUEUED`, `RUNNING`, `COMPLETED`, `RETRY_PENDING`, `FAILED`, `CANCELLED`).
- **Gaps to Address in WP-07**:
  - Dedicated fault-injection test suite simulating worker crashes, database disconnections, lease expirations, duplicate job deliveries, and timeout cancellations.

### 1.6 Backup, Restoration & Disaster Recovery (WP-07.06)
- **Backup Strategy**:
  - `scripts/backup_sqlite.py`: Non-blocking online SQLite backup via `sqlite3.Connection.backup()`.
  - Immediate verification: Executes `PRAGMA integrity_check` on the destination snapshot.
  - Hardened file permissions (`0o600`).
- **Restoration Verification**:
  - Verified in `tests/integration/test_backup_restore.py`.
- **Gaps to Address in WP-07**:
  - End-to-end disaster recovery runbook and clean-environment restoration tests.
  - Quantitative measurement of Recovery Point Objective (RPO) and Recovery Time Objective (RTO).
  - Cryptographic backup encryption, corruption rejection, and tombstone reconciliation.

---

## 2. WP-07 Execution Roadmap & Deliverables

| Task ID | Focus Area | Deliverables | Target Gate |
| :--- | :--- | :--- | :--- |
| **WP-07.01** | Authentication & Authorization | `AUTH_SECURITY_INVENTORY.md`<br/>`ROLE_PERMISSION_MATRIX.csv`<br/>`AUTHENTICATION_TEST_REPORT.json`<br/>`AUTHORIZATION_TEST_REPORT.json` | 0 unauthorized accesses<br/>0 privilege escalations |
| **WP-07.02** | Tenant Isolation | `TENANT_ISOLATION_MATRIX.csv`<br/>`TENANT_ISOLATION_TEST_REPORT.json`<br/>`CROSS_TENANT_ATTACK_REPORT.md` | 0 cross-tenant disclosures<br/>0 cross-tenant mutations |
| **WP-07.03** | Privacy Detection | `PRIVACY_CLASSIFICATION_POLICY.md`<br/>`PRIVACY_GOLDEN_DATASET.jsonl`<br/>`PRIVACY_DETECTION_REPORT.json`<br/>`PRIVACY_OUTPUT_LEAKAGE_REPORT.json` | 0% secret leakage<br/>Precision $\ge 0.90$<br/>Recall $\ge 0.90$ |
| **WP-07.04** | Document Deletion | `DOCUMENT_DATA_LIFECYCLE.md`<br/>`DELETION_TARGET_REGISTER.csv`<br/>`DOCUMENT_DELETION_TEST_REPORT.json`<br/>`DELETION_COMPLETENESS_REPORT.json` | 100% target cleanup<br/>Tombstone preservation |
| **WP-07.05** | Worker Fault Injection | `WORKER_INVENTORY.md`<br/>`WORKER_FAULT_INJECTION_PLAN.md`<br/>`WORKER_RELIABILITY_REPORT.json`<br/>`JOB_STATE_CONSISTENCY_REPORT.json` | 0 silent job losses<br/>Idempotent execution |
| **WP-07.06** | Backup Restoration | `BACKUP_POLICY.md`<br/>`BACKUP_INTEGRITY_REPORT.json`<br/>`RESTORATION_TEST_REPORT.json`<br/>`RPO_RTO_MEASUREMENTS.json`<br/>`DISASTER_RECOVERY_RUNBOOK.md` | Clean restore verified<br/>RPO $\le 1\text{ hr}$, RTO $\le 15\text{ min}$ |
| **Audit** | Central Audit Integration | `SecurityReliabilityAuditSuite`<br/>`WP07_FINAL_AUDIT.md`<br/>Acceptance Artifact | All 7+ suites passing<br/>0 Critical/High findings |
