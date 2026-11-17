# PROT-03: Proprietary Algorithm & Mathematical IP Register

**Document:** 02_PROPRIETARY_ALGORITHM_REGISTER.md  
**Audit Scope:** Deep mathematical and algorithmic inspection of core technical differentiators.  

---

## 1. Mathematical Context Packing Engine

### A. Mathematical Formulation
In `aegis-docprep/aegis_docprep/context_packer.py` and `src/engines/retrieval/submodular_packer.py`, context assembly is formulated as a **submodular facility-location knapsack optimization** problem:

$$f(S) = \alpha F_{\text{coverage}}(S) + \beta F_{\text{relevance}}(S)$$

Subject to the knapsack token budget constraint:

$$\sum_{i \in S} c_i \le B$$

Where:
- $S \subseteq V$: Set of candidate document chunks selected for the LLM context window.
- $F_{\text{coverage}}(S) = \sum_{j \in V} \max_{i \in S} \text{sim}(e_i, e_j)$: Facility-location coverage function capturing semantic breadth across the source document.
- $F_{\text{relevance}}(S) = \sum_{i \in S} r_i$: Additive query relevance score based on dense cosine similarity.
- $c_i \in \mathbb{Z}^+$: Token cost of chunk $i$.
- $B \in \mathbb{Z}^+$: Hard token budget (e.g., 4,000 or 8,000 tokens).
- $\alpha, \beta \ge 0$: Weight hyperparameters balancing diversity against query relevance.

### B. Theoretical Approximation Guarantee
The implementation implements a modified greedy heuristic for submodular knapsack maximization. It achieves a provable approximation ratio:

$$\rho = \frac{1 - 1/e}{2} \approx 0.31606$$

### C. Protection Strategy
1. **Open-Core Baseline:** The basic greedy heuristic in `aegis-docprep` is licensed under Apache-2.0. This establishes open developer credibility.
2. **Proprietary Enhancements:** Production multi-document cross-entropy packing, adaptive temperature-based diversity budgeting, and GPU-accelerated facility-location solvers remain **100% proprietary** and hosted on the private Evaluation Gateway.

---

## 2. Spatial Graph Reading-Order Engine

### A. Algorithmic Formulation
In `src/engines/graph_reading_order.py`, layout parsing reconstructs natural multi-column reading flow from unformatted bounding boxes $(x_{\min}, y_{\min}, x_{\max}, y_{\max})$.

#### Successor Condition (Definition 6.1):
Node $j$ is a valid reading-forward successor of node $i$ ($i \to j$) iff:
1. **Same-Row Condition:** $|y_i - y_j| < \tau_{\text{row}}$ and $x_j > x_i$ (horizontal flow within line band); OR
2. **Lower-Row Condition:** $y_j \ge y_i + \tau_{\text{row}}$ (vertical progression down the page).

#### Deterministic DAG Sorting:
- Cycles are broken using edge probability thresholds:
  $$w(i \to j) = \exp\left(-\frac{d(i, j)}{\sigma}\right) \cdot \cos(\theta_{ij} - \theta_{\text{flow}})$$
- Final reading order is resolved via **Kahn's topological sort** with a priority queue tie-breaker keyed on:
  $$\text{Key}(i) = (y_{\min}, x_{\min}, \text{node\_id})$$

#### Order-Preserving Wasserstein Distance (OPW):
Quantifies alignment against ground-truth document sequences:
$$D_{\text{OPW}}(A, B) = \min_{T \ge 0} \sum_{i,j} T_{ij} C_{ij} + \lambda \text{KL}(T \parallel P)$$

### B. Protection Strategy
- **Physical Exclusion:** `src/engines/graph_reading_order.py` is excluded from the downloadable package.
- Evaluators receive pre-computed, correctly ordered layout nodes in the UI; the underlying directed graph solver runs remotely on the server.

---

## 3. Sheaf Laplacian Multi-Document Topology

### A. Mathematical Formulation
In `src/engines/topology/sheaf.py`, cross-document consistency is evaluated via cellular sheaves over document discourse graphs:
- Stalks $\mathcal{F}(v) = \mathbb{R}^d$ represent local embedding spaces.
- Restriction maps $\mathcal{F}_{v \unlhd e}: \mathcal{F}(v) \to \mathcal{F}(e)$ transport assertions across references.
- Sheaf Laplacian $\Delta_0 = \delta^T \delta$ spectral decomposition identifies contradictions: non-zero eigenvalues in harmonic space $H^0(X; \mathcal{F})$ indicate factual divergence between revisions.

### B. Protection Strategy
- **Trade Secret Status:** Core sheaf decomposition algorithms represent significant research investment and are **never exposed** or bundled into downloadable binaries.
