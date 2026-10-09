# Contributing & Piloting AEGIS-DocIntel

Thank you for trying out AEGIS-DocIntel and participating in our pilot evaluation!

This document sets transparent guidelines for external pilot participants and codebase contributors.

---

## 1. Pilot Evaluation Guidelines

If you are evaluating this project as an external pilot developer or team:

1. **Start with the Cold-Start Install:**
   Please test the fresh installation sequence exactly as documented in the [Installation Guide](installation.md) before anything else. If any step fails or requires an unmentioned dependency, please file a bug report immediately.
2. **Choose the Right Scope:**
   - **Recommended:** Start with [`aegis-docprep`](docprep.md) (`pip install aegis-docprep`) if you need focused pre-LLM primitives (PII redaction, submodular context packing, spatial reading-order extraction). It has a single dependency (`numpy`) and integrates cleanly with LangChain and LlamaIndex.
   - Use the full monorepo only if you need the full REST API or the 16-domain mathematical framework.
3. **Use Structured Feedback Channels:**
   - For unexpected exceptions or installation failures: Use the GitHub Bug Report Template.
   - For pilot usage feedback and accuracy evaluations: Use the GitHub Pilot Feedback Template.
4. **Consult What's Actually Verified:**
   Review [Status & 16-Phase Journey](status.md) to understand current verified capabilities versus known architectural gaps.

---

## 2. Development Setup

Follow the tiered installation structure:

```bash
# 1. Clone repository
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel

# 2. Create isolated virtual environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install core runtime and development tooling
pip install -r requirements-core.txt -r requirements-dev.txt

# 4. Run tests locally
pytest tests/
```

---

## 3. Branch Protection & CI Requirements

All pull requests targeting `main` and `master` must satisfy automated GitHub Actions CI gates:
- **`lint`**: Code formatting and quality via `ruff check src tests` and `mypy`.
- **`test`**: Full unit test suite with coverage enforcement ($\ge 75\%$).
- **`security`**: Static analysis (`bandit`), dependency vulnerability scan (`pip-audit`), and secret leak detection.
- **`openapi-drift`**: Automated check ensuring `openapi.json` matches FastAPI application routes.

---

## 4. Coding Standards

- **Docstring Integrity**: Maintain clear, descriptive docstrings.
- **Error Handling**: Avoid bare `except: pass` blocks (discovered in Phase 9 to cause silent failures). Always log exceptions or handle explicit exception types.
- **No Unrun Assertions**: Only assert behaviors covered by automated unit tests or verified benchmarks.
