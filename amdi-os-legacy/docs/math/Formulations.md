# AEGIS-AMDI-OS — Master Formulations Reference

**Version**: 1.0  
**Status**: Production

---

## Quick Reference: All Key Equations

### 1. Element Definition

    eᵢ = (xᵢ, yᵢ, wᵢ, hᵢ, pᵢ, θᵢ, tᵢ, cᵢ)

### 2. Coordinate Normalization

    x̃ = x / W, ỹ = y / H, w̃ = w / W, h̃ = h / H

### 3. Distance

    d(i, j) = √[(xᵢ-xⱼ)² + (yᵢ-yⱼ)²] + λ_page·|pᵢ-pⱼ|

### 4. Alignment

    A(i, j) = [1 - |xᵢ-xⱼ|/W + 1 - |yᵢ-yⱼ|/H] / 2

### 5. Recurrence

    Rₙ = Rₙ₋₁,  n > 0

### 6. Frequency Weight

    I_f(x) = 1 / (1 + log(1 + f(x)))

### 7. Entropy

    H(X) = -Σₓ P(x) log₂ P(x)

### 8. Mutual Information

    I(X; Y) = H(X) + H(Y) - H(X, Y)

### 9. KL Divergence

    D_KL(P || Q) = Σₓ P(x) log[P(x)/Q(x)]

### 10. Graph Adjacency

    A[i, j] = 1 iff (i, j) ∈ E

### 11. Betti Numbers

    βₙ = rank(Hₙ(K)) = rank(ker ∂ₙ) - rank(im ∂ₙ₊₁)

### 12. Euler Characteristic

    χ(K) = Σₙ (-1)ⁿ · |Kₙ| = Σₙ (-1)ⁿ βₙ

### 13. Information Energy

    IE(e) = H(e) · R(e)

### 14. Information Gravity

    G(i) = (I(i) · C(i)) / d(i)²

### 15. Information Field

    Φ(x) = Σ... W(i) / ‖x - pᵢ‖²

### 16. Tensor Mode-n Product

    (T ×ₙ M)[...] = Σ T[...] · M[j, iₙ]

### 17. Tucker Decomposition

    T ≈ G ×₁ U⁽¹⁾ ×₂ U⁽²⁾ × ... ×ₙ U⁽ᴺ⁾

### 18. Spectral Decomposition

    A = U Λ Vᵀ

### 19. Wavelet Transform

    W(a, b) = (1/√a) ∫ f(t) ψ*((t-b)/a) dt

### 20. Bayes' Theorem

    P(A|B) = P(B|A)·P(A) / P(B)

### 21. Markov Property

    P(X_{t+1} | X_t, ..., X_0) = P(X_{t+1} | X_t)

### 22. PageRank

    π = (1-d)/N · 1 + d · D⁻¹Aπ

### 23. Optimization Objective

    min J = α·TC + β·L + γ·MC + δ·ER
    s.t. Accuracy ≥ 0.95, IR ≥ 0.95

### 24. Adaptive Fusion

    R(Q, D) = Σ... w_i(Q) · s_i(Q, D)
    w_i(Q) = softmax(MLP(φ(Q)))[i]

### 25. Context Knapsack

    max  Σᵢ vᵢxᵢ
    s.t. Σᵢ cᵢxᵢ ≤ B

### 26. Cosine Similarity

    sim(a, b) = (a·b) / (‖a‖·‖b‖)

### 27. SVD Reconstruction

    Aₖ = Σ... σᵢuᵢvᵢᵀ

### 28. PCA

    X_pca = X_centered @ eigvecs[:, :k]

### 29. Conservation Law

    I_in = I_out + I_compressed + I_discarded

### 30. Token Economics

    TEC = Answer_Quality / Tokens

---

## Index by Domain

### Geometry (G)
- E1: Element definition
- E2: Normalization
- E3: Distance
- E4: Alignment
- E5: Area Ratio (Importance)

### Recurrence (R)
- R1: Rₙ = Rₙ₋₁
- R2: Storage optimization
- R3: Hash detection

### Frequency (F)
- F1: Inverse frequency
- F2: TF-IDF
- F3: Composite weight

### Entropy & Information (E)
- E1: Shannon entropy
- E2: Joint/conditional entropy
- E3: Mutual information
- E4: KL/JS divergence
- E5: Channel capacity

### Graph (X)
- X1: Adjacency matrix
- X2: Degree
- X3: Centrality
- X4: PageRank
- X5: Laplacian
- X6: Spectral decomposition

### Topology (T)
- T1: Simplicial complex
- T2: Betti numbers
- T3: Euler characteristic
- T4: Persistent homology
- T5: Bottleneck distance

### Optimization (O)
- O1: Objective function
- O2: Lagrange multipliers
- O3: KKT conditions
- O4: Knapsack
- O5: Pareto optimality
- O6: Gradient descent

### Tensor (M)
- M1: Tensor definition
- M2: Mode-n product
- M3: CP decomposition
- M4: Tucker decomposition
- M5: HOSVD

### Spectral (S)
- S1: Fourier transform
- S2: Power spectrum
- S3: Eigenvalue decomposition
- S4: Wavelet transform

### Information Physics (P)
- P1: Information energy
- P2: Information gravity
- P3: Information field
- P4: Conservation law

### Probability (B)
- B1: Bayes' theorem
- B2: Chain rule
- B3: Independence
- B4: Markov property
- B5: Stationary distribution
- B6: HMM forward/Viterbi

### Adaptive Fusion (F)
- F1: Multi-layer retrieval
- F2: Dynamic weights
- F3: Weighted sum

### Economics (C)
- C1: Token economics
- C2: Memory economics
- C3: Retrieval economics
- C4: Agent economics

---

## Numerical Constants

| Symbol | Value | Meaning |
|--------|-------|---------|
| ε | 10⁻⁸ | Numerical stability |
| γ (spectral) | varies | Spectral gap |
| λ_page | 1.5 | Cross-page distance penalty |
| τ_damp | 0.85 | PageRank damping |
| T_threshold | 0.5 | Periodicity threshold |
| σ_threshold | 5 | Template cluster size |

---

## Notation Conventions

- **Scalars**: lowercase italic (x, y, n)
- **Vectors**: lowercase bold (x, w)
- **Matrices**: uppercase bold (A, M)
- **Tensors**: uppercase bold script (𝒯) or calligraphic (𝒯)
- **Sets**: uppercase italic (X, V)
- **Functions**: lowercase (f, h)
- **Operators**: calligraphic or special (ℒ, ℋ)

---

## File-by-File Reference

| File | Equations |
|------|-----------|
| `src/engines/geometry.py` | E1-E5 |
| `src/engines/recurrence.py` | R1-R3 |
| `src/engines/frequency.py` | F1-F3 |
| `src/engines/matrix.py` | M1-M5 (basic) |
| `src/engines/template.py` | DBSCAN-based |
| `src/engines/graph.py` | X1-X6 |
| `src/engines/semantic.py` | E1-E3 |
| `src/engines/fusion.py` | F1-F3 (fusion) |
| `src/engines/context.py` | O4 (knapsack) |
| `src/mios/physics.py` | P1-P4 |
| `src/mios/topology.py` | T1-T5 |
| `src/mios/spectral.py` | S1-S4 |
| `src/mios/tensor.py` | M1-M5 |
| `src/mios/probability.py` | B1-B6 |
| `src/mios/optimization.py` | O1-O6 |
| `src/mios/linear_algebra.py` | SVD, PCA, etc. |
| `src/mios/economics.py` | C1-C4 |

---

## Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial formulation set |
