# 16 — Mathematical Formulation and Equations

## 1. Grounded Mathematical Models
AEGIS-DocIntel employs three core mathematical formulations for retrieval, scoring, and conflict minimization.

### 1.1 High-Dimensional Cosine Similarity Metric
Measures the directional alignment of two dense vector embeddings $\mathbf{u}, \mathbf{v} \in \mathbb{R}^d$ on the unit hypersphere:

$$S_C(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2} = \frac{\sum_{i=1}^{d} u_i v_i}{\sqrt{\sum_{i=1}^{d} u_i^2} \sqrt{\sum_{i=1}^{d} v_i^2}}$$

### 1.2 Okapi BM25 Lexical Ranking
Calculates term-matching relevance between document chunk $D$ and query $Q = \{q_1, \dots, q_n\}$ with non-linear term saturation:

$$\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

Where:
- $k_1 = 1.2$: Controls term frequency saturation limits.
- $b = 0.75$: Controls document length penalization.

### 1.3 Unified Ising Hamiltonian for Fact Contradiction
Maps conflicting candidate facts to a statistical physics spin-glass minimization problem:

$$\mathcal{H}(\boldsymbol{\sigma}) = -\sum_{\langle i, j \rangle} J_{ij} \sigma_i \sigma_j - \sum_{i} h_i \sigma_i$$

Where:
- $\sigma_i \in \{-1, +1\}$: Binary fact verification state (Rejected / Approved).
- $J_{ij}$: Coupling matrix representing corroboration ($J > 0$) or contradiction ($J < 0$).
- $h_i$: Local field bias reflecting source document credibility priors.
