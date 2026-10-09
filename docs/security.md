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

### 1. Critical: Development Authentication Bypass Elimination
- **Issue**: A legacy development flag (`ALLOW_DEV_BYPASS=true`) permitted unauthenticated API access regardless of environment configuration if specific headers were omitted.
- **Resolution**: Completely excised the bypass code path. Authentication is now strictly enforced via standard Bearer tokens, with test mocking restricted exclusively to isolated unit test fixtures.
- **Reference**: Traced and verified in `production/security-audit/`.

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
