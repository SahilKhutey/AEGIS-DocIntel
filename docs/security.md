# Security Policy & Internal Audit Findings

This document describes the security posture of AEGIS-DocIntel, details the vulnerabilities identified and resolved during Phase 10, and defines our vulnerability reporting procedures.

---

## Reporting a Vulnerability

We take the security of AEGIS-DocIntel seriously. If you identify a security vulnerability, **please report it privately rather than creating a public GitHub issue**.

- **Email**: `security@aegis-docintel.org` (or contact maintainers privately via GitHub Security Advisories)
- **Encryption**: Include your PGP public key if you require encrypted communications.
- **Response Target**: Initial triage acknowledgment within 48 hours.

Please include:
- A clear description of the vulnerability and potential impact.
- Step-by-step reproduction instructions or a minimal proof of concept.
- Affected component(s) (e.g. `aegis-docprep`, API router, workflow worker).

---

## Phase 10 Internal Audit: Key Findings & Resolutions

During Phase 10, a comprehensive code review of authentication, authorization, and input processing identified the following issues:

### 1. Critical: development authentication bypass (gated — not removed)
- **Issue (Phase 10)**: `dev-<tenant>` bearer tokens and the `aegis-dev-key` API key were accepted regardless of environment.
- **Resolution**: they are accepted **only** when `AEGIS_ENVIRONMENT=development`; the default is `production`, where they return 401. The bypass code path still exists by design for local development and tests. There is no `ALLOW_DEV_BYPASS` variable (earlier versions of this page named one in error). Verified by `tests/test_auth_guard.py`.

### 2. Critical: most routes had no authentication at all (found and fixed in Phase 0)
- **Issue**: probing the live app without credentials showed that 45 of 59 operations accepted anonymous requests — the legacy AEL routes, annotations, admin, advanced and webhook routers had never been wired to authentication. An anonymous caller could export another tenant's document (`GET /v1/documents/{id}/export`) and wipe every document for every tenant (`DELETE /v1/document` → 204).
- **Resolution**: `src/api/auth_guard.py` — a deny-by-default ASGI middleware. Every HTTP route returns 401 without valid credentials unless it is on a short explicit public list (`/health`, `/readiness`, `/docs`, `/redoc`, `/openapi.json`, `/metrics`). New routes are protected automatically. `tests/test_auth_guard.py` probes every operation in the app, so a future unprotected route fails CI.
- **Known exposure**: `/metrics` is public and its series are labelled with `tenant_id`; keep it off the public internet.

### 3. Known gap: production credentials cannot be validated yet
The RS256 JWT and API-key validators in `src/api/auth.py` are stubs. Outside development every credential is rejected, so the API is currently usable only in development mode. Tracked as I-20.

### 2. Transitive Dependency Vulnerability Triage
- **Issue**: Dependency vulnerability scanning detected known CVE advisories in optional legacy packages.
- **Resolution**: Pruned obsolete packages, pinned modern versions in `requirements-core.txt`, and isolated deep learning components into optional `requirements-ml.txt`. Continuous automated scanning (`pip-audit` / GitHub Dependabot) is now active in CI.

### 3. File Ingestion Path Traversal Hardening
- **Issue**: Document upload filenames were not consistently sanitized before temporary filesystem persistence.
- **Resolution**: Enforced strict UUID-based temporary path mapping (`doc_<uuid4>`) preventing directory traversal via crafted `../../` filenames.

---

## Security Architecture & Assumptions

- **Sandbox Boundary**: The processing engines assume untrusted inputs. File parsing is executed with resource limits to prevent memory exhaustion from crafted "decompression bombs".
- **Internal Audit Status**: The findings documented above represent our own internal rigorous code audits. They do not constitute a formal third-party penetration test.
