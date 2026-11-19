# AEGIS-DocIntel Evaluation Client — User Guide

**Version:** 1.0.0-beta.1  

---

## 1. Supported Capabilities

AEGIS-DocIntel provides verifiable document intelligence for complex, layout-dense files:
- **Spatial Layout Parsing:** Preserves multi-column reading flow, headers, footers, and table grids using Kahn's topological DAG algorithm.
- **Submodular Knapsack Context Optimization:** Selects the mathematically optimal evidence subset to answer queries within model token limits without silent truncation.
- **Coordinate-Grounded Citations:** Every factual claim links to exact page numbers and bounding-box coordinates $(x_{min}, y_{min}, x_{max}, y_{max})$.
- **Cross-Document Comparison:** Compares conflicting statements, contract terms, or financial disclosures across multiple document versions.

---

## 2. Core Workflows

### 2.1 Ingesting Documents
- Supported Formats: Text-based PDF (`.pdf`), Microsoft Word (`.docx`), and Plain Text (`.txt`).
- File Size Ceiling: Up to 10 MB per document during evaluation mode.
- Idempotent Uploads: Uploading the exact same document multiple times will not duplicate storage or consume extra quota allowances.

### 2.2 Asking Grounded Questions
1. Navigate to **Ask & Investigate** in the sidebar.
2. Select one or more active documents from your workspace library.
3. Submit a specific analytical question.
4. The intelligence engine retrieves relevant candidates, packs evidence using submodular facility-location coverage, and generates a grounded response.
5. If the document corpus does not contain sufficient evidence to answer, the engine safely abstains rather than inventing answers.

### 2.3 Cross-Document Semantic Comparison
1. Navigate to **Compare Documents**.
2. Select Document A (Base Version) and Document B (Comparison Version).
3. Click **Execute Semantic Diff**.
4. The system highlights modified terms, removed clauses, and numerical discrepancies with side-by-side evidence references.

### 2.4 Data Erasure
1. Select a document in the Document Library and click **Delete**.
2. Deletion cascades immediately: SQLite records, raw byte blobs, vector indices, and memory caches are wiped.
