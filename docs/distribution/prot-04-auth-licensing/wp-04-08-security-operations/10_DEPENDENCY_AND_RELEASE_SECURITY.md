# PROT-04.08 — Dossier 10: Dependency, Build & Release Security

## 1. Supply Chain & Distribution Security Goals
The Protected Demo Edition package is distributed as an installable client artifact. Supply chain security guarantees that:
1. No private signing keys or development tokens are embedded in client binaries or frontend bundles.
2. Dependencies are locked, audited for known CVEs, and tracked via an authoritative Software Bill of Materials (SBOM).
3. Continuous integration workflows enforce strict least-privilege permissions.

---

## 2. Automated Static Secrets Gate

During release packaging and continuous integration, static scanning is enforced across all source trees (`src/`, `web/src/`):

| Target Scan Pattern | Checked Files | Policy |
| :--- | :--- | :--- |
| `BEGIN [A-Z ]*PRIVATE KEY` | `src/**/*.py`, `web/src/**/*` | Zero Tolerance (Reject Build) |
| `dev-default-tenant` / `dev-*` token fallbacks | `web/src/**/*.{ts,tsx,js}` | Zero Tolerance (Reject Build) |
| Hardcoded Backend Secrets / Passwords | `src/**/*.py` | Zero Tolerance (Reject Build) |

### Frontend Production Auth Guard:
`npm --prefix web run verify:auth` executes `scripts/verify-production-auth.mjs`. In WP-04.08, this check runs cleanly with zero violations:
```
Running PROT-04 Production Authentication Guard...
✅ PROT-04 Guard Passed: No development tokens or auth bypasses found in web/src.
```

---

## 3. Software Bill of Materials (SBOM) Generation
A formal CycloneDX v1.5 JSON SBOM is generated as part of release artifacts (`audit/prot-04-08/release-security/sbom.json`). It catalogs canonical dependency coordinates:
- `pkg:pypi/fastapi@0.115.0`
- `pkg:pypi/cryptography@43.0.0`
- `pkg:pypi/pyjwt@2.9.0`
- `pkg:pypi/pydantic@2.9.0`
- `pkg:pypi/uvicorn@0.30.0`

---

## 4. CI Least-Privilege Enforcement
GitHub Actions workflow configurations (`.github/workflows/*.yml`) enforce least-privilege token permissions:
```yaml
permissions:
  contents: read
  packages: none
  id-token: none
  issues: none
  pull-requests: none
```
Write permissions are granted only to specific release jobs when publishing signed artifacts to release registries.
