# AEGIS-DocIntel — Product Walkthrough Recording Script

**Workstream:** `launch/product-hunt/assets/video`  
**Phase:** `PROT-FINAL-09`  

---

## 1. Recording Setup & Standards
- **Resolution:** 1920 x 1080 (1080p, 60fps)
- **Software:** OBS Studio (Lossless capture, 60fps)
- **Audio:** Crisp narration, pop filter, normalized to -14 LUFS.
- **Data Safety:** Exclusively use the unencumbered synthetic evaluation corpus (`demo/seed/documents/`).
- **No Mocking:** Record the real live running application on `localhost:3000` / gateway port `8000`.

---

## 2. Voiceover & Action Script

### [00:00 - 00:08] Introduction: The Problem
> **Voice:** *"Every week, researchers and analysts spend hours reading dense technical reports, cross-referencing multi-page specs, and verifying conflicting data across revisions."*  
> **Screen:** Screen displays three overlapping PDF viewers with dense hardware schematics and tables.

### [00:08 - 00:18] Product Overview
> **Voice:** *"AEGIS-DocIntel was built to solve this. It's a document intelligence workbench combining structural parsing, submodular context packing, and grounded retrieval."*  
> **Screen:** Switch to browser window showing the AEGIS home workspace, with clean typography, sidebar navigation, and live system status.

### [00:18 - 00:32] Ingestion & Reading Order
> **Voice:** *"When you upload a document, AEGIS doesn't just strip characters. It uses spatial Kahn DAG algorithms to preserve table headers, column flows, and hierarchical sections."*  
> **Screen:** Upload `aegis_neural_hardware_spec_v2.txt`. Parser shows "Parsing layout... Building reading order DAG... Extracting heading hierarchy... Complete."

### [00:32 - 00:47] Grounded Coordinate Retrieval
> **Voice:** *"In Ask AEGIS, every retrieved answer comes with verified bounding-box citations. Click any citation to inspect the exact coordinates in the original document."*  
> **Screen:** Submits query: "What is the cache memory size and memory bandwidth?" Answer renders: "128 MB cache with 1.2 TB/s bandwidth [Citation: Page 2, Bounding Box (42, 110, 280, 145)]."

### [00:47 - 01:00] Cross-Document Comparison
> **Voice:** *"Need to compare versions? Select two documents to generate a structured discrepancy matrix that immediately identifies changed metrics and conflicting claims."*  
> **Screen:** Side-by-side comparison view displays v1 vs v2 with highlighted delta rows in amber and emerald.

### [01:00 - 01:15] Outro & Call to Action
> **Voice:** *"AEGIS-DocIntel is now available in controlled evaluation. Download the package, test it on your documents, and help us shape the future of document intelligence."*  
> **Screen:** Evaluation portal with download button, Ed25519 signature verification pill, and community links.
