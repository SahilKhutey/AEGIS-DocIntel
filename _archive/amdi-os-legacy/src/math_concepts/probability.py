'''
AEGIS-MIOS — Probability & Stochastic Processes
=================================================
Probability engine with:
- Bayesian Belief Updating (Beta Conjugate Prior)
- Bayesian Networks (Variable Elimination)
- Markov Chains (Transition, Stationarity, Spectral Gap, Mixing Time)
- Hidden Markov Models (Forward algorithm, Viterbi decoding)
'''

from __future__ import annotations

from collections import defaultdict
import numpy as np


# ============================================================
# §1. BAYESIAN INFERENCE
# ============================================================

class BayesianInference:
    '''
    Bayesian belief updating with sequential observations.
    Beta distribution conjugate prior for Bernoulli trials.
    '''

    def __init__(self, prior: float = 0.5):
        self.prior = prior
        self.alpha = prior * 2.0 + 1.0
        self.beta_param = (1.0 - prior) * 2.0 + 1.0

    def update(self, likelihood: float, evidence: float = 0.5) -> float:
        '''Bayesian update step.'''
        numerator = likelihood * self.prior
        denominator = evidence if evidence > 0 else 1e-9
        self.prior = min(1.0, max(0.0, numerator / denominator))
        self.alpha += likelihood
        self.beta_param += (1.0 - likelihood)
        return self.prior

    def sequential_update(self, likelihoods: list[float], evidence: float = 0.5) -> float:
        '''Update model sequentially over multiple observations.'''
        for lh in likelihoods:
            self.update(lh, evidence)
        return self.prior

    def posterior_mean(self) -> float:
        '''Mean of the Beta posterior distribution.'''
        return self.alpha / (self.alpha + self.beta_param)

    def credible_interval(self, alpha_level: float = 0.05) -> tuple[float, float]:
        '''Equal-tailed credible interval using scipy.stats.beta.'''
        from scipy.stats import beta
        lower = beta.ppf(alpha_level / 2.0, self.alpha, self.beta_param)
        upper = beta.ppf(1.0 - alpha_level / 2.0, self.alpha, self.beta_param)
        return float(lower), float(upper)


class BayesianNetwork:
    '''Simple discrete Bayesian Network with variable elimination representation.'''

    def __init__(self):
        self.nodes: dict[str, list] = {}
        self.parents: dict[str, list] = defaultdict(list)
        self.children: dict[str, list] = defaultdict(list)
        self.cpts: dict[tuple, dict] = {}

    def add_node(self, name: str, states: list) -> None:
        '''Add node to the network.'''
        self.nodes[name] = states

    def add_edge(self, parent: str, child: str, cpt: dict | None = None) -> None:
        '''Add directed edge between nodes.'''
        if parent not in self.nodes or child not in self.nodes:
            raise ValueError('Unknown node')
        self.parents[child].append(parent)
        self.children[parent].append(child)
        if cpt:
            self.cpts[(parent, child)] = cpt

    def query(self, target: str, evidence: dict | None = None) -> dict:
        '''Compute marginal distribution P(target | evidence) using variable elimination.'''
        evidence = evidence or {}
        result = {state: 0.0 for state in self.nodes[target]}
        for target_state in self.nodes[target]:
            full_assignment = {**evidence, target: target_state}
            prob = 1.0
            for node in self.nodes:
                parent_states = tuple(full_assignment[p] for p in self.parents[node])
                if not self.parents[node]:
                    prob *= 1.0 / len(self.nodes[node])
                else:
                    cpt = None
                    for (par, ch), c in self.cpts.items():
                        if ch == node and (par == parent_states[0] or parent_states in c):
                            cpt = c
                            break
                    if cpt:
                        # Fallback simple dictionary mapping
                        if parent_states in cpt:
                            prob *= cpt[parent_states].get(full_assignment[node], 0.0)
                        elif parent_states[0] in cpt:
                            prob *= cpt[parent_states[0]].get(full_assignment[node], 0.0)
                        else:
                            prob *= 1.0 / len(self.nodes[node])
                    else:
                        prob *= 1.0 / len(self.nodes[node])
            result[target_state] = prob

        total = sum(result.values())
        if total > 0:
            result = {k: v / total for k, v in result.items()}
        return result


# ============================================================
# §2. MARKOV CHAINS
# ============================================================

class MarkovChain:
    '''
    Discrete Time Markov Chain (DTMC) representation.
    Transition dynamics, stationarity, mixing properties.
    '''

    def __init__(self, states: list[str], transition_matrix: np.ndarray | None = None):
        self.states = states
        self.n = len(states)
        self.state_to_idx = {s: i for i, s in enumerate(states)}
        self.idx_to_state = {i: s for i, s in enumerate(states)}
        if transition_matrix is not None:
            self.P = transition_matrix
        else:
            self.P = np.ones((self.n, self.n)) / self.n

    @classmethod
    def from_sequences(cls, sequences: list[list[str]], smoothing: float = 0.01) -> MarkovChain:
        '''Train a Markov Chain transition matrix from observable sequences.'''
        all_states = set()
        for seq in sequences:
            all_states.update(seq)
        states = sorted(all_states)
        n = len(states)
        idx = {s: i for i, s in enumerate(states)}
        counts = np.full((n, n), smoothing)
        for seq in sequences:
            for i in range(len(seq) - 1):
                if seq[i] in idx and seq[i + 1] in idx:
                    counts[idx[seq[i]], idx[seq[i + 1]]] += 1.0
        T = counts / counts.sum(axis=1, keepdims=True)
        return cls(states, T)

    def stationary_distribution(self, max_iter: int = 1000, tol: float = 1e-8) -> np.ndarray:
        '''Power iteration method for stationary distribution: π P = π.'''
        pi = np.ones(self.n) / self.n
        for _ in range(max_iter):
            pi_new = pi @ self.P
            if np.linalg.norm(pi_new - pi) < tol:
                break
            pi = pi_new
        return pi

    def spectral_gap(self) -> float:
        '''Compute spectral gap of the transition matrix (1 - |λ_2|).'''
        eigvals = np.linalg.eigvals(self.P)
        eigvals = np.sort(np.abs(eigvals))[::-1]
        if len(eigvals) > 1:
            return float(eigvals[0] - eigvals[1])
        return 0.0

    def mixing_time(self, epsilon: float = 0.01) -> int:
        '''Estimate mixing time bounded by spectral gap.'''
        gap = self.spectral_gap()
        if gap <= 0:
            return 999999
        pi = self.stationary_distribution()
        pi_min = pi.min() if pi.min() > 0 else 1e-5
        return int(np.ceil(np.log(1.0 / (epsilon * pi_min)) / gap))

    def simulate(self, n_steps: int, start_state: str | None = None) -> list[str]:
        '''Simulate a trajectory path of length n_steps.'''
        path = []
        current_idx = self.state_to_idx.get(start_state, np.random.choice(self.n))
        for _ in range(n_steps):
            path.append(self.idx_to_state[current_idx])
            current_idx = np.random.choice(self.n, p=self.P[current_idx])
        return path

    def entropy_rate(self) -> float:
        '''Entropy rate: H = -Σ_i π_i Σ_j P_ij log2(P_ij)'''
        pi = self.stationary_distribution()
        H = 0.0
        for i in range(self.n):
            for j in range(self.n):
                if self.P[i, j] > 0:
                    H -= pi[i] * self.P[i, j] * np.log2(self.P[i, j])
        return H


# ============================================================
# §3. HIDDEN MARKOV MODELS
# ============================================================

class HiddenMarkovModel:
    '''Hidden Markov Model with discrete observation symbols.'''

    def __init__(self, n_states: int, n_observations: int):
        self.n_states = n_states
        self.n_observations = n_observations
        self.pi = np.ones(n_states) / n_states
        self.A = np.ones((n_states, n_states)) / n_states
        self.B = np.ones((n_states, n_observations)) / n_observations

    def forward(self, observations: list[int]) -> np.ndarray:
        '''Compute forward probability matrix α_t(i) = P(O_1...O_t, q_t=i).'''
        T = len(observations)
        alpha = np.zeros((T, self.n_states))
        alpha[0] = self.pi * self.B[:, observations[0]]
        for t in range(1, T):
            for s in range(self.n_states):
                alpha[t, s] = self.B[s, observations[t]] * np.sum(
                    alpha[t - 1] * self.A[:, s]
                )
        return alpha

    def viterbi(self, observations: list[int]) -> tuple[list[int], float]:
        '''Compute most probable hidden state sequence using Viterbi algorithm.'''
        T = len(observations)
        v = np.zeros((T, self.n_states))
        path = np.zeros((T, self.n_states), dtype=int)

        v[0] = np.log(self.pi + 1e-9) + np.log(self.B[:, observations[0]] + 1e-9)
        for t in range(1, T):
            for s in range(self.n_states):
                seq_probs = v[t - 1] + np.log(self.A[:, s] + 1e-9)
                path[t, s] = np.argmax(seq_probs)
                v[t, s] = seq_probs[path[t, s]] + np.log(self.B[s, observations[t]] + 1e-9)

        # Traceback path
        best_last_state = int(np.argmax(v[T - 1]))
        state_seq = [best_last_state]
        for t in range(T - 1, 0, -1):
            best_last_state = path[t, best_last_state]
            state_seq.insert(0, best_last_state)

        return state_seq, float(np.max(v[T - 1]))
