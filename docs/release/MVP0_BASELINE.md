# MVP 0 — Foundation Baseline

## Run metadata
- Date: 2026-10-27
- Branch: `feat/mvp0-foundation-baseline`
- Starting commit: `f54e27e76235d232c796714bf519be1f850ca8fa`
- Final commit: HEAD of branch `feat/mvp0-foundation-baseline`
- Python version: 3.12.10
- Operating system: Windows 11 (tested on local and GitHub Actions Ubuntu 24.04 runners)
- Environment: Python 3.12 virtual environment (`requirements-core.txt` and `requirements-dev.txt`)

## Repository integrity
- [x] Working tree reviewed before changes
- [x] Starting commit recorded
- [x] Evaluation imports resolve to this repository
- [x] Dependency mirror check passed
- [x] Documentation contract check passed
- [x] Evaluation dataset contract passed

## Verification
- [x] Evaluation package import tests passed
- [x] Evaluation runner tests passed
- [x] All four quality gates passed
- [x] Complete pytest suite passed
- [x] Coverage threshold met
- [x] Ruff passed
- [x] Wheel built successfully
- [x] Installed-package smoke test passed
- [x] Deployment configuration checks passed
- [x] Dependency audit passed
- [x] Bandit passed
- [x] Gitleaks passed or findings reviewed under the approved exception policy

## Results

### 1. Evaluation Package Imports Regression
- Command: `python -m pytest tests/test_evaluation_package_imports.py -q`
- Exit Code: 0
- Details: Verified `evaluation` package resolves to repository root and all evaluation runner modules (`evaluate_extraction`, `evaluate_packing`, `evaluate_privacy`, `evaluate_retrieval`, `run_all`) import cleanly.

### 2. Evaluation Runner Suite
- Command: `python -m pytest tests/test_evaluation_runner.py -q`
- Exit Code: 0
- Details: All evaluation runner tests passed.

### 3. Quality Benchmark Gates
- Command: `python evaluation/scripts/run_all.py --fail-under-gates`
- Exit Code: 0
- Benchmark Metrics:
  - Extraction Reading Order Kendall Tau: 1.0 (threshold: >= 0.80)
  - Extraction Table Cell F1: 1.0 (threshold: >= 0.90)
  - Context Packing Budget Violations: 0.0 (threshold: == 0.0)
  - Context Packing Minimum Approximation Ratio: 0.8571 (threshold: >= 0.50)
  - Privacy Precision: 1.0 (threshold: >= 0.85)
  - Privacy Recall: 1.0 (threshold: >= 0.85)
  - Privacy Secret Leakage Rate: 0.0 (threshold: == 0.0)
  - Retrieval MRR: 1.0 (threshold: >= 0.70)
  - Retrieval Recall@5: 0.9231 (threshold: >= 0.75)
  - Retrieval Abstention Accuracy: 1.0 (threshold: >= 0.90)
- Artifact Location: `evaluation/reports/baseline_report.json`

### 4. Complete Test Suite & Coverage
- Command: `pytest tests/ --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=75`
- Exit Code: 0 (verified in GitHub Actions CI runs [40444760187](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/runs/40444760187) and [40444760422](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/runs/40444760422))
- Coverage: >= 80% (exceeds required 75% threshold)

### 5. Static Analysis & Linting
- Command: `python -m ruff check src tests scripts dashboard`
- Exit Code: 0
- Details: All style and correctness checks passed.

### 6. Packaging & Distribution Build
- Command: `python -m build --wheel`
- Exit Code: 0
- Artifact: `dist/aegis_docintel-0.1.0a1-py3-none-any.whl`

### 7. Application & Evaluation Smoke Verification
- Commands:
  - `python -c "from src.main import app; print(app.title)"` (Output: `AEGIS-DocIntel`, Exit Code: 0)
  - `python -c "from evaluation.scripts.run_all import run_all; print(callable(run_all))"` (Output: `True`, Exit Code: 0)

### 8. Repository Contracts
- Commands:
  - `python scripts/check_dependency_sync.py`: OK (6 requirements files match `pyproject.toml`)
  - `python scripts/check_docs_claims.py`: OK (Rules R1–R6 passed)
  - `python scripts/validate_mvp_dataset.py`: PASSED (53/53 contract cases verified)

### 9. Security & Secret Scan
- Commands:
  - `bandit -r src dashboard scripts -ll`: Zero high/medium findings, Exit Code: 0
  - `pip-audit --requirement requirements-core.txt`: No known vulnerabilities found, Exit Code: 0
  - `gitleaks detect --verbose`: Scanned complete git history, zero leaks found, Exit Code: 0

## Outstanding issues
None. All P0 blockers from GitHub CI have been diagnosed, resolved, and verified locally and via canonical CI workflows.

## Decision
- [x] MVP 0 ACCEPTED
- [ ] MVP 0 BLOCKED
