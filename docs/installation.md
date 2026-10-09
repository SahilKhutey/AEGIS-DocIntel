# Installation & Cold-Start Guide

This guide details how to install and verify AEGIS-DocIntel from a fresh environment. Follow these exact steps to ensure a clean cold-start installation.

---

## Tiered Requirements Overview

To avoid dependency bloat and disk overhead (such as downloading multi-gigabyte PyTorch binaries when not required), dependencies are divided into distinct tiers:

| Tier File | Target Use Case | Key Packages Included |
|---|---|---|
| `requirements-core.txt` | Core mathematical engines, graph sorting, PII redaction, FastAPI server | `fastapi`, `uvicorn`, `pydantic`, `numpy`, `scipy`, `networkx`, `pdfplumber` |
| `requirements-dev.txt` | Developer test suite and code quality checks | `pytest`, `pytest-cov`, `pytest-asyncio`, `ruff`, `httpx` |
| `requirements-ml.txt` | Deep learning semantic models & dense embeddings | `torch`, `sentence-transformers`, `transformers` |
| `requirements-infra.txt` | Distributed production queues & metrics | `celery`, `redis`, `prometheus-client` |

---

## Clean Cold-Start Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
```

### 2. Create and Activate Virtual Environment

=== "Linux / macOS"
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

=== "Windows (PowerShell)"
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```

=== "Windows (Command Prompt)"
    ```cmd
    python -m venv venv
    venv\Scripts\activate.bat
    ```

### 3. Install Dependencies

For testing and running the core platform, install `requirements-core.txt` and `requirements-dev.txt`:

```bash
# Core mathematical engines and API
pip install -r requirements-core.txt

# Development and testing tools (required for pytest)
pip install -r requirements-dev.txt
```

*(Optional) If you plan to run local deep learning models:*
```bash
pip install -r requirements-ml.txt
```

---

## Verifying the Installation

Execute the test suite to confirm that all 944 unit tests pass cleanly:

```bash
python -m pytest tests/
```

Expected output:
```
============================= 944 passed in 12.45s =============================
```

### Testing the Standalone `aegis-docprep` Distribution

To verify the standalone subpackage in isolation:

```bash
cd aegis-docprep
pip install -e .
pytest tests/
```

Expected output:
```
============================= 17 passed in 0.20s =============================
```

---

## Running the API Server

Start the local FastAPI application:

```bash
python start.py
# Or directly via uvicorn:
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify service readiness:
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "version": "1.0.0-alpha"}
```

Access Swagger UI interactive documentation at `http://localhost:8000/docs`.

---

## Cold-Start Troubleshooting

### Issue: `pytest: command not found`
**Cause:** Attempting to run tests immediately after installing only `requirements.txt` or `requirements-core.txt`.  
**Fix:** Install developer requirements: `pip install -r requirements-dev.txt`.

### Issue: PyTorch download timeout or disk exhaustion
**Cause:** Installing `requirements-ml.txt` on a resource-constrained server.  
**Fix:** The platform is designed to operate fully without PyTorch; core graph and spatial algorithms run on `requirements-core.txt`. Semantic embeddings will automatically fall back to deterministic feature vectors with a warning flag (`MasterState.semantic_status = 'mock_fallback'`).
