# AEGIS-DocIntel — Release Versioning & Contract Architecture

This document defines the formal versioning specification and release contracts across AEGIS-DocIntel packages, services, and API specifications.

---

## 1. Versioning Stratification

AEGIS-DocIntel maintains a three-tier versioning model to separate platform release maturity, API wire-format compatibility, and standalone library distribution:

```
+-------------------------------------------------------------------------+
| Tier 1: Platform Distribution Package (`aegis-docintel`)               |
| Current Version: 0.1.0-alpha.1                                          |
| Source of Truth: pyproject.toml, production/release/VERSION            |
| Scope: Full multi-tenant server, mathematical engines, orchestrator     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Tier 2: API Contract Specification (`FastAPI / OpenAPI`)                |
| Current Version: 1.0.0 (API v1)                                         |
| Source of Truth: config/settings.yaml (`app.version`), openapi.json     |
| Scope: Wire format, JSON schemas, route signatures, error models       |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Tier 3: Standalone Preprocessing Library (`aegis-docprep`)             |
| Current Version: 0.1.0                                                  |
| Source of Truth: aegis-docprep/pyproject.toml                           |
| Scope: PII redaction, context packing, spatial reading order            |
+-------------------------------------------------------------------------+
```

---

## 2. Release Contract Specifications

### 2.1 Tier 1: Platform Distribution (`aegis-docintel`)
- **Format:** Semantic Versioning (`MAJOR.MINOR.PATCH[-PRERELEASE]`).
- **Current Lifecycle State:** `0.1.0-alpha.1` (Alpha / Active Remediation).
- **Packaging:** Built via PEP 517/621 (`python -m build --wheel`), published as wheel distribution.
- **Breaking Changes:** During `0.x` phases, breaking internal architectural refactors may occur between minor versions with migration notes in `docs/changelog.md`.

### 2.2 Tier 2: REST & WebSocket API Contract (`v1`)
- **Format:** SemVer for OpenAPI schema; URL path versioning (`/v1/...`).
- **Current Version:** `1.0.0`.
- **Contract Guarantees:**
  - Route additions are backward-compatible.
  - Existing response models retain documented fields (`doc_id`, `status`, `evidence`, etc.).
  - Schema drift is enforced in CI via `openapi.json` diff verification.
  - Client SDKs (`sdk/python`) target the stable `v1` contract.

### 2.3 Tier 3: Standalone Library (`aegis-docprep`)
- **Format:** SemVer (`MAJOR.MINOR.PATCH`).
- **Current Version:** `0.1.0`.
- **License:** Apache 2.0 (commercial and open-source friendly).
- **Scope:** Zero heavyweight dependencies (pure Python with optional regex/presidio hooks).
- **Distribution:** Standalone PyPI package target for developers building RAG and privacy pipelines.

---

## 3. Version Drift Verification

Release consistency is validated during continuous integration:
1. `python scripts/check_dependency_sync.py`: Verifies dependencies across all tiers.
2. `python scripts/check_docs_claims.py`: Verifies documentation claims and relative links.
3. CI OpenAPI Drift Check: Ensures `app.openapi()` strictly matches `openapi.json`.
