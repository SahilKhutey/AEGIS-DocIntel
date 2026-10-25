# Context Packing & Submodular Selection Architecture

## 1. Problem Formulation

The core proposition of AEGIS-DocIntel is to compile heterogeneous, unstructured enterprise documents (PDF, DOCX, XLSX, PPTX) into compact, privacy-aware, and maximally informative prompt contexts for large language models. Given a fixed model context window, feeding raw document tokens naively risks truncating critical information, exceeding budget limits, or diluting attention with repetitive text.

Context packing is formalized as a **Submodular Maximization problem under a Knapsack Constraint**.

---

## 2. Mathematical Model

### 2.1 Inputs and Notation
Let $V = \{1, 2, \dots, n\}$ denote the set of candidate document chunks.
For each chunk $i \in V$:
- $c_i \in \mathbb{Z}^+$: Positive integer token cost of chunk $i$.
- $r_i \ge 0$: Relevance score with respect to the user query $q$.
- $v_i \in \mathbb{R}^d$: Dense unit-normalized embedding vector of chunk $i$.
- $B \in \mathbb{Z}^+$: Total available token budget for context.

### 2.2 Token Budget Derivation
The available context budget $B$ is derived from the model's physical context window $W$ by subtracting mandatory system components and safety margins:

$$B = W - T_{\text{instructions}} - T_{\text{query}} - T_{\text{reserved\_output}} - T_{\text{overhead}}$$

Where:
- $W$: Maximum context window (e.g. 8,192 or 32,768 tokens).
- $T_{\text{instructions}}$: Static prompt instructions and role definitions.
- $T_{\text{query}}$: Token length of user question.
- $T_{\text{reserved\_output}}$: Guaranteed token allocation for generated answer tokens.
- $T_{\text{overhead}}$: Formatting delimiters, JSON schemas, and safety buffer.

If the derived budget $B \le 0$, the packing engine clamps $B = 0$ and cleanly abstains.

### 2.3 Objective Function
The selection objective $f(S): 2^V \to \mathbb{R}_{\ge 0}$ balances semantic diversity coverage and direct query relevance:

$$f(S) = \alpha \cdot \text{Coverage}(S) + \beta \cdot \text{Relevance}(S)$$

Where:
- $\text{Coverage}(S) = \sum_{j \in V} \max_{i \in S} \text{sim}(v_i, v_j)$ (Facility Location function).
- $\text{Relevance}(S) = \sum_{i \in S} r_i$.
- $\alpha \ge 0, \beta \ge 0$ are hyperparameter trade-off weights ($\alpha + \beta = 1.0$).

### 2.4 Non-Negative Similarity Metrics
Standard cosine similarity $\cos(u, v) = \frac{u \cdot v}{\|u\| \|v\|} \in [-1, 1]$ contains negative values that violate the monotonicity of submodular functions. AEGIS provides two strictly non-negative transformations:

1. **Clipped Cosine**:
   $$\text{sim}_{\text{clipped}}(u, v) = \max(0.0, \cos(u, v))$$
2. **Affine Cosine**:
   $$\text{sim}_{\text{affine}}(u, v) = \frac{1 + \cos(u, v)}{2} \in [0, 1]$$

Both transformations preserve ordering while ensuring $f(S)$ is monotone non-decreasing: $f(A) \le f(B)$ whenever $A \subseteq B$.

---

## 3. Submodular Knapsack Optimization

### 3.1 Knapsack Constraint
$$\sum_{i \in S} c_i \le B$$

### 3.2 Approximation Guarantee (Theorem 9.1)
Maximizing a monotone submodular function subject to a knapsack constraint is NP-hard.
A naive greedy algorithm choosing items by marginal gain $\Delta(e \mid S) = f(S \cup \{e\}) - f(S)$ can perform arbitrarily poorly when high-gain items have disproportionately high costs.
Choosing items strictly by density $\frac{\Delta(e \mid S)}{c_e}$ can also fail if the single best item cannot fit in the remaining budget.

**Theorem (Krause & Golovin, 2014):**
Let $S_{\text{density}}$ be the greedy density solution, and let $s^* = \arg\max_{e \in V, c_e \le B} f(\{e\})$ be the best feasible single item. The combined selection:

$$S = \arg\max \left( f(S_{\text{density}}), f(\{s^*\}) \right)$$

guarantees a constant-factor approximation:

$$f(S) \ge \frac{1 - 1/e}{2} f(S^*) \approx 0.316 \cdot f(S^*)$$

Where $S^*$ is the optimal combinatorial solution.

---

## 4. Implementation Details

1. **Input Validation (`validate_packing_inputs`)**:
   - Asserts non-empty candidates and $B > 0$.
   - Asserts all token costs $c_i \in \mathbb{Z}^+$ ($c_i \ge 1$).
   - Asserts 2D embeddings with matching dimensions.
2. **Deterministic Tie-Breaking**:
   - Equal marginal density values are deterministically broken using `(-marginal_gain, token_cost, chunk_id)` so results are 100% reproducible across operating systems and execution runs.
3. **Hard Budget Safety Check**:
   - As an invariant guard, before returning, the packer verifies $\sum_{i \in S} c_i \le B$. Any violation raises `ContextBudgetExceededError`.
