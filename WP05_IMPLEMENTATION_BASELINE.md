# AEGIS-DocIntel — WP-05: Processing Implementation Baseline

> **Work Package**: WP-05 — Processing  
> **Status**: **BASELINE ASSESSED & PHASE 0 COMPLETE**  
> **Active Branch**: `processing/wp-05-processing`  
> **Parent Baseline Commit**: `2902742` (`docs(corpus): document public corpus and governance`)  
> **Target Package**: `aegis.processing`  

---

## 1. Executive Summary

Work Package 05 (**Processing**) establishes whether AEGIS-DocIntel can reliably transform acquired documents into accurate, structured, traceable, machine-readable representations across:
1. Native & Scanned Text Extraction (OCR, CER, WER, Confidence).
2. Document Layout Detection (Region boundaries, classification, IoU, mAP).
3. Logical Reading Order (Reading-order graphs, topological sequence, Kendall's tau).
4. Table Structural Reconstruction (Row/column grid, spans, merged headers, cell accuracy, TEDS).
5. Field-Level Normalization & Provenance (Deterministic typing, source span traceability, lineage).
6. Malformed & Adversarial Document Resilience (Corrupt files, resource limits, security sandbox).

This baseline audit inventories existing assets, identifies architectural gaps, and specifies the required implementation strategy.

---

## 2. Current-State Architecture & Asset Inventory

### 2.1 PDF Parsing & Native Extraction
- **Existing Asset**: `src/ingestion/pdf_loader.py` (`PDFLoader`)
  - **Engine**: PyMuPDF (`fitz` v1.28.0) and `pdfplumber` (v0.11.10).
  - **Strengths**: Magic-byte sniffing (`%PDF` up to byte 1024), encrypted PDF detection (`EncryptedDocumentError`), basic metadata extraction.
  - **Gaps**: Lacks explicit per-page digital vs scanned classification; fallback to OCR occurs only if total extracted text across the whole document is below threshold rather than per-page.

### 2.2 OCR Engine & Image Processing
- **Existing Asset**: `src/ingestion/ocr_engine.py` (`OCREngine`) & `src/engines/ocr/universal_ocr.py`
  - **Engines**: PyTesseract (v0.3.13), PIL (v12.1.1), OpenCV (`cv2` v4.11.0). (PaddleOCR is not installed in the Windows environment, so graceful fallback to Tesseract/PyMuPDF is required).
  - **Gaps**: Missing quantitative CER/WER evaluation harnesses; confidence score calibration is unrecorded (returns generic or missing values); bounding box coordinate systems are unnormalized.

### 2.3 Layout Analysis
- **Existing Asset**: `src/engines/layout/layout_detector.py` (`LayoutDetector`)
  - **Strengths**: Performs structural block sorting by $(y_0, x_0)$, multi-column gap clustering (`_COLUMN_CLUSTER_GAP = 0.15`), and font-size proxy heading levels.
  - **Gaps**: Evaluates layout without formal COCO/DocLayNet IoU matching, class-aware precision/recall, or mAP metrics; missing visual overlay generation for missed/false-positive regions.

### 2.4 Reading Order Logic
- **Existing Asset**: `evaluation/scripts/evaluate_extraction.py` & `aegis_docprep.reading_order`
  - **Strengths**: Implements Kendall's tau rank correlation calculation (`compute_kendall_tau`).
  - **Gaps**: No explicit reading-order directed graph model; column interleaving detection is unautomated; parent-child heading and caption-figure associations are not formally verified.

### 2.5 Table Extraction & Reconstruction
- **Existing Asset**: `backend/src/multimodal/table_extractor.py` & `tests/test_table_extraction_regression.py`
  - **Strengths**: Defines `TableCell`, `CellType` (`HEADER`, `DATA`, `EMPTY`, `MERGED`), and `TableStructure`.
  - **Gaps**: Missing formal TEDS (Tree Edit Distance for Tables) or GriTS structural metrics; borderless table reconstruction lacks robust alignment evaluation.

### 2.6 Normalization & Field-Level Provenance
- **Existing Asset**: `src/normalization/` (`layout.py`, `ocr.py`) & `src/models/document_object.py`
  - **Strengths**: Normalizes text whitespace and basic block structures.
  - **Gaps**: Lacks strict field-level provenance records linking normalized dates/numbers/currencies back to exact source page, bounding box, rule ID, and original raw unparsed string.

### 2.7 Malformed Document & Security Controls
- **Existing Asset**: `src/ingestion/exceptions.py` & `tests/test_resilience_and_recovery.py`
  - **Strengths**: Raises `DocumentCorruptError`, `EncryptedDocumentError`, `SizeLimitError`.
  - **Gaps**: No isolated worker boundary or process sandboxing; missing explicit timeout enforcement, memory capping, pixel dimension limits, or decompression bomb protection.

---

## 3. WP-04 & WP-02/WP-03 Integration Touchpoints

1. **WP-04 Public Corpus Assets**:
   - 250 authentic multi-domain documents in `artifacts/corpus/manifests/document_inventory.jsonl`.
   - 63 real multi-format PDFs in `production/benchmark-dataset-real/pdf-corpus/` (including rotated, unicode, tables, empty).
   - Labelled ground truth in `audit/corpus/ground-truth/layout_ground_truth_sample.json` and `table_ground_truth_sample.json`.
   - Holdout partition manifest in `artifacts/corpus/manifests/partition_manifest.json`.
2. **WP-02 Audit Runner**:
   - `ProcessingAuditSuite` will be integrated into `aegis.audit.runner` to execute processing validation within the standard audit lifecycle.
3. **WP-03 Manifest-Driven Evaluation**:
   - `configs/evaluation/intelligence.yaml` and `evaluate_extraction.py` will integrate the new processing metrics.

---

## 4. Planned WP-05 Implementation Architecture

```
aegis/
  processing/
    __init__.py
    pipeline.py                     # Central unified document processing pipeline
    models.py                       # Unified Pydantic models conforming to schemas

    validation/
      file_validator.py             # Format, size, page, pixel, and header checks
      resource_limits.py            # Bounded memory, CPU time, and dimension guards

    extraction/
      native_pdf.py                 # Direct PyMuPDF text & character quad extractor
      ocr.py                        # Tesseract / vision OCR engine wrapper
      text_normalizer.py            # Unicode & character set normalization
      confidence.py                 # Confidence scoring and calibration

    layout/
      detector.py                   # Layout region classification & geometry
      regions.py                    # Region taxonomy & bounding box operations
      evaluator.py                  # IoU, class-aware precision/recall, mAP

    reading_order/
      graph.py                      # Directed reading-order relationship graph
      resolver.py                   # Topological & column-aware reading sequence
      evaluator.py                  # Pairwise accuracy & Kendall's tau

    tables/
      detector.py                   # Table bounding box & grid detector
      structure.py                  # Row, column, span, and cell builder
      evaluator.py                  # Cell exact match, grid accuracy, TEDS metric

    normalization/
      text.py                       # Unicode NFC, whitespace, hyphens, ligatures
      dates.py                      # ISO-8601 parser preserving raw strings
      numbers.py                    # Decimals, thousands, currencies
      tables.py                     # Canonical table grid normalizer

    provenance/
      lineage.py                    # End-to-end document & run lineage
      field_trace.py                # Field-level source bounding box traceability
      validator.py                  # Invariant integrity checkers

    security/
      sandbox.py                    # Isolated execution runner with strict limits
      error_classifier.py           # Standardized error codes & status classifications

    benchmarking/
      runner.py                     # WP-05 shared benchmark execution engine
      metrics.py                    # CER, WER, IoU, mAP, Tau, TEDS registry
      reports.py                    # JSON/Markdown benchmark report generators

configs/
  processing/
    pipeline.yaml
    resource_limits.yaml

schemas/
  processing/
    extraction.schema.json
    layout.schema.json
    reading_order.schema.json
    table.schema.json
    provenance.schema.json
    processing_result.schema.json
    benchmark.schema.json
```

---

## 5. Execution Sequence & Acceptance Gates

- **Phase 1**: Establish common JSON Draft-07 schemas and Pydantic models.
- **Phase 2 (WP-05.01)**: OCR and text extraction (CER, WER, confidence calibration).
- **Phase 3 (WP-05.02)**: Layout accuracy (Taxonomy, IoU, mAP, visual overlays).
- **Phase 4 (WP-05.03)**: Reading order (Graph, topological sorting, Kendall's tau).
- **Phase 5 (WP-05.04)**: Table reconstruction (Grid reconstruction, cell accuracy, TEDS).
- **Phase 6 (WP-05.05)**: Field-level normalization and provenance invariants.
- **Phase 7 (WP-05.06)**: Malformed-document security and fuzz resilience.
- **Phase 8**: Benchmark suite execution, latency/resource monitoring, and artifact generation.
- **Phase 9**: `ProcessingAuditSuite` integration and acceptance signoff.
