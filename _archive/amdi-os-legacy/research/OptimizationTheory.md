# AEGIS-AMDI-OS — Optimization Framework

This document details the optimization formulations, Lagrangian multipliers, and resource allocation models that drive the scheduling, context window selection, and weight routing inside **AMDI-OS**.

---

## §1. The Master Optimization Problem

The global objective of AMDI-OS is to minimize resource costs (tokens, memory, latency) while satisfying hard quality constraints (accuracy, information retention, confidence).

$$\text{Minimize } J(w) = \alpha \cdot \text{TC}(w) + \beta \cdot L(w) + \gamma \cdot \text{MC}(w) + \delta \cdot \text{ER}(w)$$

$$\begin{aligned}
\text{Subject to: } \quad & g_1(w) = \text{Accuracy}(w) \ge 0.95 \\
& g_2(w) = \text{IR}(w) \ge 0.95 \\
& g_3(w) = \text{Confidence}(w) \ge 0.90 \\
& \sum_{i=1}^{9} w_i = 1, \quad w_i \ge 0
\end{aligned}$$

Where:
- $\text{TC}$ is Token Cost (Input + Output tokens).
- $L$ is Latency (in seconds).
- $\text{MC}$ is Memory Cost (RAM + Cache).
- $\text{ER}$ is Error Rate ($1 - \text{Accuracy}$).
- $\alpha, \beta, \gamma, \delta > 0$ are the cost weighting parameters.

---

## §2. Lagrangian Formulation

To solve the constrained optimization, we introduce the Lagrangian function:

$$\mathcal{L}(w, \lambda) = J(w) + \lambda_1 (0.95 - \text{Accuracy}(w)) + \lambda_2 (0.95 - \text{IR}(w)) + \lambda_3 (0.90 - \text{Confidence}(w)) - \sum_{i=1}^{9} \mu_i w_i + \eta \left( \sum_{i=1}^{9} w_i - 1 \right)$$

Where:
- $\lambda_1, \lambda_2, \lambda_3 \ge 0$ are the inequality multiplier coefficients.
- $\mu_i \ge 0$ are the non-negativity constraint multipliers.
- $\eta$ is the equality constraint multiplier for weight summation.

---

## §3. Karush-Kuhn-Tucker (KKT) Conditions

The optimal weight allocation vector $w^*$ and multiplier vectors $\lambda^*, \mu^*, \eta^*$ must satisfy the KKT first-order necessary conditions:

### 1. Stationarity
$$\nabla_w \mathcal{L}(w^*, \lambda^*, \mu^*, \eta^*) = 0$$
$$\nabla_w J(w^*) - \lambda_1^* \nabla_w \text{Accuracy}(w^*) - \lambda_2^* \nabla_w \text{IR}(w^*) - \lambda_3^* \nabla_w \text{Confidence}(w^*) - \mu^* + \eta^* \mathbf{1} = 0$$

### 2. Primal Feasibility
$$\text{Accuracy}(w^*) \ge 0.95, \quad \text{IR}(w^*) \ge 0.95, \quad \text{Confidence}(w^*) \ge 0.90, \quad \sum w_i^* = 1, \quad w_i^* \ge 0$$

### 3. Dual Feasibility
$$\lambda_i^* \ge 0, \quad \mu_i^* \ge 0$$

### 4. Complementary Slackness
$$\lambda_1^* (0.95 - \text{Accuracy}(w^*)) = 0$$
$$\lambda_2^* (0.95 - \text{IR}(w^*)) = 0$$
$$\lambda_3^* (0.90 - \text{Confidence}(w^*)) = 0$$
$$\mu_i^* w_i^* = 0 \quad \forall i \in \{1, \dots, 9\}$$

---

## §4. Context Window Selection as 0/1 Knapsack

Selecting which document elements to include in the context window under a token budget limit is formulated as a 0/1 Knapsack problem:

$$\text{Maximize } \sum_{i=1}^{N} v_i x_i$$
$$\text{Subject to } \sum_{i=1}^{N} t_i x_i \le B, \quad x_i \in \{0, 1\}$$

Where:
- $v_i$ is the relevance score of element $E_i$.
- $t_i$ is the token count of element $E_i$.
- $B$ is the maximum token budget ($B = \text{max\_context\_tokens} - \text{reserve\_tokens}$).
- $x_i = 1$ if element $E_i$ is selected, else $0$.

### Greedy Approximation Bound
The greedy algorithm sorts elements by their value-to-weight ratio $v_i / t_i$ and inserts them until the budget is exhausted.
**Theorem 4.1:** The greedy knapsack algorithm provides a $1/2$-approximation ratio. That is:
$$\sum_{i \in \text{greedy}} v_i \ge \frac{1}{2} \cdot \text{OPT}$$
(where $\text{OPT}$ is the value of the optimal DP knapsack selection).

---

## §5. Dynamic Programming Context Solver

For exact context selection without approximation loss, a Dynamic Programming algorithm is used:

### State Space
Let $V(i, q)$ be the maximum value obtained from a subset of elements $\{E_1, \dots, E_i\}$ under a token budget limit $q$:

$$V(i, q) = \begin{cases}
0 & \text{if } i = 0 \text{ or } q = 0 \\
V(i-1, q) & \text{if } t_i > q \\
\max \{ V(i-1, q), \, v_i + V(i-1, q - t_i) \} & \text{if } t_i \le q
\end{cases}$$

The computational complexity of this solver is $\mathcal{O}(N \cdot B)$, which is efficient for typical token budgets ($B \le 4096$).

---

## §6. Linear Programming for Weight Blending

To blend representation layer scores, we solve a linear optimization problem to find coefficients $w$ that match target distributions:

$$\text{Minimize } \| S \cdot w - r \|_2^2$$
$$\text{Subject to } \sum_{i=1}^{9} w_i = 1, \quad w_i \ge 0$$

Where:
- $S \in \mathbb{R}^{N \times 9}$ is the matrix of layer scores (N elements, 9 layers).
- $r \in \mathbb{R}^N$ is the target relevance vector.
- $w \in \mathbb{R}^9$ is the layer weight vector.

---

## §7. Learnable Dynamic Router Policy Loss

In the learnable mode of the Dynamic Router, the MLP parameters $\theta$ are updated to maximize the expected negative cost (equivalent to minimizing J):

$$\theta^* = \arg\min_{\theta} E_{Q \sim \mathcal{D}} [ J(w_\theta(Q)) ]$$

Using policy gradient methods, the parameter updates follow:
$$\nabla_\theta \mathbb{E}[J] = \mathbb{E} \left[ J(w) \cdot \nabla_\theta \log \pi_\theta(w | \phi(Q)) \right]$$

Where:
- $\phi(Q)$ represents the feature vector of the query.
- $\pi_\theta$ is the softmax probability distribution output of the router network.
