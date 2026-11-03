# AEGIS-DocIntel Software License & SBOM Architecture

## 1. Dual-Licensing Model
- **Open-Core Engine (`aegis-docprep`)**: Apache License, Version 2.0 (Permissive).
- **Full Platform Engine (`aegis-docintel` / AMDI-OS)**: Proprietary Evaluation/Research License.

## 2. Dependency Compliance Summary
- Total packages audited: 84
- Python packages: 66
- NPM packages: 18
- Approved Permissive packages: 83
- Conditional Dual-Licensed packages: 1 (PyMuPDF)
- Prohibited/Viral Copyleft packages: 0
- Overall status: **COMPLIANT**

## 3. Commercial Distribution Guidance
PyMuPDF is dual-licensed under AGPL-3.0 and Artifex Commercial. For enterprise customers distributing closed-source binaries, an Artifex OEM license is required, or the runtime can be switched to the bundled MIT-licensed fallback pipeline (`pdfplumber` + `pdfminer.six`).
