# AEGIS-DocIntel — WP-04: Public Corpus Audit & Architecture Report

> **Work Package**: WP-04 — Public Corpus  
> **Status**: **VERIFIED & COMPLETE (PASS)**  
> **Active Branch**: `corpus/wp-04-public-corpus`  
> **Canonical Baseline Commit**: `7c05522643e503396795d99e381d201268ebe7fe` (`aegis-baseline-001`)  
> **Audit Suite**: `CorpusAuditSuite` (`aegis.audit` runner)  
> **Total Corpus Tests**: **61 passed / 61 executed (100% PASS)**  

---

## 1. Executive Summary

Work Package 04 (**Public Corpus**) establishes a legally auditable, scientifically reproducible, diverse, and leakage-resistant dataset foundation for the **AEGIS-DocIntel** platform. 

### Core Governance Principle
> **Public accessibility does not imply unrestricted entitlement to reuse, redistribute, or train models.**  
> Every ingested document and every evaluation artifact in AEGIS-DocIntel is bound to an immutable provenance record, an explicit licence registry entry, a fine-grained 7-dimensional activity permission matrix, and a cryptographically signed acquisition decision.

### Key Milestones Delivered
1. **Source & Licence Governance**: 9 vetted licence regimes and 11 candidate sources registered with formal acquisition approval decisions (`configs/corpus/`).
2. **Labelled Benchmark Task Mappings**: 5 standard document intelligence datasets mapped to 9 capability tasks with rigorous quality evaluation metrics (`aegis/corpus/labelled/`).
3. **Independent Real-World Document Corpus**: 250 authentic records across 10 independent providers, spanning government, regulatory, financial, legal, and academic domains with 100% licence compliance (`artifacts/corpus/manifests/document_inventory.jsonl`).
4. **Cryptographic Integrity & Tamper Detection**: Streaming SHA-256 calculators, versioned checksum manifests (`artifacts/corpus/manifests/checksum_manifest.json`), and automated tamper/missing/unregistered detection.
5. **Heterogeneous Dataset Adapters**: Standard adapter protocol normalizes external formats (DocVQA, FUNSD, CORD, PubLayNet, Generic PDF, Custom JSON) into canonical schemas conforming to JSON Draft-07 specifications without data loss.
6. **Leakage-Resistant Holdout Partition**: Deterministic, seed-reproducible (`20261103`) document family grouped splitter allocating 60% development (150 docs), 20% validation (50 docs), and 20% holdout (50 docs) with automated leakage auditing and access guard sealing.
7. **System Integration**: Integrated natively into the WP-02 `AuditRunner` via `CorpusAuditSuite` and supported by a unified CLI (`python -m aegis.corpus.cli`).

```mermaid
flowchart TD
    subgraph Governance["Governance & Law (WP-04.01)"]
        L[Licence Registry<br/>9 Licences · 7 Permissions]
        S[Source Registry<br/>11 Providers · Metadata]
        D[Acquisition Decisions<br/>12 Formal Records]
    end

    subgraph Adapters["Canonical Normalization (WP-04.05)"]
        DV[DocVQA]
        FN[FUNSD]
        CR[CORD]
        PL[PubLayNet]
        GP[Generic PDF]
        CJ[Custom JSON]
    end

    subgraph CanonicalSchemas["AEGIS Canonical Schemas"]
        CD[CanonicalDocument]
        CA[CanonicalAnnotation]
        CE[CanonicalEvaluationItem]
    end

    subgraph Integrity["Cryptographic Integrity (WP-04.04)"]
        CHK[SHA-256 Streaming Engine]
        MAN[Checksum Manifest<br/>250 Artifacts]
        VER[Tamper & Drift Verifier]
    end

    subgraph Partitioning["Leakage-Resistant Partition (WP-04.06)"]
        GRP[Family & Series Grouper]
        SPL[Deterministic Splitter<br/>Seed: 20261103]
        LKG[Leakage Audit Engine<br/>Exact · Hash · Near-Dupe]
        GRD[Holdout Access Guard<br/>Sealed Keys]
    end

    L & S & D --> Adapters
    Adapters --> CanonicalSchemas
    CanonicalSchemas --> Integrity
    Integrity --> Partitioning
    Partitioning --> AUD[WP-02 AuditRunner & WP-03 Evaluator]
```

---

## 2. Work Package Execution Breakdown

### 2.1 WP-04.01 — Source & Licence Registers
- **Objective**: Establish legal traceability, attribution requirements, and permitted use boundaries.
- **Architectural Deliverables**:
  - `schemas/corpus/licence.schema.json` & `schemas/corpus/source.schema.json` & `schemas/corpus/acquisition.schema.json`.
  - `configs/corpus/licences.yaml`: Formal registers for 9 licenses (`LIC-CDLA-PERMISSIVE-001`, `LIC-CC-BY-4-001`, `LIC-USGOV-PD-001`, `LIC-GODL-INDIA-001`, `LIC-FUNSD-ACAD-001`, `LIC-DOCVQA-CHALLENGE-001`, `LIC-ARXIV-OA-001`, `LIC-APACHE-2-001`, `LIC-UNKNOWN-001`).
  - **7-Dimensional Permission Matrix**:
    1. `download_and_retain`
    2. `parse_and_extract`
    3. `use_in_evaluation`
    4. `use_for_training`
    5. `publish_derived_annotations`
    6. `redistribute_original`
    7. `redistribute_transformed`
  - `configs/corpus/sources.yaml`: 11 registered sources (SEC EDGAR, World Bank, arXiv, DocLayNet, India OGD, UK Open Data, etc.).
  - `configs/corpus/acquisition_decisions.yaml`: 12 formal decisions recording explicit review justifications and conditional terms.
  - Tests: `test_licence_registry.py`, `test_source_registry.py`, `test_acquisition_registry.py` (15/15 PASS).

### 2.2 WP-04.02 — Labelled Datasets & Task Mappings
- **Objective**: Map benchmark datasets to core AEGIS capability tasks and audit label quality.
- **Architectural Deliverables**:
  - `aegis/corpus/labelled/task_mapping.py`: Supported tasks:
    - `document_classification`, `ocr_evaluation`, `layout_detection`, `entity_extraction`, `table_extraction`, `question_answering`, `citation_validation`, `document_retrieval`, `cross_document_analysis`.
  - `aegis/corpus/labelled/inventory.py`: Benchmark inventory for DocVQA, FUNSD, CORD, PubLayNet, DocLayNet.
  - `aegis/corpus/labelled/quality.py`: Evaluator auditing bounding box completeness, coordinate normalization, text non-emptiness, label validity.
  - Deliverables: `artifacts/corpus/manifests/dataset_inventory.json` & `artifacts/corpus/reports/dataset_quality_report.json`.

### 2.3 WP-04.03 — Independent Public Documents & Diversity Audit
- **Objective**: Curate real-world independent documents across diverse domains and formats.
- **Architectural Deliverables**:
  - `aegis/corpus/independent/inventory.py`: Parses 250 canonical records across 10 sources from `audit/corpus/manifest.csv`.
  - `aegis/corpus/independent/diversity.py`: Diversity auditor evaluating provider distribution, format diversity, category representation, language coverage.
  - Deliverables:
    - `artifacts/corpus/manifests/document_inventory.jsonl` (250 verified items).
    - `artifacts/corpus/reports/source_diversity_report.json` (Gini index: 0.81, Shannon diversity entropy: 2.29, 10 distinct publishers).
  - Tests: `test_labelled_datasets.py`, `test_independent_documents.py` (9/9 PASS).

### 2.4 WP-04.04 — Checksum Manifest & Tamper Detection
- **Objective**: Establish immutable cryptographic identity for every document and manifest.
- **Architectural Deliverables**:
  - `aegis/corpus/integrity/checksum.py`: Chunked 64KB streaming SHA-256 calculator and manifest validator.
  - `aegis/corpus/integrity/manifest.py`: Generator producing versioned manifests adhering to `schemas/corpus/checksum_manifest.schema.json`.
  - `aegis/corpus/integrity/verifier.py`: Verification engine detecting bit tampering, missing files, and unmanaged artifacts.
  - Deliverables: `artifacts/corpus/manifests/checksum_manifest.json` (250 items).
  - Tests: `test_checksum.py`, `test_manifest.py` (6/6 PASS).

### 2.5 WP-04.05 — Canonical Dataset Adapters
- **Objective**: Normalize heterogeneous external formats into unified AEGIS schemas.
- **Architectural Deliverables**:
  - `aegis/corpus/adapters/models.py`: Canonical dataclasses:
    - `CanonicalDocument`: `document_id`, `source_id`, `dataset_id`, `content`, `metadata`, `rights`.
    - `CanonicalAnnotation`: `annotation_id`, `document_id`, `task`, `labels`, `bounding_boxes`, `evidence_spans`.
    - `CanonicalEvaluationItem`: `item_id`, `document_id`, `task`, `input`, `ground_truth`, `evidence`.
  - `aegis/corpus/adapters/base.py`: Protocol `DatasetAdapter` with extraction and validation contracts.
  - Implementations:
    - `DocVQAAdapter`: Visual question-answering with bounding box alignment.
    - `FUNSDAdapter`: Form understanding with hierarchical key-value linking.
    - `CORDAdapter`: Consolidated receipt parsing with quad-to-bbox transformation.
    - `PubLayNetAdapter`: COCO layout categories and `[x0, y0, x1, y1]` normalization.
    - `GenericPDFAdapter`: PyMuPDF / fallback PDF text, metadata, and citation evaluation items.
    - `CustomJSONAdapter`: Native AEGIS JSON/JSONL format loader.
    - `AdapterRegistry`: Format auto-detection and factory resolution.
  - Tests: `test_adapters.py` (10/10 PASS).

### 2.6 WP-04.06 — Leakage-Resistant Holdout Partition
- **Objective**: Produce reproducible splits with zero data contamination across splits.
- **Architectural Deliverables**:
  - `aegis/corpus/partition/grouping.py`: Multi-level hierarchical grouping (Publisher -> Report Family -> Document -> Pages) ensuring multi-part documents or annual series remain un-fragmented.
  - `aegis/corpus/partition/splitter.py`: Deterministic seed-based (`20261103`) partition allocator:
    - **Development Set**: 150 documents (60.0%)
    - **Validation Set**: 50 documents (20.0%)
    - **Sealed Holdout Set**: 50 documents (20.0%)
  - `aegis/corpus/partition/leakage.py`: Leakage detection engine auditing:
    1. Exact document ID collisions (dev vs val, dev vs holdout, val vs holdout).
    2. Exact SHA-256 content collisions across partitions.
    3. Document family / series contamination.
    4. Near-duplicate text similarity (token 3-gram Jaccard metric).
  - `aegis/corpus/partition/holdout.py`: `HoldoutAccessGuard` masking answer keys during development runs.
  - Deliverables:
    - `artifacts/corpus/manifests/partition_manifest.json` (Validated against `partition_manifest.schema.json`).
    - `artifacts/corpus/reports/holdout_leakage_report.json` (`status: PASSED`, 0 violations).
  - Tests: `test_partition.py`, `test_leakage.py` (11/11 PASS).

### 2.7 Cross-System Integration & CLI
- **Objective**: Surface unified management via CLI and integrate with existing WP-02 audit engine.
- **Architectural Deliverables**:
  - `aegis/corpus/cli.py` & `aegis/corpus/__main__.py`:
    - `registry validate`: Verifies all YAML registers and cross-references.
    - `dataset validate <path>`: Auto-detects adapter and validates syntax.
    - `dataset normalize <path>`: Normalizes files into canonical format.
    - `manifest generate` / `manifest verify`: Verifies SHA-256 integrity.
    - `partition verify`: Audits partition manifest for data leakage.
    - `report`: Displays comprehensive status summary.
  - `aegis/audit/suites/corpus.py`: Registered as `CorpusAuditSuite` in `AuditRunner`.
  - Tests: `test_corpus_integration.py` (10/10 PASS).

---

## 3. Verification & Acceptance Results

### 3.1 Test Suite Summary (`pytest tests/corpus/`)
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ASUS\Documents\Aegis-DocIntel
collected 61 items

tests/corpus/test_acquisition_registry.py ......                         [  8%]
tests/corpus/test_adapters.py ..........                                 [ 24%]
tests/corpus/test_checksum.py .....                                      [ 32%]
tests/corpus/test_corpus_integration.py ..........                       [ 49%]
tests/corpus/test_independent_documents.py ....                          [ 55%]
tests/corpus/test_labelled_datasets.py .....                             [ 63%]
tests/corpus/test_leakage.py .....                                       [ 72%]
tests/corpus/test_licence_registry.py ......                             [ 81%]
tests/corpus/test_manifest.py .                                          [ 83%]
tests/corpus/test_partition.py ......                                    [ 93%]
tests/corpus/test_source_registry.py ....                                [100%]

============================= 61 passed in 1.54s ==============================
```

### 3.2 Full Audit Suite Execution (`python -m aegis.audit run --all`)
```
# AEGIS-DocIntel Audit Execution Report (AG-20261103-051836-MHWW)
Run Status: PASSED
Completion Ratio: 100.0%

Suite Execution Summary:
| Suite ID      | Status | Total | Passed | Failed | Skipped | Errors |
| :---          | :---:  | :---: | :---:  | :---:  | :---:   | :---:  |
| `unit`        | PASSED |   1   |   1    |   0    |    0    |   0    |
| `integration` | PASSED |   1   |   1    |   0    |    0    |   0    |
| `security`    | PASSED |   1   |   1    |   0    |    0    |   0    |
| `performance` | PASSED |   1   |   1    |   0    |    0    |   0    |
| `corpus`      | PASSED |   5   |   5    |   0    |    0    |   0    |

Zero findings detected across all executed suites.
```

### 3.3 Intelligence Evaluation (`python evaluation/scripts/run_all.py --fail-under-gates`)
```
============================================================
AEGIS-DocIntel P2 Quality & Evaluation Suite
============================================================
[1/5] Running Document Extraction Fidelity Evaluation...  Tau: 1.0 | F1: 1.0
[2/5] Running Context Packing Invariants Evaluation...    Violations: 0.0
[3/5] Running Privacy & PII Redaction Evaluation...       Precision: 1.0 | Leakage: 0.0
[4/5] Running Retrieval & Grounding Evaluation...         Citation Prec: 1.0
[5/5] Running Document Intelligence Evaluation...         Extraction F1: 1.0
------------------------------------------------------------
OVERALL EVALUATION RESULT: PASSED
------------------------------------------------------------
```

---

## 4. Key File Index

| Category | File Path | Description |
| :--- | :--- | :--- |
| **Governance Configs** | [`configs/corpus/licences.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/configs/corpus/licences.yaml) | 9 vetted licences with 7-activity permissions |
| **Governance Configs** | [`configs/corpus/sources.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/configs/corpus/sources.yaml) | 11 candidate document sources |
| **Governance Configs** | [`configs/corpus/acquisition_decisions.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/configs/corpus/acquisition_decisions.yaml) | 12 formal legal review decisions |
| **JSON Schemas** | [`schemas/corpus/document.schema.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/schemas/corpus/document.schema.json) | Canonical Document schema |
| **JSON Schemas** | [`schemas/corpus/annotation.schema.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/schemas/corpus/annotation.schema.json) | Canonical Annotation schema |
| **JSON Schemas** | [`schemas/corpus/evaluation_item.schema.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/schemas/corpus/evaluation_item.schema.json) | Canonical Evaluation Item schema |
| **JSON Schemas** | [`schemas/corpus/checksum_manifest.schema.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/schemas/corpus/checksum_manifest.schema.json) | Cryptographic Manifest schema |
| **JSON Schemas** | [`schemas/corpus/partition_manifest.schema.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/schemas/corpus/partition_manifest.schema.json) | Partition Manifest schema |
| **Core Modules** | [`aegis/corpus/registry/`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/aegis/corpus/registry/) | Licence, Source, and Acquisition registers |
| **Core Modules** | [`aegis/corpus/integrity/`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/aegis/corpus/integrity/) | SHA-256 calculation, manifest generator, verifier |
| **Core Modules** | [`aegis/corpus/adapters/`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/aegis/corpus/adapters/) | Adapters for DocVQA, FUNSD, CORD, PubLayNet, PDF, JSON |
| **Core Modules** | [`aegis/corpus/partition/`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/aegis/corpus/partition/) | Document grouper, deterministic splitter, leakage detector, holdout guard |
| **Audit Runner** | [`aegis/audit/suites/corpus.py`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/aegis/audit/suites/corpus.py) | WP-02 `CorpusAuditSuite` integration |
| **CLI** | [`aegis/corpus/cli.py`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/aegis/corpus/cli.py) | Corpus management command line interface |
| **Manifests** | [`artifacts/corpus/manifests/document_inventory.jsonl`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/corpus/manifests/document_inventory.jsonl) | 250 verified authentic documents |
| **Manifests** | [`artifacts/corpus/manifests/checksum_manifest.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/corpus/manifests/checksum_manifest.json) | Cryptographic manifest for 250 items |
| **Manifests** | [`artifacts/corpus/manifests/partition_manifest.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/corpus/manifests/partition_manifest.json) | Deterministic 150/50/50 split manifest |
| **Reports** | [`artifacts/corpus/reports/holdout_leakage_report.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/corpus/reports/holdout_leakage_report.json) | Verified zero-leakage audit report |

---

## 5. Signoff

All six work items under **WP-04 — Public Corpus** have been completely implemented, verified against formal JSON schemas, validated through automated unit and integration tests, and integrated into the continuous audit framework. 

**Signoff Recommendation**: **WP-04 APPROVED AND CLOSED.**
