# AMDI-OS Mathematical Foundations

This document details the mathematical formulations and formal definitions underpinning the 12 specialized document intelligence engines, fusion score models, and rankers.

---

## 1. Geometry Engine

The Geometry Engine normalizes coordinates across varying page dimensions and models document elements as spatial coordinate vectors.

### 1.1 Element Bounding Box Representation
Each block $E_i$ on page $p_i$ is mapped as:
$$E_i = (x_i, y_i, w_i, h_i, p_i) \in \mathbb{R}^5$$

### 1.2 Coordinate Normalization
Page coordinates are normalized to the interval $[0, 1000]$ to ensure aspect-ratio invariant representation:
$$x_{\text{norm}} = \frac{x - x_{\text{min}}}{W} \times 1000$$
$$y_{\text{norm}} = \frac{y - y_{\text{min}}}{H} \times 1000$$

---

## 2. Matrix Engine

The Matrix Engine extracts tabular structures and analyzes growth metrics and data distributions.

### 2.1 Tabular Representation
A table is represented as a matrix $M \in \mathbb{R}^{R \times C}$ of cell values.

### 2.2 Singular Value Decomposition (SVD)
For tabular compression and latent factor extraction:
$$M = U \Sigma V^T$$
where:
* $U \in \mathbb{R}^{R \times R}$ (orthonormal left singular vectors)
* $\Sigma \in \mathbb{R}^{R \times C}$ (diagonal matrix of singular values $\sigma_i$)
* $V \in \mathbb{R}^{C \times C}$ (orthonormal right singular vectors)

---

## 3. Template Engine

The Template Engine generates Structural Fingerprints of document layouts and computes layout similarities.

### 3.1 Structural Fingerprints
Let $F \in \{0, 1\}^B$ be a binary layout fingerprint representing grid presence.

### 3.2 Fingerprint Similarities
* **Jaccard Similarity**:
$$\text{Jaccard}(F_1, F_2) = \frac{|F_1 \cap F_2|}{|F_1 \cup F_2|} = \frac{\sum (F_1 \land F_2)}{\sum (F_1 \lor F_2)}$$
* **Cosine Similarity**:
$$\text{Cosine}(F_1, F_2) = \frac{F_1 \cdot F_2}{\|F_1\|_2 \|F_2\|_2}$$

---

## 4. Frequency Engine

The Frequency Engine computes word frequencies, statistical distributions, and information density.

### 4.1 BM25 Relevance Scoring
$$\text{Score}(D, Q) = \sum_{i=1}^n \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

### 4.2 Shannon Entropy
$$\text{Entropy}(D) = -\sum_{x \in D} P(x) \log_2 P(x)$$

---

## 5. Recurrence Engine

The Recurrence Engine identifies repeating layouts, headers, and boilerplate text using Locality Sensitive Hashing (LSH).

### 5.1 MinHash Signatures
$$\text{MinHash}(D) = \min_{s \in D} h(s)$$

### 5.2 LSH Banding
For $b$ bands and $r$ rows, the probability of a candidate match is:
$$P(\text{match}) = 1 - (1 - s^r)^b$$
where $s$ is the Jaccard similarity.

---

## 6. Semantic Engine

The Semantic Engine projects text segments into dense vector spaces and extracts semantic entities.

### 6.1 Semantic Projection
$$\vec{s}_i = \text{Encoder}(T_i) \in \mathbb{R}^d$$

### 6.2 Distance Metrics
$$\text{Distance}_{\text{cosine}}(\vec{u}, \vec{v}) = 1 - \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\|_2 \|\vec{v}\|_2}$$

---

## 7. Graph Engine

The Graph Engine models cross-references and sections as a network $G = (V, E)$.

### 7.1 PageRank Node Centrality
$$\text{PR}(u) = \frac{1 - d}{N} + d \sum_{v \in B_u} \frac{\text{PR}(v)}{L(v)}$$
where:
* $d$ is the damping factor (typically $0.85$)
* $B_u$ is the set of nodes linking to $u$
* $L(v)$ is the out-degree of $v$

---

## 8. Topology Engine

The Topology Engine extracts topological structures from spatial element placements.

### 8.1 persistent Homology
For a point cloud $X$ of element centroids, persistent homology computes Betti numbers:
* $\beta_0$: Number of connected components.
* $\beta_1$: Number of 1-dimensional loops/voids.

---

## 9. Spectral Engine

The Spectral Engine performs graph partitionings and clusters elements using Laplacians.

### 9.1 Graph Laplacian
$$L = D - A$$
where $D$ is the degree matrix and $A$ is the adjacency matrix.

### 9.2 Spectral Clustering
Find the eigenvalues $\lambda_i$ and eigenvectors $\vec{v}_i$ satisfying:
$$L \vec{v} = \lambda \vec{v}$$

---

## 10. Tensor Engine

The Tensor Engine compresses document models across multi-dimensional representations (Page $\times$ Section $\times$ Row $\times$ Column).

### 10.1 Tucker Decomposition
$$\mathcal{T} \approx \mathcal{G} \times_1 U^{(1)} \times_2 U^{(2)} \times_3 U^{(3)}$$
where $\mathcal{G}$ is the core tensor and $U^{(i)}$ are factor matrices.

---

## 11. Information Physics Engine

The Information Physics Engine treats document content density as "mass" and computes virtual gravitational fields.

### 11.1 Information Gravity
$$F = G \frac{m_1 m_2}{r^2}$$
where $m_1, m_2$ represent information mass (entropy/density) and $r$ is the spatial distance between blocks.

---

## 12. Retrieval Engine (Adaptive Fusion)

The Retrieval Engine combines retrieval scores from the 7 methods via Reciprocal Rank Fusion (RRF).

### 12.1 Reciprocal Rank Fusion
$$\text{RRF}(d) = \sum_{m \in \mathcal{M}} \frac{1}{k + r_m(d)}$$
where:
* $\mathcal{M}$ is the set of retrieval methods.
* $r_m(d)$ is the rank of document $d$ under method $m$.
* $k$ is a constant hyperparameter (typically $60$).