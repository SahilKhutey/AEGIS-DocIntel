# PROT-01: Dependency Licensing & Third-Party Obligations Audit

**Document:** 04_DEPENDENCY_LICENSE_AUDIT.md  
**Audit Objective:** Catalog direct and transitive dependencies across Python and Node.js ecosystems, identify license obligations, and ensure complete open-source legal compliance.  

---

## 1. Ecosystem License Summary

The platform interacts with 34 distinct direct runtime dependencies cataloged in `distribution/audit/dependency_license_register.csv`:

| License Family | Count | Key Packages | Compliance Obligations | Compatibility Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Apache License 2.0** | 7 | `aegis-docprep`, `cryptography`, `prometheus-client`, `bcrypt`, `openai` | Retain copyright notice, Apache-2.0 license copy, and state changes. | **COMPATIBLE** |
| **MIT License** | 15 | `fastapi`, `pydantic`, `next`, `react`, `react-dom`, `zod`, `tiktoken`, `anthropic`, `python-docx` | Include standard copyright notice and permission text. | **COMPATIBLE** |
| **BSD 2/3-Clause** | 8 | `starlette`, `uvicorn`, `numpy`, `scipy`, `networkx`, `scikit-learn`, `nginx` | Retain BSD copyright notice and disclaimer in documentation. | **COMPATIBLE** |
| **ISC / HPND** | 2 | `lucide-react`, `pillow` | Permissive notice attribution. | **COMPATIBLE** |
| **AGPL-3.0 / Commercial** | 1 | `pymupdf` (fitz) | Strong copyleft if distributed over network. Must be strictly isolated or licensed commercially. | **RESTRICTED / CLOUD ONLY** |
| **GPL-2.0 / 3.0** | 1 | `poppler-utils` (system binary) | Strong copyleft. Kept strictly on server CLI boundary; not linked into downloadable client package. | **RESTRICTED / CLOUD ONLY** |

---

## 2. High-Risk Copyleft Dependency Analysis

### A. PyMuPDF (AGPL-3.0 / Commercial)
- **Nature:** High-performance PDF parser and text extractor.
- **Risk:** AGPL-3.0 requires making all source code available to users interacting with the software over a network if modified.
- **Mitigation & Compliance:**
  1. PyMuPDF is **NOT** bundled into the downloadable demo package.
  2. In the cloud backend, it is either licensed under Artifex commercial terms or isolated across a clean inter-process REST/CLI boundary within `aegis-docprep`.
  3. No copyleft infection reaches the proprietary sheaf topology or context packing engines.

### B. Poppler-Utils (`pdftotext`, `pdfimages` — GPL-2.0/3.0)
- **Nature:** System command-line utilities used for document layout rasterization.
- **Risk:** Linking against libpoppler can trigger GPL viral obligations.
- **Mitigation:**
  1. Executed exclusively as independent subprocesses via command-line interface.
  2. Subprocess invocation does not create a derivative work under established open-source legal doctrine.
  3. Excluded from the downloadable client package.

---

## 3. Third-Party Notice Attribution Delivery

All third-party libraries incorporated into the client evaluation package (Next.js, React, TailwindCSS, Lucide, Cryptography, Nginx) are formally attributed in:
- `distribution/demo-edition/THIRD-PARTY-NOTICES.md`
- Automated test `SEC-DEMO-017` verifies that this file exists in the bundle and includes all required attributions.
