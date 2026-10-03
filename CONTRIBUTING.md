# Contributing to AEGIS-DocIntel

Thank you for your interest in contributing to AEGIS-DocIntel!

---

## 1. Branch Protection & CI Requirements

All contributions to `main` and `master` are governed by automated GitHub Actions CI checks.

### Required Status Checks
Before any pull request can be merged, the following automated jobs must pass:
* **`lint`**: Code style and correctness via `ruff check src tests` and `mypy`.
* **`test (ubuntu-latest, 3.12)`**: Full unit test suite with coverage enforcement ($\ge 70\%$).
* **`test (ubuntu-latest, 3.13)`**: Full unit test suite on Python 3.13.
* **`security`**: Static analysis (`bandit`), dependency vulnerability scan (`pip-audit`), and secret leak prevention (`gitleaks`).

Branches must be kept up-to-date with upstream prior to merge. See repository **Settings → Branches** for the current GitHub enforcement rule.

---

## 2. Development Setup

Follow the tiered installation structure established under Phase 2:

```bash
# 1. Clone repository
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel

# 2. Create isolated virtual environment
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 3. Install core runtime and development tooling
pip install -r requirements-core.txt -r requirements-dev.txt

# 4. Run tests locally
pytest tests/ --ignore=tests/test_multimodal.py
```

---

## 3. Code Standards & Quality Checks

Before committing or opening a PR, ensure local checks pass:

```bash
# Linter check
ruff check src tests

# Test execution with coverage gate
pytest tests/ --ignore=tests/test_multimodal.py --cov=src --cov-fail-under=70
```

---

## 4. Verification & Credibility Standard

In accordance with our [STATUS.md](STATUS.md) and [16-Phase Roadmap](docs/ROADMAP.md), **every claim and metric must be reproducible**. Do not commit mock or unverified audit reports, placeholder signatures, or synthetic performance numbers.
