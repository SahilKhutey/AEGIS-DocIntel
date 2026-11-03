# AEGIS-DocIntel — Environment & Dependency Reproducibility Report
**Baseline ID**: AEGIS-BASELINE-001  
**Generated Date**: 2026-11-03  
**Status**: VERIFIED (with environment isolation requirement)

---

## 1. Executive Summary

This reproducibility report establishes the technical requirements and validation status for recreating the exact development, testing, and operational runtime of **AEGIS-DocIntel**.

The canonical repository provides strictly separated requirement manifests and SHA256-pinned lockfiles:
- `requirements-core.txt` & `requirements-core.lock.txt`
- `requirements-ml.txt` & `requirements-ml.lock.txt`
- `requirements-ocr.txt`
- `requirements-ui.txt`
- `requirements-infra.txt`
- `requirements-dev.txt`

---

## 2. Verified Host Environment

| Parameter | Observed Value | Validation Status |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Enterprise / Pro (64-bit, Build 26300) | COMPLIANT |
| **Python Runtime** | Python 3.12.10 (`sys.executable`) | COMPLIANT |
| **Node.js Runtime** | Node.js v24.18.0 | COMPLIANT |
| **Package Manager (JS)** | npm 11.16.0 | COMPLIANT |
| **Version Control** | Git 2.54.0.windows.1 | COMPLIANT |

---

## 3. Dependency Lockfile Integrity

The lockfiles guarantee deterministic wheel resolution across platforms:

| Lockfile | Purpose | SHA256 Checksum |
| :--- | :--- | :--- |
| `requirements-core.lock.txt` | Minimal Core Runtime (API, Parsers, Math, Graph) | `838fff8d275bbc511947c67b92ba9dac18df0e7ad9b23fd948669928eae72de7` |
| `requirements-ml.lock.txt` | Optional ML & Embedding Tier (Torch, Transformers) | `c11d2b9db9138308703760991023f5c4c2de7656ed44f805f451542f92aa2d99` |

---

## 4. Environment Health Findings

An audit of the host environment via `python -m pip check` identified pre-existing dependency conflicts within the unisolated system-level Python environment:
- Conflicts between system tools (`aider-chat`, `ai-fashion-assistant`, `mediapipe`) and modern Starlette/FastAPI/Protobuf versions.
- **Architectural Remedy**: AEGIS-DocIntel execution and testing must **always** occur within an isolated virtual environment (`.venv`) initialized directly from the locked manifests rather than the ambient global environment.

---

## 5. Verified Clean Reproduction Procedure

To deterministically reproduce this environment from a clean machine:

```powershell
# 1. Clone canonical repository
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel

# 2. Checkout canonical baseline
git checkout aegis-baseline-001

# 3. Create isolated Python 3.12 virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip and install locked core dependencies
python -m pip install --upgrade pip
pip install -r requirements-core.lock.txt

# 5. Verify dependency health
pip check
# Expected result: No broken requirements found.
```

---

## 6. Reproducibility Acceptance Sign-Off

- **Host Runtimes Captured**: PASS
- **Direct & Transitive Inventories Exported**: PASS (`dependency_inventory.csv`)
- **Secrets Excluded**: PASS (`environment_variables_inventory.txt` verified free of tokens/keys)
- **Lockfile Checksums Verified**: PASS
- **Overall WP01-02 Status**: **PASS**
