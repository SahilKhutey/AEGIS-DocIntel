# AEGIS-DocIntel Evaluation Client — Known Limitations

**Version:** 1.0.0-beta.1  
**Distribution Channel:** Beta / Evaluation  

---

## 1. Supported File Formats & Layouts
- **Supported Formats:** Clean text-based PDF (`.pdf`), Microsoft Word (`.docx`), Plain Text (`.txt`).
- **Unsupported / Experimental Formats:**
  - Password-protected, encrypted, or DRM-locked files are rejected at the intake gate.
  - Pure raster scans with low DPI (< 150 DPI) or heavy handwriting require external OCR pre-processing.
  - Complex vector CAD blueprints and multi-layer SVG diagrams are not parsed for textual geometry.

---

## 2. Evaluation Boundaries & Quotas
- **Concurrent Active Documents:** Maximum of 5 documents in active evaluation library.
- **Max File Size:** 10 MB per file.
- **Session Query Quota:** 20 analytical queries per evaluation token.
- **Device Binding:** 1 active Windows workstation per license key.

---

## 3. Platform & Browser Scope
- **Operating System:** Windows x64 only for the initial evaluation beta release. macOS and Linux native packages are scheduled for future development phases.
- **Offline Capabilities:** Offline document reading and cached inspection are available; analytical LLM question answering requires an active HTTPS connection to the evaluation gateway.
