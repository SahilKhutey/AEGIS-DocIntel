# AEGIS-DocIntel Release Notes — Version 1.0.0-beta.1

**Release Date:** 2026-11-19  
**Target Platform:** Windows x64  
**Channel:** Beta Evaluation Release  

---

## Highlights of this Release

### 1. Spatial Layout & Kahn DAG Reading Order
Replaces simplistic text-dump chunking with full coordinate-aware layout recovery. Multi-column academic papers, two-column financial balance sheets, and margin notes are correctly ordered using Kahn's topological DAG algorithm with deterministic tie-breaking.

### 2. Submodular Knapsack Context Optimization
Provides mathematical assurance that retrieved evidence fits model context budgets with provable $(1 - 1/e)/2 \approx 0.316$ facility-location coverage bounds. Eliminates silent truncation of critical clauses.

### 3. Coordinate-Grounded Citations
Every generated answer includes clickable citation badges that resolve to exact bounding-box coordinates on the original document page.

### 4. Cross-Document Comparison
Compare multiple document revisions or contract drafts to automatically surface conflicting clauses, numerical modifications, and omitted sections.

### 5. Ed25519 Cryptographic Licensing & Device Binding
Hardware challenge-response device activation with server-side atomic quota enforcement and zero-leak boundary packaging.
