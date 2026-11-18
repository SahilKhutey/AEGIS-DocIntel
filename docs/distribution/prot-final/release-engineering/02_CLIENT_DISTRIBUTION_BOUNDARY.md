# Client Distribution Boundary & Allowlist Specification

**Phase:** PROT-FINAL-04  
**Date:** 2026-11-18T04:20:09.415275+00:00  

---

## 1. Component Distribution Classification

| Repository Path | Classification | Distribution Policy |
|---|---|---|
| `web/` | Public Client | Compiled production build only (no source maps) |
| `src/` | Private Backend | **EXCLUDED** (0 files allowed in client archive) |
| `tests/` | Internal Test Suite | **EXCLUDED** |
| `evaluation/` | Private Benchmarks | **EXCLUDED** |
| `audit/` | Audit Evidence | **EXCLUDED** |
| `distribution/demo-edition/launcher/` | Client Launchers | **INCLUDED** (PowerShell & POSIX scripts) |
| `distribution/demo-edition/deploy/` | Client Deploy Config | **INCLUDED** (compose.yaml, proxy.conf) |
| `distribution/demo-edition/demo-data/` | Synthetic Evaluation Data | **INCLUDED** (synthetic demo docs only) |
| `distribution/demo-edition/license/` | Public License | **INCLUDED** (`evaluation.lic`, `public-key.pem`) |
| `.env*`, `.git/`, `.github/` | Repository Secrets | **STRICTLY PROHIBITED** |

## 2. Enforcement Mechanism
Enforced programmatically via `scripts/release/assemble_client.py` and validated independently by `scripts/release/validate_artifact.py`.
