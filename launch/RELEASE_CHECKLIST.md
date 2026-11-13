# AEGIS-DocIntel — Release Checklist (Product Launch Edition v1.2.0)

This checklist acts as the mandatory release gate for publishing the Product Launch Edition. Every item must be verified before tagging the release or opening the Product Hunt listing.

---

## 1. Security & Authentication Release Gates

- [x] **Deny-by-Default HTTP Route Guard:** All unauthenticated calls to non-public endpoints return `401 Unauthorized`. Verified by `tests/test_auth_guard.py`.
- [x] **RS256 Production JWT Validation:** Validates `exp`, `sub`, `tenant_id`, and RS256 signature against RSA public key. Verified by `tests/test_production_auth.py`.
- [x] **Dev-Token Bypass Disabled:** `dev-*` tokens and `aegis-dev-key` are unconditionally rejected in `production` and `demo` environments.
- [x] **Scoped Demo Identity:** Demo access is strictly bounded to `demo-tenant` with `viewer`/`editor` roles. Platform and tenant administration endpoints return `403 Forbidden`. Verified by `demo/tests/test_demo_isolation.py`.
- [x] **Cross-Tenant IDOR Protection:** Parameterized SQL queries enforce `WHERE tenant_id = ?`. Inquiries for foreign tenant records return non-disclosing `404 Not Found`. Verified by `tests/test_multitenancy_isolation.py`.
- [x] **Frontend Credential Protection:** Removed hardcoded dev-tokens from `web/src/lib/api/client.ts`. No privileged secret exposed in client code.
- [x] **Metrics Egress Blocked:** Public Nginx reverse proxy returns `404 Not Found` for `/metrics` requests.

---

## 2. Ingestion, Storage & Persistence Gates

- [x] **SQLite Schema v2 Migration:** Automatically initializes document metadata, status, sha256 checksums, and raw byte storage. Verified by `tests/test_persistence_and_audit.py`.
- [x] **Cross-Restart Recovery:** Documents and orchestrator state successfully re-hydrate across container restarts. Verified by `tests/test_persistence_and_audit.py`.
- [x] **Cascading Erasure:** Document deletion atomically cleans up SQLite raw bytes, extracted chunks, and memory indexes within <500ms. Verified by `tests/test_document_deletion.py`.
- [x] **Tamper-Evident Audit Chaining:** All actions are chained with SHA-256 hashes rooted at genesis hash. Verified by `tests/test_persistence_and_audit.py`.

---

## 3. Demo Environment & Repeatability Gates

- [x] **Synthetic Document Corpus:** Three realistic technical documents created (`demo/seed/documents/`) containing repeated facts, deliberate contradictions, and tables.
- [x] **Corpus Manifest:** Machine-readable `manifest.json` indexing seed documents, expected QA facts, and contradiction pairs.
- [x] **In-Process Seeding Script:** `demo/scripts/seed_demo.py` successfully seeds documents into `demo-tenant`. Verified by `demo/tests/test_demo_seed.py`.
- [x] **Automated Workspace Reset:** `demo/scripts/reset_demo.py` and `/api/v1/demo/reset` purge temporary uploads and restore pristine seed state. Verified by `demo/tests/test_demo_reset.py`.
- [x] **Pre-Launch Verification Harness:** `demo/scripts/verify_demo.py` tests health, session discovery, queries, citations, and contradiction detection.

---

## 4. Frontend & User Experience Gates

- [x] **Same-Origin API Routing:** Browser client uses same-origin relative URLs with Next.js rewrites in `next.config.ts` or Nginx proxying.
- [x] **Dashboard Version Accurate:** Updated static "Workbench v1.0" badge to "Product Launch Edition v1.2.0 · Live Interactive Workspace".
- [x] **3-Minute Guided Walkthrough:** Guided tour cards on `/` directing visitors to Documents, Ask AEGIS, Compare Specs, and Math.
- [x] **Interactive Demo Reset Button:** Dashboard provides a 1-click "Reset Demo Data" action for evaluators.
- [x] **Citations & Evidence Rendering:** Inline citation badges link to evidence panels showing page-level passages and bounding boxes.

---

## 5. Deployment & Packaging Gates

- [x] **Self-Hosted Docker Compose:** `deploy/docker-compose.yml` updated with `aegis-web` Next.js frontend, `aegis-api`, and internal networking.
- [x] **Live Demo Docker Compose:** `deploy/docker-compose.demo.yml` packages the full demo sandbox, Nginx reverse proxy, and auto-seeding.
- [x] **Multi-Stage Frontend Dockerfile:** `deploy/Dockerfile.web` builds standalone Next.js container.
- [x] **Nginx Ingress Routing:** `deploy/nginx/aegis-demo.conf` and `deploy/nginx/aegis.conf` proxy frontend and backend traffic with rate limits and security headers.

---

## 6. Product Truth & Documentation Gates

- [x] **STATUS.md & status.md Reconciliation:** Replaced obsolete Phase 0 summary with verified test suite evidence.
- [x] **Dual Licensing Disclosure:** Explicit distinction between Apache 2.0 `aegis-docprep` and AMDI-OS Evaluation & Research terms in `launch/KNOWN_LIMITATIONS.md`.
- [x] **Product Hunt Materials:** Copy, taglines, maker comment, and screenshot plan finalized in `launch/PRODUCT_HUNT_COPY.md`.
