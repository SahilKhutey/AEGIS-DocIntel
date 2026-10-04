# AEGIS-AMDI-OS — Mathematical Framework

**Version**: 1.0  
**Status**: Production  
**Last Updated**: 2024

---

## 1. Notation and Conventions

### 1.1 Sets and Spaces

- ℝ: Real numbers
- ℕ: Natural numbers (positive integers)
- ℤ: Integers
- ℝⁿ: n-dimensional Euclidean space
- Δⁿ⁻¹ = {x ∈ ℝⁿ : xᵢ ≥ 0, Σxᵢ = 1}: Probability simplex

### 1.2 Common Symbols

| Symbol | Meaning |
|--------|---------|
| `D` | Document |
| `e\u208i` or `E\u208i` | i-th element |
| `p` | Page number |
| `f(x)` | Frequency of x |
| `H(X)` | Entropy of random variable X |
| `I(x)` | Importance weight |
| `M[i,j]` | Matrix entry at (i,j) |
| `G = (V, E)` | Graph with vertices and edges |
| `\u03b2\u209c` | k-th Betti number |
| `\u03bb` | Eigenvalue |
| `\u03a6(x)` | Information field at point x |
| `IE` | Information energy |
| `G` (scalar) | Information gravity |
| `PE` | Potential energy |

### 1.3 Document Model

A document D is the tuple:

    D = (P, S, G, R, F, M, T, X, H, E)

Where:
- P = {P\u2081, P\u2082, ..., P\u209c}: ordered set of pages
- S: semantic layer (embeddings)
- G: geometric layer (spatial coordinates)
- R: recurrence layer (template invariance)
- F: frequency layer (importance)
- M: matrix layer (tables)
- T: template layer (fingerprints)
- X: graph layer (relations)
- H: hierarchical layer (coordinates)
- E: entropy layer (information density)

---

## 2. Coordinate System (Geometry Engine)

### 2.1 Element Definition

Each element e\u208i is defined as a 7-tuple:

    e\u208i = (x\u208i, y\u208i, w\u208i, h\u208i, p\u208i, \u03b8\u208i, t\u208i)

Where:
- x\u208i \u2208 [0, 1]: normalized x-coordinate (left edge)
- y\u208i \u2208 [0, 1]: normalized y-coordinate (top edge)
- w\u208i \u2208 [0, 1]: normalized width
- h\u208i \u2208 [0, 1]: normalized height
- p\u208i \u2208 \u2115\u207a: page number
- \u03b8\u208i \u2208 [0, 2\u03c0): rotation angle in radians
- t\u208i \u2208 T: element type (text, table, figure, etc.)

### 2.2 Normalization

Raw coordinates are normalized to page dimensions:

    x\u0303 = x / W_page
    y\u0303 = y / H_page
    w\u0303 = w / W_page
    h\u0303 = h / H_page

### 2.3 Theorem 4.1 (Scale Invariance)

**Statement**: The normalized geometric distance d\u0303(i, j) between elements i and j is
invariant to uniform page scaling.

**Proof**: 
For uniform scaling factor \u03bb > 0, raw distances scale as d \u2192 \u03bbd, while
normalized coordinates satisfy x\u0303 \u2192 x\u0303 (invariant). Therefore:

    d\u0303(i, j) = \u221a[(x\u0303\u208i - x\u0303\u208b)\u00b2 + (y\u0303\u208i - y\u0303\u208b)\u00b2]

is scale-invariant. \u25a1

### 2.4 Euclidean Distance

The distance between elements:

    d(i, j) = \u221a[(x\u208i - x\u208b)\u00b2 + (y\u208i - y\u208b)\u00b2] + \u03bb_page \u00b7 |p\u208i - p\u208b|

Where \u03bb_page is the cross-page penalty (typically 1.5).

### 2.5 Alignment Score

Horizontal alignment:

    A\u209d(i, j) = 1 - |x\u208i - x\u208b| / W

Vertical alignment:

    A\u1d67(i, j) = 1 - |y\u208i - y\u208b| / H

Overall alignment:

    A(i, j) = (A\u209d + A\u1d67) / 2

**Property**: A(i, j) \u2208 [0, 1], with A = 1 iff positions are identical.

### 2.6 Area Ratio (Importance)

    AR(i) = w\u208i \u00b7 h\u208i \u2208 [0, 1]

**Property**: Represents the fraction of page area covered by element i.

### 2.7 Reading Order

The reading order key:

    RO(e\u208i) = (y\u208i, x\u208i)

Sorting lexicographically gives the natural reading sequence.

### 2.8 Bounding Box Intersection over Union

For two bounding boxes B\u2081 and B\u2082:

    IoU(B\u2081, B\u2082) = |B\u2081 \u2229 B\u2082| / |B\u2081 \u222a B\u2082|

Where:

    |B \u2229 B| = max(0, min(x\u2081\u2082, x\u2082\u2082) - max(x\u2081\u2081, x\u2082\u2081)) \u00b7 max(0, min(y\u2081\u2082, y\u2082\u2082) - max(y\u2081\u2081, y\u2082\u2081))

    |B \u222a B| = |B\u2081| + |B\u2082| - |B\u2081 \u2229 B\u2082|

---

## 3. Recurrence Relations

### 3.1 Basic Recurrence

For n copies of the same element:

    R\u209b = R\u209b\u208b\u2081  for n > 0

With initial condition R\u2080 = canonical representation.

### 3.2 General Linear Recurrence

    R\u209b = a\u00b7R\u209b\u208b\u2081 + b

Characteristic polynomial: \u03bb - a

Solutions:
- If a \u2260 1: R\u209b = a\u209b \u00b7 R\u2080 + b \u00b7 (a\u209b - 1) / (a - 1)
- If a = 1: R\u209b = R\u2080 + n\u00b7b

### 3.3 Storage Optimization

For n identical elements across pages p\u2081, ..., p\u209b:

    Storage = |R\u2080| + n \u00b7 log(p_max)

Versus naive storage:

    Storage_naive = n \u00b7 |R\u2080|

Compression ratio:

    CR = Storage / Storage_naive = 1/n + log(p_max)/|R\u2080|

**For typical documents**: |R\u2080| ~ 100 bytes, log(p_max) ~ 3, so CR \u2248 1/n + 0.03.

### 3.4 Hash-Based Detection

For text recurrence:

    h\u208i = Hash(normalize(e\u208i.content))

Where normalize() lowercases and collapses whitespace.

Recurrence detected iff:

    f(h\u208i) = |{j : h\u208b = h\u208i}| > 1

### 3.5 Template Definition

A template group G is a set of equivalent elements:

    G = {e\u208i : \u2200i, j \u2208 G, hash(e\u208i) = hash(e\u208b) \u2227 spatial_close(e\u208i, e\u208b)}

Where spatial_close checks normalized coordinate similarity within threshold \u03b5.

---

## 4. Frequency Equations

### 4.1 Term Frequency

For document D with elements {e\u2081, ..., e\u209b}:

    tf(t, D) = \u03a3\u208i |{w \u2208 tokens(e\u208i) : w = t}|

### 4.2 Inverse Frequency Weight

**Definition**:

    I_f(x) = 1 / (1 + log(1 + f(x)))

### 4.3 Theorem 12.1 (Monotonicity)

**Statement**: I_f(x) is strictly decreasing in f(x) for f > 1.

**Proof**:

    dI_f/df = -1 / [(1 + log f)\u00b2 \u00b7 f] < 0  for f > 0

\u25a1

### 4.4 Theorem 12.2 (Bounds)

**Statement**: I_f \u2208 (0, 1].

**Proof**:
- Upper bound: I_f(1) = 1/(1+0) = 1
- Lower bound: lim_{f\u2192\u221e} I_f = lim_{f\u2192\u221e} 1/log(1+f) = 0

\u25a1

### 4.5 TF-IDF

    TF-IDF(t, D) = tf(t, D) \u00b7 log(N / df(t))

Where:
- N: total documents in collection
- df(t): number of documents containing t

### 4.6 Composite Element Weight

    I(e) = \u03b1 \u00b7 I_f(e) + \u03b2 \u00b7 I_type(e) + \u03b3 \u00b7 I_recurrence(e)

With:
- \u03b1 + \u03b2 + \u03b3 = 1 (typically \u03b1=0.6, \u03b2=0.4, \u03b3=-0.3 for suppression)
- I_type(e): type-based baseline (TABLE=1.8, HEADING=1.5, etc.)

---

## 5. Entropy Equations

### 5.1 Shannon Entropy

For discrete random variable X with distribution P(x):

    H(X) = -\u03a3\u209d P(x) log\u2082 P(x)

### 5.2 Theorem 13.1 (Entropy Bounds)

**Statement**: 0 \u2264 H(X) \u2264 log\u2082|X|

**Proof**: Lower bound: each term -p log p \u2265 0.
Upper bound: By Gibbs' inequality, H(X) \u2264 -\u03a3p(x) log(1/|X|) = log|X|.
\u25a1

### 5.3 Joint Entropy

    H(X, Y) = -\u03a3\u209d,\u1d67 P(x, y) log\u2082 P(x, y)

### 5.4 Conditional Entropy

    H(Y | X) = H(X, Y) - H(X) = \u03a3\u209d P(x) \u00b7 H(Y | X=x)

### 5.5 Mutual Information

    I(X; Y) = H(X) + H(Y) - H(X, Y)
            = H(X) - H(X | Y)
            = H(Y) - H(Y | X)

**Property**: I(X; Y) = 0 iff X and Y are independent.

### 5.6 KL Divergence

    D_KL(P || Q) = \u03a3\u209d P(x) log\u2082[P(x)/Q(x)]

**Properties**:
- D_KL(P || Q) \u2265 0 (Gibbs' inequality)
- D_KL(P || Q) = 0 iff P = Q
- Not symmetric: D_KL(P||Q) \u2260 D_KL(Q||P)

### 5.7 JS Divergence (Symmetric)

    D_JS(P, Q) = \u00bd D_KL(P || M) + \u00bd D_KL(Q || M)

Where M = (P + Q) / 2.

**Properties**:
- D_JS \u2208 [0, 1] (using log base 2)
- Symmetric: D_JS(P, Q) = D_JS(Q, P)

### 5.8 Cross-Entropy

    H(P, Q) = -\u03a3\u209d P(x) log\u2082 Q(x)

**Property**: H(P, Q) = H(P) + D_KL(P || Q) \u2265 H(P)

### 5.9 Channel Capacity (Shannon)

    C = max_{P(X)} I(X; Y)

For document retrieval, this represents the maximum information transferable
about a query Q through the retrieval channel.

---

## 6. Graph Equations

### 6.1 Graph Definition

    G = (V, E)

Where V is a set of vertices and E \u2286 V \u00d7 V is a set of edges.

### 6.2 Adjacency Matrix

    A[i, j] = 1 if (i, j) \u2208 E
            0 otherwise

### 6.3 Degree

    deg(v) = \u03a3\u208b A[v, j]

### 6.4 Centrality (Degree)

    C_D(v) = deg(v) / (N - 1)

Where N = |V|.

### 6.5 PageRank

The PageRank vector \u03c0 satisfies:

    \u03c0 = (1-d)/N \u00b7 1 + d \u00b7 D\u207b\u00b9 A \u03c0

Or in matrix form:

    \u03c0\u1d4c = (1-d)/N \u00b7 1\u1d4c + d \u00b7 \u03c0\u1d4c M

Where M = D\u207b\u00b9 A is the transition matrix and d is the damping factor (typically 0.85).

**Power iteration**:

    \u03c0\u209c\u208a\u2081 = (1-d)/N \u00b7 1 + d \u00b7 M\u1d4c \u03c0\u209c

Converges when \u2016\u03c0\u209c\u208a\u2081 - \u03c0\u209c\u2016 < \u03b5.

### 6.6 Betweenness Centrality

    C_B(v) = \u03a3_{s\u2260v\u2260t} \u03c3_st(v) / \u03c3_st

Where:
- \u03c3_st: number of shortest paths from s to t
- \u03c3_st(v): number passing through v

### 6.7 Closeness Centrality

    C_C(v) = (N - 1) / \u03a3_{u\u2260v} d(v, u)

Where d(v, u) is the shortest path distance.

### 6.8 Graph Density

    \u03c1(G) = 2|E| / (|V| \u00b7 (|V| - 1))

For directed graphs: \u03c1 = |E| / (|V| \u00b7 (|V| - 1))

### 6.9 Laplacian Matrix

    L = D - A

Where D is the degree matrix.

### 6.10 Spectral Decomposition

The graph spectrum:

    A = U \u039b U\u1d4c

Where \u039b = diag(\u03bb\u2081, ..., \u03bb\u209c) are eigenvalues.

### 6.11 Hypergraph Extension

A hypergraph HG = (V, E*) where each hyperedge e \u2208 E* connects k \u2265 2 vertices:

    e = {v\u2081, v\u2082, ..., v\u209c}

Hypergraph incidence matrix:

    H[v, e] = 1 if v \u2208 e, 0 otherwise

---

## 7. Topology Equations

### 7.1 Simplicial Complex

A simplicial complex K is a collection of simplices closed under taking faces.

**n-simplex**: \u03c3 = {v\u2080, v\u2081, ..., v\u209b} (n+1 affinely independent points)

**Dimension**: dim(\u03c3) = n

### 7.2 Boundary Operator

The boundary of an n-simplex:

    \u2202\u209b(\u03c3) = \u03a3\u208i (-1)\u207f (\u03c3 \u200b \ {v\u208i})

### 7.3 Chain Complex

    ... \u2192 C\u209b\u208a\u2081(K) \u2192\u2202\u209b\u208a\u2081\u2192 C\u209b(K) \u2192\u2202\u209b\u2192 C\u209b\u208b\u2081(K) \u2192 ...

Where C\u209b(K) is the group of n-chains.

### 7.4 Betti Numbers

    \u03b2\u209b = rank(H\u209b(K)) = rank(ker \u2202\u209b) - rank(im \u2202\u209b\u208a\u2081)

**Interpretation**:
- \u03b2\u2080 = number of connected components
- \u03b2\u2081 = number of independent loops
- \u03b2\u2082 = number of enclosed voids

### 7.5 Euler Characteristic

    \u03c7(K) = \u03a3\u209b (-1)\u209b \u00b7 |K\u209b| = \u03a3\u209b (-1)\u209b \u03b2\u209b

Where |K\u209b| is the number of n-simplices.

### 7.6 Persistent Homology

For a filtration K\u2080 \u2286 K\u2081 \u2286 ... \u2286 K\u209b:

**Birth**: \u03b5_b = first scale where feature appears
**Death**: \u03b5_d = first scale where feature disappears
**Persistence**: pers = \u03b5_d - \u03b5_b

### 7.7 Vietoris-Rips Complex

Given point cloud P and threshold \u03b5:

    VR_\u03b5(P) = {\u03c3 \u2286 P : diam(\u03c3) \u2264 \u03b5}

Where diam(\u03c3) = max_{i,j \u2208 \u03c3} \u2016p\u208i - p\u208b\u2016

### 7.8 Persistence Diagram

    Dgm(f) = {(b\u208i, d\u208i) : birth and death of topological features}

With pairing of critical points.

### 7.9 Bottleneck Distance

    d_B(Dgm\u2081, Dgm\u2082) = inf_\u03b3 sup_x \u2016x - \u03b3(x)\u2016\u221e

### 7.10 Theorem (Stability)

For tame functions f, g:

    d_B(Dgm(f), Dgm(g)) \u2264 \u2016f - g\u2016\u221e

---

## 8. Information Field Equations

### 8.1 Information Energy

For element e with entropy H(e) and relevance R(e):

    IE(e) = H(e) \u00b7 R(e)

**High energy**: conclusions, warnings, critical values  
**Low energy**: page numbers, headers, footers

### 8.2 Information Gravity

For element i with importance I(i), connectivity C(i), and distance d(i, j) to other elements:

    G(i) = (I(i) \u00b7 C(i)) / d(i)\u00b2

Where d(i) = \u03a3\u208b \u2016p\u208i - p\u208b\u2016 + \u03b5

### 8.3 Information Field

The field at point x:

    \u03a5(x) = \u03a3\u208i W(i) / \u2016x - p\u208i\u2016\u00b2 + \u03b5

Where W(i) is the weight (importance) of element i and \u03b5 is a smoothing constant.

### 8.4 Field Gradient

    \u2207\u03a5(x) = \u03a3\u208i -2W(i)(x - p\u208i) / (\u2016x - p\u208i\u2016\u00b2 + \u03b5)\u00b2

### 8.5 Potential Energy

    PE(e) = I(e) \u00b7 P(e)

Where P(e) is the position-based priority (e.g., top of page = high priority).

### 8.6 Information Kinetics

    IK(t) = dI/dt

For versioned documents, this measures information change rate.

### 8.7 Conservation Law

For any document processing:

    I_input = I_output + I_compressed + I_discarded

**Constraint**: I_discarded / I_input < 0.05 (5%)

### 8.8 Theorem (Energy Conservation)

For a closed information system:

    E_total = \u03a3\u208i IE(i) = constant

Under the constraint that no information crosses the system boundary.

### 8.9 Theorem (Field Monotonicity)

For two points x, y on the same ray from element i:

    \u03a5(x) > \u03a5(y) iff \u2016x - p\u208i\u2016 < \u2016y - p\u208i\u2016

---

## 9. Tensor Equations

### 9.1 Tensor Definition

An n-way tensor T \u2208 \u211d^{I\u2081 \u00d7 I\u2082 \u00d7 ... \u00d7 I\u209c}

For documents, the 4-way tensor:

    T[i, j, k, l] = (page=i, section=j, row=k, column=l)

### 9.2 Mode-n Unfolding

The mode-n unfolding of T is a matrix:

    T\u208d\u209b\u208e \u2208 \u211d^{I\u209c \u00d7 (I\u2081 \u00b7 ... \u00b7 I\u209c\u208b\u2081 \u00b7 I\u209c\u208a\u2081 \u00b7 ... \u00b7 I\u209c)}

Where elements are arranged with index n as rows.

### 9.3 Mode-n Product

For T \u2208 \u211d^{I\u2081 \u00d7 ... \u00d7 I\u209c} and M \u2208 \u211d^{J \u00d7 I\u209c}:

    (T \u00d7\u209b M)[i\u2081, ..., i\u209c\u208b\u2081, j, i\u209c\u208a\u2081, ..., i\u209c] = \u03a3\u208i\u209b T[i\u2081, ..., i\u209c] \u00b7 M[j, i\u209b]

### 9.4 CP Decomposition (CANDECOMP/PARAFAC)

    T \u2248 \u03a3\u208b\u208c\u2081\u1d3f \u03bb\u208b \u00b7 a\u208b\u207d\u00b9\u207e \u2218 a\u208b\u207d\u00b2\u207e \u2218 ... \u2218 a\u208b\u207d\u1d3a\u207e

Where \u2218 is the outer product.

The factors minimize:

    \u2016T - \u03a3\u208b \u03bb\u208b \u2297\u209c a\u208b\u207d\u1d4f\u207e\u2016\u00b2

### 9.5 Tucker Decomposition

    T \u2248 G \u00d7\u2081 U\u207d\u00b9\u207e \u00d7\u2082 U\u207d\u00b2\u207e \u00d7 ... \u00d7\u209b U\u207d\u1d3a\u207e

Where:
- G is the core tensor
- U\u207d\u1d4f\u207e are orthogonal factor matrices

### 9.6 Higher-Order SVD (HOSVD)

The HOSVD is computed via:

    U\u207d\u207f\u207e = leading left singular vectors of T\u208d\u207f\u208e

### 9.7 Tensor Norm

Frobenius norm:

    \u2016T\u2016_F = \u221a(\u03a3\u208i\u2081,...,\u208i\u209c T[i\u2081,...,i\u209c]\u00b2)

### 9.8 Inner Product

    \u27e8T\u2081, T\u2082\u27e9 = \u03a3\u208i\u2081,...,\u208i\u209c T\u2081[i\u2081,...,i\u209c] \u00b7 T\u2082[i\u2081,...,i\u209c]

---

## 10. Spectral Equations

### 10.1 Fourier Transform

For discrete signal x[n]:

    X[k] = \u03a3\u209b\u208c\u2080\u1d39\u208b\u2081 x[n] \u00b7 e^{-i2\u03c0kn/N}

### 10.2 Inverse Fourier Transform

    x[n] = (1/N) \u03a3\u208b\u208c\u2080\u1d39\u208b\u2081 X[k] \u00b7 e^{i2\u03c0kn/N}

### 10.3 Power Spectrum

    P[k] = |X[k]|\u00b2

### 10.4 Periodicity Score

    \u03a0 = \u03a3\u208b\u2208top_k P[k] / \u03a3\u208b P[k]

Where top_k are the frequencies with highest power.

### 10.5 Eigenvalue Decomposition

For matrix A:

    A = V \u039b V\u207b\u00b9

Where:
- V: matrix of eigenvectors
- \u039b = diag(\u03bb\u2081, ..., \u03bb\u209c): diagonal of eigenvalues

### 10.6 Spectral Gap

    \u03b3 = |\u03bb\u2081| - |\u03bb\u2082|

Larger gap \u2192 faster convergence \u2192 more "structured" data.

### 10.7 Wavelet Transform

Continuous wavelet transform:

    W(a, b) = (1/\u221aa) \u222b f(t) \u00b7 \u03c8*((t-b)/a) dt

Where:
- a: scale parameter
- b: translation parameter
- \u03c8: mother wavelet

### 10.8 Wavelet Energy at Scale

    E(a) = \u03a3\u1d9e |W(a, b)|\u00b2

### 10.9 Theorem (Parseval)

For Fourier transform:

    \u03a3\u209b |x[n]|\u00b2 = (1/N) \u03a3\u208b |X[k]|\u00b2

### 10.10 Theorem (Wavelet Inversion)

    f(t) = (1/C_\u03c8) \u222b\u222b W(a, b) \u00b7 \u03c8_{a,b}(t) (da db)/a\u00b2

Where C_\u03c8 is the admissibility constant.

---

## 11. Probability Equations

### 11.1 Bayes' Theorem

    P(A | B) = P(B | A) \u00b7 P(A) / P(B)

### 11.2 Chain Rule

    P(A, B) = P(A | B) \u00b7 P(B) = P(B | A) \u00b7 P(A)

### 11.3 Total Probability

    P(B) = \u03a3\u208i P(B | A\u208i) \u00b7 P(A\u208i)

### 11.4 Independence

X, Y independent iff:

    P(X, Y) = P(X) \u00b7 P(Y)

### 11.5 Conditional Independence

X \u22a5 Y | Z iff:

    P(X, Y | Z) = P(X | Z) \u00b7 P(Y | Z)

### 11.6 Markov Chain Transition

For states {s\u2081, ..., s\u209c}:

    P(X_{t+1} = s\u208b | X_t = s\u208i) = P\u208i\u208b

Transition matrix: P = [P\u208i\u208b]

### 11.7 Markov Property

    P(X_{t+1} | X_t, ..., X_0) = P(X_{t+1} | X_t)

### 11.8 Stationary Distribution

\u03c0 satisfies:

    \u03c0 P = \u03c0
    \u03a3\u208i \u03c0\u208i = 1

### 11.9 Chapman-Kolmogorov Equation

    P\u207f\u207a\u1d50 = P\u207f \u00b7 P\u1d50

### 11.10 HMM Forward Algorithm

\u03b1\u209c(i) = P(O\u2081, ..., O\u209c, X\u209c = i)

Recurrence:

    \u03b1\u209c(i) = [\u03a3\u208b \u03b1\u209c\u208b\u2081(j) \u00b7 A\u208b\u208i] \u00b7 B\u208i(O\u209c)

### 11.11 HMM Viterbi Algorithm

    V\u209c(i) = max_{path} P(path, O\u2081, ..., O\u209c, X\u209c = i)

Recurrence:

    V\u209c(i) = max\u208b [V\u209c\u208b\u2081(j) \u00b7 A\u208b\u208i] \u00b7 B\u208i(O\u209c)

### 11.12 HMM Baum-Welch (EM)

E-step: compute \u03be and \u03b3  
M-step: update A, B, \u03c0

---

## 12. Optimization Equations

### 12.1 Lagrange Multipliers

For constrained optimization:

    L(x, \u03bb) = f(x) + \u03a3\u208i \u03bb\u208i \u00b7 g\u208i(x)

Stationary point: \u2207L = 0

### 12.2 KKT Conditions

For optimal x*:

1. \u2207f(x*) + \u03a3\u208i \u03bb\u208i \u2207g\u208i(x*) = 0
2. g\u208i(x*) \u2264 0
3. \u03bb\u208i \u2265 0
4. \u03bb\u208i \u00b7 g\u208i(x*) = 0 (complementary slackness)

### 12.3 0/1 Knapsack

    max  \u03a3\u208i v\u208i x\u208i
    s.t. \u03a3\u208i w\u208i x\u208i \u2264 B
         x\u208i \u2208 {0, 1}

DP solution:

    DP[i, w] = max(DP[i-1, w], v\u208i + DP[i-1, w-w\u208i])

### 12.4 Greedy Approximation

Sort by v\u208i/w\u208i ratio, take items in order until capacity reached.

**Approximation ratio**: \u2265 1/2 of optimal.

### 12.5 Convex Function

f is convex iff for all x, y and \u03bb \u2208 [0, 1]:

    f(\u03bbx + (1-\u03bb)y) \u2264 \u03bbf(x) + (1-\u03bbf(y)

### 12.6 Gradient Descent

    x\u209c\u208a\u2081 = x\u209c - \u03b1\u209c \u2207f(x\u209c)

Convergence rate: O(1/t) for convex, O(e^{-t}) for strongly convex.

### 12.7 Newton's Method

    x\u209c\u208a\u2081 = x\u209c - [\u2207\u00b2f(x\u209c)]\u207b\u00b9 \u2207f(x\u209c)

Quadratic convergence near optimum.

### 12.8 Pareto Optimality

x* is Pareto optimal if no other x dominates it, where x dominates y iff:

    \u2200i: f\u208i(x) \u2264 f\u208i(y)  AND  \u2203j: f\u208b(x) < f\u208b(y)

### 12.9 Weighted Sum Scalarization

    min  \u03a3\u208i w\u208i f\u208i(x)
    s.t. constraints

For convex problems, finds Pareto-optimal points.

### 12.10 Lagrangian Relaxation

Relax integer constraints:

    min  f(x)
    s.t. g\u208i(x) \u2264 0  \u2192  min f(x) + \u03a3\u208i \u03bb\u208i max(0, g\u208i(x))

---

## 13. Linear Algebra Equations

### 13.1 SVD Decomposition

    A = U \u03a3 V\u1d4c

Where:
- U: left singular vectors (orthogonal)
- \u03a3: diagonal of singular values
- V: right singular vectors (orthogonal)

### 13.2 Low-Rank Approximation (Eckart-Young)

    A\u209b = U[:, :k] \u00b7 \u03a3[:k, :k] \u00b7 V[:, :k]\u1d4c

Minimizes \u2016A - A\u209b\u2016_F over all rank-k matrices.

### 13.3 QR Decomposition

    A = Q R

Where Q is orthogonal and R is upper triangular.

### 13.4 Cholesky Decomposition

For symmetric positive definite A:

    A = L L\u1d4c

### 13.5 PCA

    X_centered = X - \u03bc
    C = (1/n) X_centered\u1d4c X_centered
    eigvals, eigvecs = eig(C)
    X_pca = X_centered @ eigvecs[:, :k]

### 13.6 Condition Number

    \u03ba(A) = \u03c3_max / \u03c3_min

Higher \u03ba \u2192 more ill-conditioned \u2192 numerical instability.

### 13.7 Matrix Norm

    \u2016A\u2016_F = \u221a(\u03a3\u208i\u208b |a\u208i\u208b|\u00b2)    (Frobenius)
    \u2016A\u2016\u2082 = \u03c3_max              (Spectral)

---

## 14. Computational Geometry Equations

### 14.1 Convex Hull

The smallest convex polygon containing all points:

    CH(P) = {\u03a3\u208i \u03bb\u208i p\u208i : \u03bb\u208i \u2265 0, \u03a3\u03bb\u208i = 1, p\u208i \u2208 P}

### 14.2 Voronoi Cell

    Vor(p\u208i) = {x : \u2016x - p\u208i\u2016 \u2264 \u2016x - p\u208b\u2016 for all j}

### 14.3 KD-Tree

For k-dimensional data, KD-tree recursively partitions:

    Split on median of dimension d (cycling d = (d+1) mod k)

### 14.4 Point-in-Polygon (Ray Casting)

For point p and polygon with vertices v\u2081, ..., v\u209c:

    inside = \u03a3\u208i sign((v\u208i,\u2081 - p.y) \u00b7 (v\u208i\u208a\u2081,\u2080 - v\u208i,\u2080) - (v\u208i,\u2080 - p.x) \u00b7 (v\u208i\u208a\u2081,\u2081 - v\u208i,\u2081))

### 14.5 Line-Line Intersection

For lines p\u2081p\u2082 and p\u2083p\u2084:

    t = ((p\u2081.x - p\u2083.x)(p\u2083.y - p\u2084.y) - (p\u2081.y - p\u2083.y)(p\u2083.x - p\u2084.x)) / denom
    u = -((p\u2081.x - p\u2082.x)(p\u2081.y - p\u2083.y) - (p\u2081.y - p\u2082.y)(p\u2081.x - p\u2083.x)) / denom

Where denom = (x\u2081-x\u2082)(y\u2083-y\u2084) - (y\u2081-y\u2082)(x\u2083-x\u2084)

Intersection iff 0 \u2264 t \u2264 1 and 0 \u2264 u \u2264 1.

### 14.6 Polygon Area (Shoelace Formula)

    A = \u00bd |\u03a3\u208i (x\u208iy\u208i\u208a\u2081 - x\u208i\u208a\u2081y\u208i)|

---

## 15. Information Economics Equations

### 15.1 Token Economics (TEC)

    TEC = Answer_Quality / Tokens_Used

Goal: maximize.

### 15.2 Memory Economics (MEC)

    MEC = Useful_Data_MB / Total_Memory_MB

### 15.3 Information Economics (IEC)

    IEC = Useful_Information_Bits / Total_Storage_Bits

### 15.4 Retrieval Economics (REC)

    REC = Correct_Retrievals / Total_Operations

### 15.5 Agent Economics (AEC)

    AEC = Answer_Quality / Agent_Cost_USD

### 15.6 Composite Score

    Score = w\u2081\u00b7TEC + w\u2082\u00b7MEC + w\u2083\u00b7REC + w\u2084\u00b7AEC

With weights summing to 1.

---

## 16. Decision Theory Equations

### 16.1 Expected Utility

    E[U(a)] = \u03a3\u208c P(s) \u00b7 U(a, s)

Where:
- a: action
- s: state
- P(s): probability of state
- U(a, s): utility of action in state

### 16.2 Bayesian Decision

    a* = argmax_a E[U(a) | evidence]

    = argmax_a \u03a3\u208c P(s | evidence) \u00b7 U(a, s)

### 16.3 Multi-Armed Bandit

For action a\u208i with reward distribution N(\u03bc\u208i, \u03c3\u208i\u00b2):

    UCB(a\u208i) = \u03bc\u0302\u208i + c \u221a(log t / n\u208i)

Select a* = argmax UCB(a\u208i).

### 16.4 Reinforcement Learning

State-value function:

    V^\u03c0(s) = E[\u03a3\u209c \u03b3\u209c r\u209c | s\u2080 = s, \u03c0]

Q-function:

    Q^\u03c0(s, a) = E[\u03a3\u209c \u03b3\u209c r\u209c | s\u2080 = s, a\u2080 = a, \u03c0]

Bellman equation:

    Q*(s, a) = E[r + \u03b3 max_{a'} Q*(s', a')]

---

## 17. Key Theorems Summary

### 17.1 Theorem (Information Preservation)

**Statement**: Multi-representation encoding preserves \u2265 95% of source information.

    IR = |retained_info| / |original_info| \u2265 0.95

### 17.2 Theorem (Adaptive Fusion Optimality)

**Statement**: For convex loss functions, the weighted-sum fusion with learned weights
converges to Pareto-optimal solutions.

### 17.3 Theorem (Compression Bound)

**Statement**: Token reduction ratio is bounded below by the entropy of the question:

    TR \u2265 H(Q) / L_baseline

Where L_baseline is the naive token count and H(Q) is question entropy.

### 17.4 Theorem (Template Compression)

**Statement**: For a document with n template repetitions, compression ratio is:

    CR \u2264 1/n + O(log(p_max)/|T|)

### 17.5 Theorem (Spectral Gap & Mixing)

**Statement**: Mixing time of a Markov chain satisfies:

    t_mix \u2264 (1/\u03b3) \u00b7 log(1/(\u03b5 \u00b7 \u03c0_min))

Where \u03b3 is spectral gap and \u03c0_min is minimum stationary probability.

### 17.6 Theorem (Retrieval Improvement)

**Statement**: Multi-signal retrieval with optimal fusion satisfies:

    nDCG_fused \u2265 \u03a3\u208i w\u208i \u00b7 nDCG\u208i - \u03b5

For small \u03b5 > 0 when weights are optimal.

---

## 18. Coordinate Transformations

### 18.1 Cartesian to Polar

    r = \u221a(x\u00b2 + y\u00b2)
    \u03b8 = arctan(y/x)

### 18.2 Rotation

    [x']   [cos \u03b8  -sin \u03b8] [x]
    [y'] = [sin \u03b8   cos \u03b8] [y]

### 18.3 Scaling

    [x']   [sx   0] [x]
    [y'] = [0   sy] [y]

### 18.4 Translation

    [x']   [x]   [tx]
    [y'] = [y] + [ty]

### 18.5 Affine Transform

    [x']   [a b] [x]   [tx]
    [y'] = [c d] [y] + [ty]

---

## 19. Hierarchical Coordinates

### 19.1 5-Tuple Definition

    H(e) = (p, s, b, l, t)

Where:
- p: page number
- s: section number
- b: block number
- l: line number
- t: token index

### 19.2 Theorem (Uniqueness)

**Statement**: The 5-tuple H uniquely identifies any token in any document.

**Proof**: Each component is an integer from a unique set.
The Cartesian product of n finite sets of sizes N\u2081, ..., N\u2085 has
N\u2081 \u00b7 N\u2082 \u00b7 N\u2083 \u00b7 N\u2084 \u00b7 N\u2085 distinct elements. \u25a1

### 19.3 Ancestor Function

    ancestor(H) = { (p, s, b, l, 0), (p, s, b, 0, 0), (p, s, 0, 0, 0), (p, 0, 0, 0, 0) }

### 19.4 Depth Function

    depth(H) = 5

(Always 5 in canonical form.)

---

## 20. Complete Theorem Index

| Theorem | Statement |
|---------|-----------|
| 4.1 | Scale invariance of normalized distance |
| 12.1 | Monotonicity of inverse frequency weight |
| 12.2 | Bounds of inverse frequency weight |
| 13.1 | Entropy bounds |
| 21.1 | Uniqueness of 5-tuple hierarchical coordinates |
| 17.1 | Information preservation |
| 17.2 | Adaptive fusion optimality |
| 17.3 | Compression bound |
| 17.4 | Template compression |
| 17.5 | Spectral gap & mixing |
| 17.6 | Retrieval improvement |
| Bottleneck | Persistence stability |
| Parseval | Fourier energy conservation |
| Wavelet Inversion | Wavelet reconstruction |
| Eckart-Young | Optimal low-rank approximation |
| Shannon | Channel capacity existence |
| Gibbs | KL divergence non-negativity |

---

## Appendix A: Notation Reference

| Symbol | Meaning |
|--------|---------|
| \u2208 | Element of |
| \u2286 | Subset of |
| \u2200 | For all |
| \u2203 | There exists |
| \u03a3 | Summation |
| \u03a0 | Product |
| \u222b | Integral |
| \u2202 | Partial derivative |
| \u2207 | Gradient |
| \u2207\u00b2 | Hessian |
| \u2218 | Outer product |
| \u2297 | Tensor product |
| \u2295 | Direct sum |
| \u221e | Infinity |
| \u2192 | Maps to |
| \u21d2 | Implies |
| \u21d4 | If and only if |
| \u221d | Proportional to |
| \u2248 | Approximately equal |
| \u2261 | Defined as |

## Appendix B: Acronyms

- AMDI: Adaptive Mathematical Document Intelligence
- MIOS: Mathematical Information Operating System
- TEC: Token Economics Coefficient
- MEC: Memory Economics Coefficient
- IEC: Information Economics Coefficient
- REC: Retrieval Economics Coefficient
- AEC: Agent Economics Coefficient
- RAG: Retrieval-Augmented Generation
- IE: Information Energy
- IoU: Intersection over Union
- KKT: Karush-Kuhn-Tucker
- HMM: Hidden Markov Model
- SVD: Singular Value Decomposition
- PCA: Principal Component Analysis
- DBSCAN: Density-Based Spatial Clustering
- BM25: Best Matching 25
- TF-IDF: Term Frequency-Inverse Document Frequency
