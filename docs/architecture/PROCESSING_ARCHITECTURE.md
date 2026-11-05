# Processing Architecture

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## Pipeline Mechanics
- **OCR Engine**: Tesseract/EasyOCR fallback with deterministic character confidence scoring.
- **Layout Engine**: Bounding box coordinate normalization with 12 region categories.
- **Reading Order**: Topological sort driven by geometric heuristics and reading order graph.
- **Table Reconstruction**: Grid coordinate mapping, row/column spanning detection, and TEDS evaluation.
