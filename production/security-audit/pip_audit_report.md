# Dependency Security Audit Report (pip-audit)

**Target Specification:** `requirements-core.txt` (62 resolved dependencies)  
**Tool:** `pip-audit` v2.9.0 (PyPA Advisory Database / OSV)  
**Date:** October 2026  
**Status:** Clean — Zero Known Vulnerabilities  
**Raw Results Artifact:** [`production/security-audit/pip_audit_results.json`](pip_audit_results.json)

---

## 1. Executive Summary

A real-world dependency vulnerability audit was conducted using PyPA's `pip-audit` against all declared and transitive dependencies of `requirements-core.txt`. 

This scan replaces the previously fabricated compliance and dependency audit claims from Phase 1 with authentic, machine-generated scanner outputs.

- **Total Dependencies Inspected:** 62 packages
- **Known Vulnerabilities Identified:** 0
- **Remediated Transitive Vulnerabilities:** 1 (`ecdsa` Minerva timing attack via `python-jose` migration to `PyJWT`)

---

## 2. Remediated Supply-Chain Vulnerabilities

### Transitive `ecdsa` Vulnerability (PYSEC-2026-1325 / CVE-2024-23342)
- **Previous Component:** `python-jose[cryptography]>=3.3.0`
- **Issue Description:** `python-jose` pulled in the pure-Python `ecdsa` package. The `ecdsa` library is vulnerable to the Minerva timing attack against P-256 / ECDSA signatures, allowing private key extraction when signing operations are timed. The upstream `ecdsa` project has no fixed release available.
- **Exploitability Analysis in AEGIS-DocIntel:**
  - AEGIS-DocIntel exclusively utilizes RS256 (RSA with SHA-256) and HS256 for JWT token verification; it never executed ECDSA P-256 token verification.
  - While not exploitable under existing usage, maintaining an unmaintained cryptographic library with an open CVE introduced unnecessary supply-chain risk.
- **Remediation:**
  - Migrated authentication token parsing in `src/api/auth.py` from `python-jose` to `PyJWT[crypto]>=2.9.0`.
  - Swapped dependency declarations in `requirements-core.txt` and `pyproject.toml`.
  - Eliminates transitive dependency on `ecdsa` entirely while retaining high-performance C-accelerated cryptographic validation via `cryptography`.

---

## 3. Scanned Package Summary

The following core packages and their dependency trees were verified clean against the Python Advisory Database:

| Package | Resolved Version | Vulnerabilities Found |
|---|---|---|
| `pydantic` | 2.13.5 | 0 |
| `fastapi` | 0.142.2 | 0 |
| `uvicorn` | 0.54.0 | 0 |
| `pymupdf` | 1.28.2 | 0 |
| `pdfplumber` | 0.11.10 | 0 |
| `pillow` | 12.3.0 | 0 |
| `scikit-learn` | 1.9.1 | 0 |
| `scipy` | 1.18.1 | 0 |
| `networkx` | 3.7 | 0 |
| `numpy` | 2.5.3 | 0 |
| `pyjwt` | 2.15.1 | 0 |
| `cryptography` | 50.0.2 | 0 |
| `passlib` | 1.7.4 | 0 |
| `tiktoken` | 0.14.0 | 0 |
| `structlog` | 26.1.0 | 0 |
| `loguru` | 0.7.3 | 0 |
| `prometheus-client` | 0.26.0 | 0 |

---

## 4. Conclusion & Continuous Monitoring

The core dependency tree of AEGIS-DocIntel is completely free of known Common Vulnerabilities and Exposures (CVEs). Dependency health is continuously enforced via the CI pipeline security workflow (`.github/workflows/ci.yml`).
