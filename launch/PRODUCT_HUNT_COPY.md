# AEGIS-DocIntel — Product Hunt Launch Copy & Kit

## 1. Listing Metadata

- **Product Name:** AEGIS-DocIntel
- **Tagline:** Turn complex documents into structured, evidence-grounded AI context.
- **Short Description (260 chars max):**
  A mathematical context compiler and document intelligence engine. Extract layout-aware reading order DAGs, pack submodular contexts with provable guarantees, verify 100% of citations, and detect cross-document contradictions.
- **Topics / Categories:**
  `Artificial Intelligence`, `Developer Tools`, `Open Source / Software Engineering`, `Data & Analytics`, `Productivity`
- **Pricing:**
  Free Evaluation & Research / Dual-Licensed (Open-core `aegis-docprep` is Apache 2.0)
- **Primary Website / Live Demo Link:** `https://demo.aegis-docintel.com`
- **GitHub Repository:** `https://github.com/SahilKhutey/AEGIS-DocIntel`

---

## 2. Product Description (Main Body)

Most AI document tools are built on a fragile shortcut: dump unstructured text into an embedding model, hope multi-column tables don't get shredded, and ask an LLM to generate an answer with no proof. When documents contradict each other or contain critical engineering specs, probabilistic models hallucinate.

**AEGIS-DocIntel is built differently.** It is a mathematical context compiler that treats document intelligence as an evidence-grounded engineering pipeline:

### Key Capabilities:
1. **Layout-Aware Reading Order Recovery:** Reconstructs spatial Directed Acyclic Graphs (DAGs) from PDFs and complex Office documents, preserving multi-column reading flow and table matrices without flattening.
2. **Submodular Knapsack Context Packing:** Formulates context engineering as a constrained submodular optimization problem, delivering a provable $(1 - 1/e)/2 \approx 0.316$ knapsack approximation bound that maximizes semantic diversity while cutting token waste.
3. **Traceable Evidence & Citations:** Every assertion in "Ask AEGIS" is linked to exact source passages, page numbers, and bounding boxes. If the source documents lack the answer, AEGIS explicitly abstains instead of inventing facts.
4. **Cross-Document Contradiction Engine:** Automatically compares technical revisions and legal agreements to pinpoint conflicting numerical and semantic claims.
5. **Tamper-Evident SHA-256 Audit Trails:** Chained cryptographic audit records rooted at genesis hash ensure total compliance visibility for SOC 2 and GDPR right-to-erasure workflows.
6. **Self-Hosted & Privacy-First:** Run locally with Docker Compose in minutes. Your proprietary documents never leak to external LLM providers unless explicitly configured by policy.

---

## 3. Maker Introduction Comment (First Comment)

> Hey Product Hunt! 👋
> 
> I'm Sahil, creator of **AEGIS-DocIntel**.
> 
> Over the past year building RAG pipelines and document analyzers, I kept running into the same frustrating reality: naive chunking turns structured engineering PDFs into garbage, and LLMs generate confident answers backed by phantom citations.
> 
> We built AEGIS to bring mathematical rigor to document understanding. Instead of treating text as a flat string, AEGIS treats documents as geometric and topological manifolds:
> - It recovers reading order using spatial topological DAGs.
> - It solves context packing using submodular knapsack algorithms with mathematical approximation guarantees.
> - It enforces 100% citation resolution and zero-hallucination abstention.
> 
> **How to try it today:**
> 1. **Live Hosted Demo:** Visit our live sandbox to explore pre-seeded hardware specs and test cross-document contradiction detection in under 3 minutes—no installation or API keys required.
> 2. **Self-Hosted Docker:** Clone the repo and run `docker-compose -f deploy/docker-compose.demo.yml up` to run your own local instance with full data sovereignty.
> 3. **Standalone Open-Core Package:** `aegis-docprep` is available under Apache 2.0 with zero heavy dependencies (just NumPy) for spatial reading order and context packing.
> 
> We're an alpha-to-MVP stage research platform and we believe in radical transparency: our feature matrix and known limitations are fully published in `STATUS.md`.
> 
> I'd love your feedback, bug reports, and thoughts on what document intelligence should look like. Let me know what you think in the comments! 🚀

---

## 4. Product Hunt Screenshot Plan

1. **Screenshot 1 (Hero / Overview):** Modern Workbench dashboard showing active documents, 3-minute guided tour cards, and operational health metrics.
2. **Screenshot 2 (Inspection):** Document Workspace displaying layout-aware reading order DAG overlay, bounding boxes, and extracted table matrix.
3. **Screenshot 3 (Ask AEGIS):** Evidence-grounded Q&A interface with highlighted inline citation badges and side-by-side Evidence Panel showing exact source passages.
4. **Screenshot 4 (Contradiction Comparison):** Split-view comparing Hardware Spec v1.0 vs v2.0, highlighting the 450 TFLOPS vs 620 TFLOPS conflict with confidence scores.
5. **Screenshot 5 (Mathematical & Audit Invariants):** Visual inspection of submodular knapsack token efficiency curve and cryptographically chained SHA-256 audit log.
