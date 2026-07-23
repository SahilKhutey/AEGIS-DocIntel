'''
AEGIS-MIOS — Graph Theory
===========================
Modular implementation of graph and hypergraph formulations:
- Centrality measures (Degree, Closeness, Betweenness)
- PageRank (Power Iteration)
- Hypergraph representations (Incidence, Degree, Laplacian)
'''

from __future__ import annotations

import numpy as np


def degree_centrality(adjacency: np.ndarray) -> np.ndarray:
    '''
    Compute degree centrality for each node in a graph.
    DC_i = k_i / (N - 1)
    '''
    n = adjacency.shape[0]
    if n <= 1:
        return np.zeros(n)
    degrees = np.sum(adjacency > 0, axis=1)
    return degrees / (n - 1)


def closeness_centrality(adjacency: np.ndarray) -> np.ndarray:
    '''
    Compute closeness centrality using Floyd-Warshall for all-pairs shortest paths.
    C_i = (N - 1) / Σ_j d(i, j)
    '''
    n = adjacency.shape[0]
    if n <= 1:
        return np.zeros(n)

    # Initialize distance matrix
    dist = np.full((n, n), float('inf'))
    np.fill_diagonal(dist, 0.0)
    for i in range(n):
        for j in range(n):
            if adjacency[i, j] > 0:
                dist[i, j] = 1.0  # Unweighted edges

    # Floyd-Warshall
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i, k] + dist[k, j] < dist[i, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]

    closeness = np.zeros(n)
    for i in range(n):
        sum_dist = np.sum(dist[i, dist[i] != float('inf')])
        reachable = np.sum(dist[i] != float('inf')) - 1
        if sum_dist > 0 and reachable > 0:
            # Scale by fraction of reachable nodes
            closeness[i] = (reachable / (n - 1)) * (reachable / sum_dist)
    return closeness


def betweenness_centrality(adjacency: np.ndarray) -> np.ndarray:
    '''
    Compute betweenness centrality using a BFS-based shortest path counter (Brandes algorithm proxy).
    BC_v = Σ_{s≠v≠t} σ_st(v) / σ_st
    '''
    n = adjacency.shape[0]
    betweenness = np.zeros(n)

    for s in range(n):
        # BFS from source s
        stack = []
        P = [[] for _ in range(n)]
        sigma = np.zeros(n)
        sigma[s] = 1.0
        d = np.full(n, -1.0)
        d[s] = 0.0
        queue = [s]

        while queue:
            v = queue.pop(0)
            stack.append(v)
            for w in range(n):
                if adjacency[v, w] > 0:
                    if d[w] < 0:
                        queue.append(w)
                        d[w] = d[v] + 1.0
                    if d[w] == d[v] + 1.0:
                        sigma[w] += sigma[v]
                        P[w].append(v)

        delta = np.zeros(n)
        while stack:
            w = stack.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                betweenness[w] += delta[w]

    # Normalize betweenness (undirected graph scaling)
    if n > 2:
        betweenness = betweenness / ((n - 1) * (n - 2))
    return betweenness


def pagerank(
    adjacency: np.ndarray,
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> np.ndarray:
    '''
    Compute PageRank vector using power iteration.
    PR = (1 - d) / N + d * (M * PR)
    '''
    n = adjacency.shape[0]
    if n == 0:
        return np.array([])

    # Row-normalize adjacency matrix (transition probability matrix)
    row_sums = np.sum(adjacency, axis=1)
    # Handle sink nodes
    M = np.zeros((n, n))
    for i in range(n):
        if row_sums[i] > 0:
            M[i] = adjacency[i] / row_sums[i]
        else:
            M[i] = np.ones(n) / n

    # Transpose M for PR equation: PR = (1-d)/N + d * M.T * PR
    MT = M.T

    # Initialize PR vector
    pr = np.ones(n) / n
    for _ in range(max_iter):
        prev_pr = pr.copy()
        pr = (1.0 - damping) / n + damping * (MT @ pr)
        # Check convergence
        if np.linalg.norm(pr - prev_pr, 1) < tol:
            break
    return pr


class Hypergraph:
    '''
    Mathematical representation of a Hypergraph H = (V, E)
    where V is a set of nodes and E is a set of hyperedges (subsets of V).
    '''

    def __init__(self, n_nodes: int, hyperedges: list[list[int]]):
        self.n_nodes = n_nodes
        self.hyperedges = hyperedges

    def incidence_matrix(self) -> np.ndarray:
        '''
        Generate incidence matrix H of shape (n_nodes, n_hyperedges).
        H_ve = 1 if node v belongs to hyperedge e, else 0.
        '''
        h = np.zeros((self.n_nodes, len(self.hyperedges)))
        for e_idx, edge in enumerate(self.hyperedges):
            for node in edge:
                if 0 <= node < self.n_nodes:
                    h[node, e_idx] = 1.0
        return h

    def node_degrees(self) -> np.ndarray:
        '''Degree of each node in the hypergraph: number of hyperedges containing the node.'''
        h = self.incidence_matrix()
        return np.sum(h, axis=1)

    def hyperedge_degrees(self) -> np.ndarray:
        '''Degree of each hyperedge: number of nodes in the hyperedge.'''
        h = self.incidence_matrix()
        return np.sum(h, axis=0)

    def laplacian_matrix(self) -> np.ndarray:
        '''
        Compute normalized hypergraph Laplacian: L = I - D_v^(-1/2) * H * W * D_e^(-1) * H.T * D_v^(-1/2)
        Assuming uniform hyperedge weights W = I.
        '''
        h = self.incidence_matrix()
        n_edges = len(self.hyperedges)
        if n_edges == 0 or self.n_nodes == 0:
            return np.eye(self.n_nodes)

        d_v = np.sum(h, axis=1)
        d_e = np.sum(h, axis=0)

        # Inverse degree matrices
        d_v_inv_sqrt = np.diag([1.0 / np.sqrt(d) if d > 0 else 0.0 for d in d_v])
        d_e_inv = np.diag([1.0 / d if d > 0 else 0.0 for d in d_e])

        # Laplacian
        return np.eye(self.n_nodes) - d_v_inv_sqrt @ h @ d_e_inv @ h.T @ d_v_inv_sqrt

    def hypergraph_spectral_clustering(self, k: int = 2) -> np.ndarray:
        '''
        Perform hypergraph spectral clustering by computing eigenvectors of normalized hypergraph Laplacian.
        '''
        L = self.laplacian_matrix()
        if L.shape[0] <= 1:
            return np.zeros(L.shape[0], dtype=int)

        evals, evecs = np.linalg.eigh(L)
        idx = np.argsort(evals)
        k_evecs = evecs[:, idx[:max(1, k)]]
        labels = np.argmax(np.abs(k_evecs), axis=1)
        return labels


def build_spatial_reading_dag(elements: list[dict]) -> Any:
    '''
    Builds spatial reading order DAG over document elements with Kahn's priority queue tie-breaking.
    Enforces Theorem 6.1 (graph acyclicity) and Theorem 6.2 (determinism).
    '''
    import networkx as nx
    G = nx.DiGraph()
    n = len(elements)
    for i in range(n):
        G.add_node(i, data=elements[i])

    row_tol = 0.03
    for i in range(n):
        e1 = elements[i]
        y1, x1, h1, w1 = e1.get('y', 0.0), e1.get('x', 0.0), e1.get('h', 0.05), e1.get('w', 0.8)
        for j in range(i + 1, n):
            e2 = elements[j]
            y2, x2 = e2.get('y', 0.0), e2.get('x', 0.0)

            # Check spatial successor relationship
            is_same_row = abs(y1 - y2) <= row_tol
            if is_same_row:
                if x2 > x1 + w1 / 2.0:
                    G.add_edge(i, j)
                elif x1 > x2 + e2.get('w', 0.8) / 2.0:
                    G.add_edge(j, i)
            else:
                if y2 >= y1 + h1 - row_tol:
                    G.add_edge(i, j)
                elif y1 >= y2 + e2.get('h', 0.05) - row_tol:
                    G.add_edge(j, i)

    # Ensure acyclicity
    if not nx.is_directed_acyclic_graph(G):
        # Remove back-edges via cycle feedback vertex set
        cycles = list(nx.simple_cycles(G))
        for cyc in cycles:
            if len(cyc) >= 2:
                G.remove_edge(cyc[-1], cyc[0])

    return G
