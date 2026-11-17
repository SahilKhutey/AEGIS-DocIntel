# PROT-01: Repository Baseline State

**Document:** 01_REPOSITORY_BASELINE.md  
**Audit Target:** `SahilKhutey/AEGIS-DocIntel`  
**Audit Timestamp:** 2026-11-12T19:59:00Z  

---

## 1. Git Repository State

| Parameter | Value | Verification Source |
| :--- | :--- | :--- |
| **Remote Origin URL** | `https://github.com/SahilKhutey/AEGIS-DocIntel.git` | `git-state.json` / git config |
| **Active Development Branch** | `master` (and feature tracking `feat/mvp8-job-orchestration`) | `audit/baseline/git-state.json` |
| **Latest Observed Commit** | `16a688a4bf189b57c9552f1309659cd03482094f` | Public GitHub code search snapshot |
| **Canonical Audit Commit** | `7c05522643e503396795d99e381d201268ebe7fe` | `audit/baseline/canonical_commit.txt` |
| **Head Commit (Audit Baseline)** | `32dfcb977344805d2932052df3bd58ce3f73dd18` | `audit/baseline/git-state.json` |
| **Published Software Release** | `v1.1.0` | GitHub Releases / Release Verification Notes |
| **Working Tree State** | Clean build branch `product_hunt_launch_packaging` | Active worktree |

---

## 2. Commit History Traceability

The recent commit lineage reflects progressive maturation from audit baseline to production release:
1. `32dfcb9`: `feat(corpus): integrate public document corpus v1.0, 250-record manifest, and automated benchmark runner`
2. `fdb4122`: `feat(audit): deliver complete MVP audit suite, orchestrator, and verification artifacts`
3. `04527de`: `feat(ui): deliver self-contained Document Intelligence Workbench SPA`
4. `2a0ce4c`: `feat(operations): add job verification drill and harden handler result serialization`
5. `e72ae0c`: `docs(release): add MVP final verification and validation report`

---

## 3. Runtime & Toolchain Baseline

| Component | Target Version | Host Environment |
| :--- | :--- | :--- |
| **Python** | 3.12.10 | Windows 11 / Linux container runtime |
| **Node.js** | 20.x / 24.18.0 | Standalone Docker container runtime |
| **Package Manager** | `pnpm` 11.11.0 / `pip` 24.0 | Isolated build phases |
| **Container Engine** | Docker Compose v2.26+ | Linux alpine containers |
| **Cryptography** | `pyca/cryptography` 42.0+ | Ed25519 signature signing & validation |

---

## 4. Release Lineage Reconciliation

The repository contains documented transitions between:
- **Baseline v1.0.0 (Research Prototype):** In-memory prototype documented in legacy `docs/status.md`.
- **Release v1.1.0 (Production Candidate):** Reconciled workbench with complete test suite, strict tenant boundaries, and persistence.
- **Demo Edition v1.1.0 (Protected Distribution):** Hybrid downloadable package where proprietary backend logic runs behind the authenticated Evaluation Gateway.
