# Build Environment Specification & Tooling Pinning

**Phase:** PROT-FINAL-04  
**Date:** 2026-11-18T04:20:09.415275+00:00  

---

## 1. Environment Pinning

| Tool | Pinned Version | Execution Scope |
|---|---|---|
| OS | Ubuntu 22.04 / 24.04 LTS | GitHub Actions Runner |
| Node.js | `22.x` (LTS) | Frontend production build |
| npm | `10.x` | Frontend dependency installation via `npm ci` |
| Python | `3.12.x` | Release assembly, signing, and verification |
| Cryptography | `cryptography>=43.0.0` | Ed25519 signing engine |
| Packaging | `packaging>=24.0` | SemVer parsing for client policy |

## 2. Reproducibility Factors
- All dependencies installed exclusively via lockfiles (`npm ci`).
- Archive packaging enforces deterministic metadata (normalized zip epoch 2026-01-01).
