# AEGIS-AMDI-OS — Information-Theoretic Analysis

This document presents the information-theoretic framework of **AMDI-OS**, defining how document structures, layouts, and semantics translate to entropy bounds, source coding limits, and channel transmission models.

---

## §1. Document as a Stochastic Information Source

Let a document $D$ be modeled as a stochastic source emitting discrete elements $e_i \in D$ according to a probability distribution $P(e_i)$.

### Self-Information
The self-information (surprisal) of an element $e_i$ is defined as:

$$I(e_i) = -\log_2 P(e_i) \quad \text{[bits]}$$

### Document Source Entropy
The aggregate Shannon entropy of the document source, representing the average uncertainty or information content per emitted element, is:

$$H(D) = -\sum_{e \in D} P(e) \log_2 P(e)$$

---

## §2. Shannon's Source Coding Theorem & Compression Bounds

Shannon's Source Coding Theorem establishes that the expected code length $L$ per element for any lossless compression code is bounded below by the source entropy:

$$H(D) \le L < H(D) + 1$$

### AMDI Spatial-Structural Compression
In AMDI, the layout template $T$ and recurring patterns $R$ are extracted. The compressed representation length (in bits) is:

$$L_{\text{AMDI}} = |T_{\text{unique}}| + |R| \log_2(k) + |U| \cdot \text{size}(e_u)$$

Where:
- $|T_{\text{unique}}|$ is the code length of unique layouts.
- $|R|$ is the count of recurring elements mapped to pages $k$.
- $|U|$ is the set of non-recurring unique elements.

For documents with high structural recurrence ($|R| \gg |U|$), the AMDI representation converges close to the theoretical entropy limit:

$$\lim_{|R| \to \infty} \frac{L_{\text{AMDI}}}{|R|} = \log_2(k) \approx H(D)$$

---

## §3. Mutual Information & Ingestion Channels

The goal of document retrieval is to maximize the mutual information between the user query $Q$ and the retrieved document elements $D_R$, ensuring that maximum relevance is preserved within a constrained token budget.

$$I(D_R; Q) = H(D_R) - H(D_R | Q) = H(Q) - H(Q | D_R)$$

Where:
- $H(D_R | Q)$ is the conditional entropy (remaining uncertainty) of the document content given the query.

### Data Processing Inequality
For the Markov chain representing the ingestion and retrieval process:

$$D \longrightarrow G \longrightarrow D_R \longrightarrow Q$$

(where $D$ is the raw document, $G$ is the AMDI mathematical representation, $D_R$ is retrieved elements, and $Q$ is the query), the Data Processing Inequality guarantees:

$$I(D; Q) \ge I(G; Q) \ge I(D_R; Q)$$

AMDI-OS minimizes the information loss in the step $D \to G$ by preserving geometry, frequency, recurrence, and matrices, keeping $I(G; Q) \approx I(D; Q)$ compared to token-only pipelines.

---

## §4. Channel Capacity of Context Windows

The context window of the Large Language Model acts as a communication channel. The capacity $C$ of the context window channel (under token budget constraint $B$) is:

$$C = \max_{P(D_R): \sum \text{len}(D_R) \le B} I(D_R; A)$$

Where $A$ is the final LLM response. AMDI-OS maximizes this channel capacity by filtering out low-entropy elements ($H(e_i) < \text{threshold}$) and prioritizing elements with high composite density.

---

## §5. Rate-Distortion Limits

When context windows must be compressed below the Shannon bound, we accept a distortion $D$. The Rate-Distortion function $R(D)$ represents the minimum information rate (in bits/token) required to achieve a reconstruction within distortion $D$:

$$R(D) = \min_{P(\hat{D}|D): E[d(D, \hat{D})] \le D} I(D; \hat{D})$$

AMDI-OS traces this rate-distortion curve. By eliminating recurring blocks (headers/footers) and formatting tables as compact matrices, the system drops the rate $R$ (reducing token costs) while keeping the distortion $D$ (fact loss) near zero.

---

## §6. KL Divergence (Layer Importance)

The Kullback-Leibler (KL) divergence measures the difference between the retrieval score distribution of layer $P$ and the uniform distribution $Q$:

$$D_{KL}(P \parallel Q) = \sum_{x \in X} P(x) \log_2 \left( \frac{P(x)}{Q(x)} \right)$$

In AMDI-OS, the KL divergence of each representation layer's scores is used by the router. A high divergence $D_{KL}(P_i \parallel \text{Uniform})$ indicates that layer $P_i$ provides sharp, highly selective filters, whereas a low divergence indicates flat, non-informative scores.

---

## §7. Empirical Entropy in AMDI-OS

For each representation layer $\ell$ (e.g., semantic, frequency, geometry), the empirical entropy is computed over the normalized relevance scores of elements:

$$p_\ell(e_i) = \frac{s_\ell(e_i)}{\sum_{j} s_\ell(e_j)}$$
$$H_\ell = -\sum_{i} p_\ell(e_i) \log_2 p_\ell(e_i)$$

The layer entropy profile ($H_{\text{semantic}}, H_{\text{geometry}}, \dots$) provides direct diagnostics on which mathematical representations carry the highest information density for a specific query.
