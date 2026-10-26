# AEGIS-DocIntel — MVP Developer Quickstart

> **Status Notice:** AEGIS-DocIntel is currently an MVP integration baseline and research toolkit; it is not production-ready. This guide details local developer onboarding, verification, and end-to-end API execution in development mode.

---

## 1. Prerequisites

Before starting, verify your environment meets the minimum requirements:

- **Python:** Version 3.12 or 3.13 (`python --version`)
- **Git:** Version 2.30+ (`git --version`)
- **Virtual Environment:** Python `venv` module available
- **Memory & Storage:** 4 GB RAM and 2 GB free disk space

No external Docker containers, GPU accelerators, or deep learning libraries are required to run the core platform or execute the benchmark suites.

---

## 2. Fresh Installation

### Step 2.1 — Clone Repository
```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
```

### Step 2.2 — Create & Activate Virtual Environment

=== "Windows (PowerShell)"
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

=== "Linux / macOS"
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2.3 — Install Dependencies
Install the tiered core and developer requirements:

```bash
pip install -r requirements-core.txt
pip install -r requirements-dev.txt
```

To review dependency tiers and optional deep learning packages, refer to [installation.md](installation.md).

---

## 3. Environment Configuration

To run locally without third-party identity providers, set the environment to `development`. This activates development auth-bypass tokens (`dev-*`) and development API keys (`aegis-dev-key`).

=== "Windows (PowerShell)"
```powershell
$env:AEGIS_ENVIRONMENT = "development"
```

=== "Linux / macOS (Bash)"
```bash
export AEGIS_ENVIRONMENT=development
```

---

## 4. Starting the Application Server

Launch the Uvicorn application server:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

When startup completes, you should observe log output indicating the service container is ready:
```text
INFO aegis.startup: Starting AEGIS-DocIntel env=development
INFO aegis.startup: AEGIS-DocIntel ready host=0.0.0.0 port=8000
```

Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## 5. Health & Readiness Verification

Open a separate terminal window and verify service availability using `curl`:

### Liveness Probe
```bash
curl -s http://localhost:8000/health
```
**Expected Response (HTTP 200):**
```json
{
  "status": "healthy",
  "checks": {
    "api": "ok",
    "document_service": "ok",
    "rag_engine": "ok"
  }
}
```

### Readiness Probe
```bash
curl -s http://localhost:8000/readiness
```
**Expected Response (HTTP 200):**
```json
{
  "ready": true,
  "checks": {
    "storage": "ok",
    "vector_store": "ok"
  }
}
```

---

## 6. End-to-End Workflow Walkthrough

### Step 6.1 — Upload a Document for Ingestion

Upload a document (e.g., text or PDF) using the `/v1/documents/upload` endpoint. In development mode, provide the header `Authorization: Bearer dev-tenant-alpha`:

```bash
# Create a sample document
echo "AEGIS-DocIntel provides submodular context packing for bounded token budgets." > sample_doc.txt

# Ingest document
curl -s -X POST http://localhost:8000/v1/documents/upload \
  -H "Authorization: Bearer dev-tenant-alpha" \
  -F "file=@sample_doc.txt"
```

**Expected Response (HTTP 202 Accepted):**
```json
{
  "doc_id": "doc-a1b2c3d4-sample",
  "status": "pending",
  "filename": "sample_doc.txt",
  "message": "Document accepted for indexing."
}
```

### Step 6.2 — Poll Ingestion Status

Check processing status by querying the document endpoint with the returned `doc_id`:

```bash
curl -s -X GET http://localhost:8000/v1/documents/doc-a1b2c3d4-sample \
  -H "Authorization: Bearer dev-tenant-alpha"
```

**Expected Response (HTTP 200 OK):**
```json
{
  "doc_id": "doc-a1b2c3d4-sample",
  "status": "completed",
  "chunks_indexed": 1,
  "tables_extracted": 0
}
```

### Step 6.3 — Execute Grounded RAG Query

Submit a natural language question against indexed documents:

```bash
curl -s -X POST http://localhost:8000/v1/query \
  -H "Authorization: Bearer dev-tenant-alpha" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does AEGIS-DocIntel provide?",
    "top_k": 3
  }'
```

**Expected Response (HTTP 200 OK):**
```json
{
  "answer": "AEGIS-DocIntel provides submodular context packing for bounded token budgets.",
  "citations": [
    {
      "chunk_id": "c_sample_0",
      "text": "AEGIS-DocIntel provides submodular context packing for bounded token budgets.",
      "score": 0.95
    }
  ],
  "confidence": "high",
  "budget_tokens_used": 14
}
```

For comprehensive route definitions and parameters, see [api.md](api.md).

---

## 7. Running Evaluation Benchmarks & Quality Gates

AEGIS-DocIntel enforces automated quality gates for extraction fidelity, context packing bounds, PII redaction, and retrieval grounding.

### Validate Evaluation Dataset Contract
Verify that the golden evaluation manifest and dataset match declared slices and counts:
```bash
python scripts/validate_mvp_dataset.py
```

### Run Quality Benchmark Suite
Execute the full benchmark suite with strict automated threshold gates:
```bash
python evaluation/scripts/run_all.py --fail-under-gates
```

All 4 quality gates must pass:
1. **Extraction:** Reading order Kendall's tau $\ge 0.80$ and table cell F1 $\ge 0.90$.
2. **Context Packing:** 0% token budget violation and knapsack approximation ratio $\ge 0.316$.
3. **Privacy:** PII precision $\ge 0.85$, recall $\ge 0.85$, and 0% secret leakage.
4. **Retrieval:** MRR $\ge 0.70$, Recall@5 $\ge 0.80$, and 100% abstention on unanswerable queries.

---

## 8. Troubleshooting & Common Pitfalls

- **HTTP 401 Unauthorized:** Ensure `Authorization: Bearer dev-<tenant_id>` or `X-API-Key: aegis-dev-key` is supplied and `AEGIS_ENVIRONMENT` is set to `development`.
- **Port 8000 in use:** Pass `--port 8080` to Uvicorn and update client URLs accordingly.
- **SQLite Concurrency:** In local development, SQLite WAL mode is used. For concurrent test execution, tests run in isolated temporary database contexts.
