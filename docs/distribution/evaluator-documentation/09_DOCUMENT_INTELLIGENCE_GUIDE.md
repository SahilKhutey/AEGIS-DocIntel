# 09 - Document Intelligence Guide
AEGIS-DocIntel provides grounded question-answering and multi-document synthesis.

### Grounding & Citations
Every statement returned by the intelligence engine includes an interactive citation linking directly to the page number, bounding box, or line offset of the source document.
If a question cannot be answered from the uploaded corpus, the engine returns an explicit `UNGROUNDED_IN_CORPUS` notice rather than guessing.

### Cross-Document Comparison
Compare multiple agreements side-by-side to highlight indemnification clauses, governing laws, and term deviations.
