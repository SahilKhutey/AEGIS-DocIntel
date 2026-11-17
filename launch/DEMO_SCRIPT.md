# AEGIS-DocIntel — 3-Minute Demo Script & Video Storyboard

This script outlines the exact sequence for a 60–90 second Product Hunt product video or a 3-minute live evaluation walkthrough.

---

## Storyboard Overview

| Timestamp | Step & Screen | Narrator / Action | Visitor Observes |
| :--- | :--- | :--- | :--- |
| **0:00–0:20** | **Home Dashboard** (`/`) | "Welcome to AEGIS-DocIntel. Today we're showing how complex technical documents become verifiable AI intelligence in under 3 minutes." | Clean workspace overview, zero setup required, preloaded synthetic technical specifications ready. |
| **0:20–0:50** | **Document Workspace** (`/documents`) | "Let's open our first document: the NHA-100 Hardware Specification. Notice that AEGIS didn't just dump raw text." | Document structure view: layout-aware reading order DAG, bounding box coordinates, and extracted table matrix (frequency, throughput, TDP). |
| **0:50–1:20** | **Ask AEGIS (Evidence RAG)** (`/ask`) | "Now we ask a direct engineering question: *'What is the peak FP16 tensor throughput of the NHA-100 accelerator?'*" | Instant response: "Rated at 450 TFLOPS FP16 at 1.85 GHz." Every sentence links directly to an inline citation badge. |
| **1:20–1:50** | **Citation Inspection** (`/ask`) | "Clicking citation [1] opens the Evidence Inspector." | Side panel displays the exact source passage in Section 2, page 1, highlighting the grounding phrase. Zero hallucination. |
| **1:50–2:20** | **Cross-Document Compare** (`/compare`) | "Now the real test. What happens when an engineering revision changes key numbers? Let's select Hardware Spec v1.0 and v2.0." | The comparison engine highlights contradictions: Throughput upgraded from 450 TFLOPS to 620 TFLOPS; TDP elevated from 220W to 285W. Preserves 128 MB cache invariant. |
| **2:20–2:50** | **Mathematical Invariants** (`/mathematics`) | "Under the hood, AEGIS compiles context using submodular knapsack optimization with provable $(1 - 1/e)/2$ approximation guarantees." | Interactive visualization of reading order DAGs, graph Laplacians, and token budget compression savings. |
| **2:50–3:00** | **Governance & Audit** (`/governance/audit`) | "Every extraction, query, and decision is cryptographically chained using SHA-256 hashes. Verifiable AI you can stake enterprise decisions on." | Append-only audit log, genesis hash `000...000`, tamper verification badge. Call to action: "Try the live demo now." |

---

## Demo Script Prompts & Questions

### Query 1: Fact Retrieval with Citations
- **Question:** "What is the peak FP16 tensor throughput of the NHA-100 hardware accelerator?"
- **Expected Answer:** "Rated at 450 TFLOPS FP16 at a base operating frequency of 1.85 GHz."
- **Citation:** `aegis_neural_hardware_spec_v1.txt`, Section 2.

### Query 2: Invariant Check across Revisions
- **Question:** "What is the capacity of the submodular context packing cache across hardware revisions?"
- **Expected Answer:** "Across both v1.0 and v2.0 specifications, the submodular context packing cache is an invariant fixed at 128 MB SRAM per compute tile."
- **Citation:** Both v1.0 and v2.0 Section 2.

### Query 3: Deliberate Abstention (Zero Hallucination)
- **Question:** "What cloud backup regions and secondary disaster recovery zones are supported?"
- **Expected Answer:** "The provided documents do not contain evidence regarding cloud backup regions." (Model abstains cleanly without hallucinating false AWS or Azure regions).

### Comparison Test: Hardware Revision Contradictions
- **Input:** Document `doc-seed-hw-v1` vs `doc-seed-hw-v2`.
- **Output:**
  - Conflict 1: Peak Compute: `450 TFLOPS` (v1) vs `620 TFLOPS` (v2)
  - Conflict 2: Operating Frequency: `1.85 GHz` (v1) vs `2.20 GHz` (v2)
  - Conflict 3: TDP: `220 Watts` (v1) vs `285 Watts` (v2)
  - Invariant 1: Context Cache: `128 MB SRAM` (both)
  - Invariant 2: Compliance: `ISO 26262 ASIL-B` (both)
