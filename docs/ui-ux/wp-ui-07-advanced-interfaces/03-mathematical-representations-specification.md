# 03 — Mathematical Representations Specification

## 1. Functional Scope
The Mathematical Explorer (`/mathematics`, `/mathematics/[representationId]`) exposes the underlying geometric and algebraic primitives that power AEGIS vector search and contradiction minimization.

## 2. Interface Primitives
1. **Vector Viewer (`VectorViewer.tsx`)**:
   - High-dimensional vector coordinate exploration (1536-dimensional float32 embeddings).
   - Dual inspection modes: Dynamic Heatmap view and Full Precision Table view.
   - Sub-chunk pagination (dimensions `[0..31]`, `[32..63]`, etc.) to prevent DOM freezing.
   - Numerical invariant metrics: L2 Euclidean Norm ($\|\mathbf{u}\|_2 = 1.0$), Min value, Max value, Sparsity percentage.
2. **Matrix Viewer (`MatrixViewer.tsx`)**:
   - 2D Gram matrix and Cosine similarity kernel inspection ($8 \times 8$).
   - Interactive cell selection displaying coordinate pair, row/column labels, and unrounded float value.
   - Condition number estimation ($\kappa(A) = 2.45$) to evaluate matrix stability.
3. **Formulation Catalog (`EquationRenderer.tsx`)**:
   - Formal mathematical definitions rendered with LaTeX:
     - Okapi BM25 Lexical Ranking
     - High-Dimensional Cosine Similarity Metric
     - Spin Glass Ising Hamiltonian Energy Function
   - Explanatory parameter tables detailing variable physical meaning.
4. **Transformation Trace (`TransformationTrace.tsx`)**:
   - Provenance timeline tracking text normalization $\to$ recursive chunking $\to$ dense vector embedding $\to$ L2 hypersphere normalization $\to$ kernel matrix synthesis.
