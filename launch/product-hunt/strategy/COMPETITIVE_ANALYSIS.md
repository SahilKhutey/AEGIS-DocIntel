# AEGIS-DocIntel — Competitive Landscape & Technical Differentiation

**Workstream:** `launch/product-hunt/strategy`  
**Phase:** `PROT-FINAL-09`  

---

## 1. Competitive Category Landscape

```
                     High Structural Understanding
                                  |
                                  |     * AEGIS-DocIntel
                                  |       (DAG Layout + Sheaf Topology)
                                  |
   * Enterprise IDP/OCR           |
     (Textract, Azure DocIntel)   |     * NotebookLM / Heptabase
                                  |       (Consumer Notebook / Research RAG)
----------------------------------+----------------------------------
Single-Doc Naive Extraction       |     Multi-Document Comparative
                                  |
   * ChatPDF / AskYourPDF         |
     (Naive chunking + Chatbot)   |
                                  |
                      Low Structural Understanding
```

---

## 2. Detailed Technical Differentiation

| Feature / Capability | Generic PDF Chatbots (ChatPDF, AskYourPDF) | Enterprise Notebooks (NotebookLM) | Enterprise IDP (Textract, Azure) | AEGIS-DocIntel |
| :--- | :--- | :--- | :--- | :--- |
| **Document Representation** | Flat string dump; loses table layouts and column reading order. | Paragraph-level embedding chunks. | Raw bounding boxes & OCR key-value pairs. | **Spatial Kahn's DAG reading order & hierarchical heading tree.** |
| **Context Packing** | Blind truncation or top-k similarity stuffing. | Proprietary notebook context window. | Developer API only; no context packing. | **Submodular knapsack coverage maximization under token budget.** |
| **Multi-Doc Comparison** | Very limited; single document focus. | Multi-source notebook synthesis. | No out-of-the-box comparative synthesis. | **Topological contradiction & agreement mapping (Sheaf Laplacian).** |
| **Citation Verifiability** | Page numbers only (often hallucinated). | Source document quotes. | Bounding box coordinates only. | **Deterministic bounding box coordinates + cryptographic hash grounding.** |
| **Deployment & Privacy** | Public SaaS; data retained/processed in cloud. | Proprietary cloud silo. | Cloud API requiring cloud infrastructure. | **Zero-leak two-tier architecture: downloadable client + isolated private engine.** |
| **Evaluation Licensing** | Simple email signup; freemium paywall. | Google Account login. | Cloud billing account required. | **Cryptographic Ed25519 licensing with hardware binding & atomic quota holds.** |

---

## 3. Unfair Technical Advantages

1. **Mathematical Rigor:** Rather than relying solely on probabilistic prompt tuning, AEGIS incorporates topological data analysis (Sheaf Theory) and combinatorial optimization (Submodular Knapsack).
2. **Defensive Boundary Architecture:** The evaluation package contains zero proprietary engine source and zero credentials, certified against 130 adversarial attack vectors.
3. **Data Protection Invariant:** Data processing agreements legally and technically guarantee zero model training on uploaded evaluator files.
