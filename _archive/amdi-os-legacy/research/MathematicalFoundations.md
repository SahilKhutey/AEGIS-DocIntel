# AEGIS-AMDI-OS — Mathematical Foundations

This document lists all formal mathematical definitions, representations, and coordinate formulations utilized throughout the **Adaptive Mathematical Document Intelligence Operating System (AMDI-OS)**.

---

## §1. Master Document Representation

A document $D$ is defined as a 10-tuple representing synchronized semantic, spatial, recurrence, frequency, structural, and information-theoretic layers:

$$D = (P, S, G, R, F, M, T, X, H, E)$$

Where:
- $P$ represents the ordered set of page representations.
- $S$ represents the semantic representation layer.
- $G$ represents the geometric coordinate layout layer.
- $R$ represents the duplicate structural recurrence layer.
- $F$ represents the token frequency and weight layer.
- $M$ represents the table matrix relational layer.
- $T$ represents the clustered template fingerprint layer.
- $X$ represents the structural linkage graph layer.
- $H$ represents the hierarchical coordinates layer.
- $E$ represents the Shannon entropy layer.

---

## §2. Page Representation

Each page $P_i$ is defined as an ordered set of elements:

$$P = \{P_1, P_2, \dots, P_k\}$$
$$P_i = \{E_1, E_2, E_3, \dots, E_n\}$$

---

## §3. Element Representation

Each element $E_i$ is defined as an 8-tuple carrying positional, geometric, structural, and content attributes:

$$E_i = (x_i, y_i, w_i, h_i, p_i, \theta_i, t_i, c_i)$$

Where:
- $x_i, y_i \in [0, 1]$ are the normalized horizontal and vertical coordinates of the bounding box's top-left corner.
- $w_i, h_i \in [0, 1]$ are the normalized width and height of the bounding box.
- $p_i \in \mathbb{N}^+$ is the page number.
- $\theta_i \in [0, 2\pi)$ is the rotation angle of the element.
- $t_i \in \mathcal{T}$ is the element type (e.g., text, table, figure, heading).
- $c_i$ is the textual or binary content of the element.

---

## §4. Normalized Coordinates

To eliminate physical page-size dependencies, coordinate transformations are applied:

$$\tilde{x}_i = \frac{x_i}{W_p}, \quad \tilde{y}_i = \frac{y_i}{H_p}, \quad \tilde{w}_i = \frac{w_i}{W_p}, \quad \tilde{h}_i = \frac{h_i}{H_p}$$

Where $W_p$ and $H_p$ represent the physical width and height of page $p_i$.

**Theorem 4.1 (Scale Invariance):** For any scale factor $\lambda > 0$,
$$\text{dist}(\tilde{x}_i, \tilde{x}_j) = \frac{\text{dist}(x_i, x_j)}{\lambda}$$
The normalized distance metrics are invariant under page rescaling.

---

## §5. Geometric Distance

The Euclidean distance between two normalized elements $E_i$ and $E_j$ on the same page is:

$$d_{ij} = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}$$

For elements residing on different pages, a page distance penalty is applied:

$$d_{ij} = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2} + 1.5 \cdot |p_i - p_j|$$

---

## §6. Alignment Score

Alignment metrics determine reading columns and layouts:

$$\text{Horizontal Alignment: } A_x(i, j) = 1 - \frac{|x_i - x_j|}{W}$$
$$\text{Vertical Alignment: } A_y(i, j) = 1 - \frac{|y_i - y_j|}{H}$$
$$\text{Combined Alignment: } A(i, j) = \frac{A_x(i, j) + A_y(i, j)}{2}$$

Where $A(i, j) \in [0, 1]$; a score of $1.0$ represents perfect alignment.

---

## §7. Area Ratio

The proportion of canvas area covered by an element is:

$$\text{AR}_i = \frac{w_i \cdot h_i}{W \cdot H} = \tilde{w}_i \cdot \tilde{h}_i$$
$$I_A(i) = \text{AR}_i$$

---

## §8. Reading Order Sorting

Reading order is determined by a lexicographical sort key:

$$\text{RO}(E_i) = (y_i, x_i)$$

---

## §9. Recurrence Relation

Structural duplicate elements (such as running headers, footers, page numbers) follow recurrence relations:

$$R_n = a \cdot R_{n-1} + b$$

For a document with $n$ recurring blocks and one canonical form:
$$\text{Storage} = |R_0| + n \cdot \log(p_{\max})$$
$$\text{Naive Storage} = n \cdot |R_0|$$
$$\text{Compression Ratio} = \frac{1}{n} + \frac{\log(p_{\max})}{|R_0|}$$

---

## §10. Similarity Function

Relevance scoring between element dense vectors:

$$\text{Sim}(i, j) = \frac{V_i \cdot V_j}{\|V_i\| \cdot \|V_j\|}$$

---

## §11. Hash Recurrence

Hashing determines exact structural duplicates:

$$H_i = \text{Hash}(E_i) \in \{0, 1\}^k$$
$$f(H_i) = |\{j : H_j = H_i\}|$$

An element is defined as recurring if and only if $f(H_i) > 1$.

---

## §12. Frequency Weighting

Token importance weighting:

$$I_f(x) = \frac{1}{1 + \log f(x)}$$

**Theorem 12.1 (Monotonicity):** $I_f(x)$ is strictly decreasing in $f(x)$.
**Theorem 12.2 (Bounds):** $I_f(x) \in (0, 1]$ where $I_f(1) = 1$ and $\lim_{f \to \infty} I_f(x) = 0$.

---

## §13. Shannon Entropy

Shannon entropy computed over element token distributions:

$$H(X) = -\sum_{x \in X} p(x) \log_2 p(x)$$
$$H(e_i) = -\sum_{t \in e_i} \left(\frac{\text{tf}_t}{|e_i|}\right) \log_2 \left(\frac{\text{tf}_t}{|e_i|}\right)$$

**Theorem 13.1:** $0 \le H(X) \le \log_2 |X|$.

---

## §14. Density

Information density relates token count or entropy to spatial area:

$$D = \frac{N}{A}$$
$$\bar{D} = \frac{1}{|D|} \sum_{i} D_i$$

---

## §15. Semantic Embedding

Dense embedding representation:

$$S_i \in \mathbb{R}^d, \quad d \in \{384, 768, 1024, 1536, 3072\}$$
$$\text{Sim}(S_i, S_j) = \cos(\theta) = \frac{S_i \cdot S_j}{\|S_i\| \|S_j\|}$$

---

## §16. Table as Matrix

Tables are represented as a cell matrix $M$:

$$M = [m_{ij}]_{r \times c}$$

Linear algebra operations on tables:
$$\text{Total Sum: } \sum_{i,j} M[i, j]$$
$$\text{Mean: } \mu = \frac{1}{r \cdot c} \sum_{i,j} M[i, j]$$
$$\text{Variance: } \sigma^2 = \frac{1}{r \cdot c} \sum_{i,j} (M[i, j] - \mu)^2$$
$$\text{Covariance: } \text{Cov}(X, Y) = E[XY] - E[X]E[Y]$$
$$\text{Correlation: } \rho = \frac{\text{Cov}(X, Y)}{\sigma_X \cdot \sigma_Y}$$

---

## §17. Table Dependency

Cell coordinates depend on neighboring indices:

$$\mathcal{D}(i, j) = \{M[i, j-1], M[i-1, j], M[i-1, j-1]\}$$

Table cells are represented as an adjacency network where edges connect orthogonal neighbors:
$$A_T[i,j; i',j'] = 1 \iff |i - i'| + |j - j'| = 1$$

---

## §18. Relative Growth & CAGR

Growth metrics inside tables:

$$\text{Growth: } G = \frac{V_2 - V_1}{V_1}$$
$$\text{CAGR: } \text{CAGR} = \left(\frac{V_n}{V_1}\right)^{\frac{1}{n-1}} - 1$$

---

## §19. Template Fingerprint

Templates represent recurring layout profiles:

$$T = (h, b, t, i, m)$$

Where:
- $h$ represents the count of headers.
- $b$ represents the count of text blocks.
- $t$ represents the count of tables.
- $i$ represents the count of images.
- $m \in \mathbb{R}^4$ represents the page margins.

$$\text{Template Similarity: } \text{TS}(T_1, T_2) = \cos(T_1, T_2)$$

---

## §20. Structural Graph Topology

Document structure represented as a network $G$:

$$G = (V, E)$$
$$A[i, j] = 1 \iff (i, j) \in E$$
$$\text{Degree: } \text{deg}(v) = \sum_{j} A[v, j]$$
$$\text{Centrality: } C(v) = \frac{\text{deg}(v)}{N - 1}$$
$$\text{PageRank: } \text{PR}(v) = \frac{1-d}{N} + d \cdot \sum_{u \to v} \frac{\text{PR}(u)}{L(u)}$$

---

## §21. Hierarchical Coordinates

Coordinates tracking structure through tokens:

$$H = (p, s, b, l, t)$$

Where:
- $p$ represents the page index.
- $s$ represents the section index.
- $b$ represents the block index.
- $l$ represents the line index.
- $t$ represents the token index.

**Theorem 21.1 (Uniqueness):** The 5-tuple coordinate $H$ uniquely identifies any token in the document.

---

## §22. Context Compression Ratio

$$\text{Compression Ratio: } \text{CR} = \frac{|\text{compressed}|}{|\text{original}|}$$
$$\text{Compression Percentage: } \text{CP} = 1 - \text{CR}$$

---

## §23. Information Retention

The fraction of source facts retained in the context window:

$$\text{Information Retention: } \text{IR} = \frac{|\text{retained}|}{|\text{original}|}$$

---

## §24. Multi-Layer Retrieval Score

Combined multi-signal relevance scoring:

$$R(Q, D) = \sum_{i} w_i(Q) \cdot s_i(Q, D)$$

Subject to constraints:
$$\sum w_i = 1, \quad w_i \ge 0$$

---

## §25. Dynamic Weighting

Normalized relevance scoring dynamically assigned per query:

$$w_i = \frac{\text{score}_i}{\sum_j \text{score}_j}$$
$$w^* = \text{softmax}(\text{MLP}(\phi(Q)))$$

---

## §26. Confidence

Weighted retrieval confidence:

$$C = \sum_{i} w_i \cdot R_i$$

---

## §27. Query Complexity

The sum complexity of query intents:

$$\text{QC} = a + b + c + d$$

Where $a$, $b$, $c$, $d$ represent semantic, table, geometry, and graph complexity dimensions.

---

## §28. Computational Cost

Total system resource overhead:

$$\text{CC} = \alpha \cdot T + \beta \cdot M + \gamma \cdot R$$

Where $T$ represents tokens, $M$ represents memory, and $R$ represents retrieval passes.

---

## §29. Token Cost

$$\text{TC} = I + O$$

Where $I$ is input tokens and $O$ is output tokens.

---

## §30. Memory Cost

$$\text{MC} = \text{RAM} + \text{Cache} + \text{Storage}$$

---

## §31. Latency

$$\text{L} = T_p + T_r + T_l$$

Where $T_p$ represents parsing latency, $T_r$ represents retrieval latency, and $T_l$ represents LLM inference latency.

---

## §32. Global Optimization Objective

The objective function minimized during system executions:

$$\text{Minimize } J = w_1 \cdot \text{TC} + w_2 \cdot L + w_3 \cdot \text{MC}$$
$$\text{Subject to: } \text{Accuracy} \ge 0.95, \quad \text{IR} \ge 0.95, \quad \text{Confidence} \ge 0.90$$
