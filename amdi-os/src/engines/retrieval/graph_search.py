"""

Graph Search

============



Graph-based retrieval using:

- Personalized PageRank (PPR)

- BFS / DFS traversal

- Shortest-path queries

- Subgraph extraction

"""



from __future__ import annotations



from collections import deque

from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Set, Tuple



import numpy as np



from .exceptions import EmptyIndexError, InvalidQueryError





@dataclass

class GraphResult:

    """A single graph search result."""



    node_id: Any

    score: float

    rank: int

    path: List[Any] = field(default_factory=list)

    distance: int = 0

    metadata: Dict[str, Any] = field(default_factory=dict)





class GraphSearch:

    """

    Graph-based retrieval.



    Mathematical Foundation:

        Personalized PageRank:

            p = (1 - α) · M^T · p + α · s



        BFS: O(V + E) unweighted shortest path

        Dijkstra: O((V + E) log V) weighted shortest path

    """



    def __init__(

        self,

        damping: float = 0.85,

        max_iter: int = 100,

        tol: float = 1e-6,

    ) -> None:

        self.damping = damping

        self.max_iter = max_iter

        self.tol = tol

        self.adjacency: Dict[Any, List[Tuple[Any, float]]] = {}

        self.metadata: Dict[Any, Dict[str, Any]] = {}



    def add_node(self, node_id: Any, metadata: Optional[Dict[str, Any]] = None) -> None:

        if node_id not in self.adjacency:

            self.adjacency[node_id] = []

        if metadata is not None:

            self.metadata[node_id] = metadata



    def add_edge(

        self,

        source: Any,

        target: Any,

        weight: float = 1.0,

        directed: bool = True,

    ) -> None:

        """Add an edge (undirected by default if directed=False)."""

        self.add_node(source)

        self.add_node(target)

        self.adjacency[source].append((target, weight))

        if not directed:

            self.adjacency[target].append((source, weight))



    def add_edges(

        self,

        edges: List[Tuple[Any, Any, float]],

        directed: bool = True,

    ) -> None:

        for s, t, w in edges:

            self.add_edge(s, t, w, directed=directed)



    def bfs(

        self,

        start: Any,

        max_depth: int = 3,

    ) -> List[GraphResult]:

        """Breadth-first traversal from `start`."""

        if start not in self.adjacency:

            raise InvalidQueryError(f"Start node '{start}' not in graph.")

        visited: Set[Any] = {start}

        queue: deque = deque([(start, 0, [start])])

        results: List[GraphResult] = [

            GraphResult(

                node_id=start,

                score=1.0,

                rank=1,

                path=[start],

                distance=0,

            )

        ]

        rank = 2

        while queue:

            node, depth, path = queue.popleft()

            if depth >= max_depth:

                continue

            for neighbor, _ in self.adjacency.get(node, []):

                if neighbor not in visited:

                    visited.add(neighbor)

                    new_path = path + [neighbor]

                    score = 1.0 / (1.0 + depth + 1)

                    results.append(

                        GraphResult(

                            node_id=neighbor,

                            score=float(score),

                            rank=rank,

                            path=new_path,

                            distance=depth + 1,

                            metadata=self.metadata.get(neighbor, {}),

                        )

                    )

                    rank += 1

                    queue.append((neighbor, depth + 1, new_path))

        return results



    def shortest_path(

        self,

        source: Any,

        target: Any,

    ) -> Optional[List[Any]]:

        """BFS shortest path (unweighted)."""

        if source not in self.adjacency or target not in self.adjacency:

            return None

        if source == target:

            return [source]

        visited: Set[Any] = {source}

        queue: deque = deque([(source, [source])])

        while queue:

            node, path = queue.popleft()

            for neighbor, _ in self.adjacency.get(node, []):

                if neighbor == target:

                    return path + [neighbor]

                if neighbor not in visited:

                    visited.add(neighbor)

                    queue.append((neighbor, path + [neighbor]))

        return None



    def personalized_pagerank(

        self,

        seed_nodes: List[Any],

        top_k: int = 10,

    ) -> List[GraphResult]:

        """

        Personalized PageRank from seed nodes.



        p = (1 - α) M^T p + α s

        """

        if not self.adjacency:

            raise EmptyIndexError("Graph is empty.")

        for s in seed_nodes:

            if s not in self.adjacency:

                raise InvalidQueryError(f"Seed node '{s}' not in graph.")

        nodes = list(self.adjacency.keys())

        n = len(nodes)

        idx = {node: i for i, node in enumerate(nodes)}

        # transition matrix M: M[i,j] = prob(j → i) — column-stochastic

        M = np.zeros((n, n), dtype=np.float64)

        for src, neighbors in self.adjacency.items():

            if not neighbors:

                continue

            total_w = sum(w for _, w in neighbors)

            if total_w <= 0:

                continue

            for tgt, w in neighbors:

                M[idx[tgt], idx[src]] = w / total_w

        # seed vector

        s = np.zeros(n, dtype=np.float64)

        for seed in seed_nodes:

            s[idx[seed]] = 1.0 / len(seed_nodes)

        # power iteration

        p = s.copy()

        for it in range(self.max_iter):

            p_new = (1 - self.damping) * (M @ p) + self.damping * s

            if np.linalg.norm(p_new - p, 1) < self.tol:

                p = p_new

                break

            p = p_new

        # build results

        scored = [(nodes[i], float(p[i])) for i in range(n)]

        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:top_k]

        results: List[GraphResult] = []

        for rank, (node, score) in enumerate(top, start=1):

            results.append(

                GraphResult(

                    node_id=node,

                    score=score,

                    rank=rank,

                    path=[node],

                    distance=0,

                    metadata=self.metadata.get(node, {}),

                )

            )

        return results



    def neighbors(

        self,

        node: Any,

        max_hops: int = 1,

    ) -> List[GraphResult]:

        """Get neighbors within max_hops."""

        return self.bfs(node, max_depth=max_hops)
