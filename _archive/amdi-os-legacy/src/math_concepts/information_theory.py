'''
AEGIS-MIOS — Information Theory
=================================
Information theory calculations:
- Shannon Entropy (distributions and text)
- Mutual Information (MI)
- Kullback-Leibler (KL) Divergence
- Channel Capacity (Blahut-Arimoto algorithm)
'''

from __future__ import annotations

import numpy as np


def shannon_entropy(probabilities: np.ndarray) -> float:
    '''
    Compute Shannon entropy of a probability distribution.
    H(P) = -Σ P_i log2(P_i)
    '''
    p = probabilities / np.sum(probabilities) if np.sum(probabilities) != 1.0 else probabilities
    p = p[p > 0.0]
    return float(-np.sum(p * np.log2(p)))


def text_entropy(text: str) -> float:
    '''Compute character-level Shannon entropy of a text string.'''
    if not text:
        return 0.0
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    total = len(text)
    probs = np.array([count / total for count in char_counts.values()])
    return shannon_entropy(probs)


def mutual_information(p_xy: np.ndarray) -> float:
    '''
    Compute Mutual Information from a joint probability distribution matrix P(X, Y).
    I(X; Y) = Σ_x Σ_y P(x, y) log2( P(x, y) / ( P(x) P(y) ) )
    '''
    # Marginal distributions
    p_x = np.sum(p_xy, axis=1)
    p_y = np.sum(p_xy, axis=0)

    mi = 0.0
    n_rows, n_cols = p_xy.shape
    for i in range(n_rows):
        for j in range(n_cols):
            val = p_xy[i, j]
            if val > 0:
                denominator = p_x[i] * p_y[j]
                if denominator > 0:
                    mi += val * np.log2(val / denominator)
    return float(mi)


def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    '''
    Compute Kullback-Leibler divergence D_KL(P || Q).
    D_KL = Σ P_i log2(P_i / Q_i)
    '''
    assert p.shape == q.shape, 'Distributions must have same shape'
    # Normalize
    p_norm = p / np.sum(p)
    q_norm = q / np.sum(q)

    # Avoid division by zero and log of zero
    mask = p_norm > 0
    kl = np.sum(p_norm[mask] * np.log2(p_norm[mask] / (q_norm[mask] + 1e-15)))
    return float(kl)


def blahut_arimoto(
    transition_matrix: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-6,
) -> tuple[float, np.ndarray]:
    '''
    Compute Channel Capacity of a discrete memoryless channel using the Blahut-Arimoto algorithm.
    transition_matrix P(Y|X) of shape (n_inputs, n_outputs).
    Returns (capacity_bits, optimal_input_distribution).
    '''
    P = transition_matrix
    n_inputs, n_outputs = P.shape

    # Initialize input probability distribution p(x) uniformly
    p = np.ones(n_inputs) / n_inputs

    for _ in range(max_iter):
        # Compute joint probabilities Q(x, y) = p(x) P(y|x)
        # and conditional transition probabilities back: r(x|y) = p(x) P(y|x) / Σ p(x') P(y|x')
        p_y = p @ P  # shape (n_outputs,)
        p_y = np.maximum(p_y, 1e-15)

        # r_xy[i, j] = P[i, j] * p[i] / p_y[j]
        r = P * p[:, np.newaxis] / p_y[np.newaxis, :]

        # Update input distribution: p_new[i] ~ exp( Σ_j P[i, j] log( r[i, j] ) )
        # Using base 2 log for bits
        # Avoid log(0)
        c = np.zeros(n_inputs)
        for i in range(n_inputs):
            exponent = 0.0
            for j in range(n_outputs):
                if P[i, j] > 0 and r[i, j] > 0:
                    exponent += P[i, j] * np.log2(r[i, j])
            c[i] = np.exp2(exponent)

        p_new = c / np.sum(c)

        if np.linalg.norm(p_new - p, 1) < tol:
            p = p_new
            break
        p = p_new

    # Compute capacity: C = I(X; Y) with optimal input distribution p
    p_y = p @ P
    p_y = np.maximum(p_y, 1e-15)
    capacity = 0.0
    for i in range(n_inputs):
        for j in range(n_outputs):
            if P[i, j] > 0 and p[i] > 0:
                capacity += p[i] * P[i, j] * np.log2(P[i, j] / p_y[j])

    return float(capacity), p
