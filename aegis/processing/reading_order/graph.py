"""
aegis.processing.reading_order.graph
====================================
Directed graph representing document reading order, columnar structures, and entity associations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from aegis.processing.models import OrderRelationship


class ReadingOrderGraph:
    """Directed acyclic graph modeling document visual and semantic reading order."""

    def __init__(self) -> None:
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {}  # node -> set of successor nodes
        self.relationships: List[OrderRelationship] = []

    def add_node(self, node_id: str) -> None:
        """Add a region node."""
        self.nodes.add(node_id)
        if node_id not in self.edges:
            self.edges[node_id] = set()

    def add_precedence(self, before_id: str, after_id: str) -> None:
        """Add directed precedence edge (before_id must precede after_id)."""
        self.add_node(before_id)
        self.add_node(after_id)
        self.edges[before_id].add(after_id)

    def add_relationship(self, source_id: str, target_id: str, relation_type: str) -> None:
        """Add semantic association between regions."""
        self.add_node(source_id)
        self.add_node(target_id)
        self.relationships.append(
            OrderRelationship(source_id=source_id, target_id=target_id, relation_type=relation_type)
        )

    def has_cycle(self) -> bool:
        """Check for cycles using depth-first search."""
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node: str) -> bool:
            visited[node] = 1
            for neighbor in self.edges.get(node, set()):
                state = visited.get(neighbor, 0)
                if state == 1:
                    return True  # back edge found (cycle)
                if state == 0 and dfs(neighbor):
                    return True
            visited[node] = 2
            return False

        for n in self.nodes:
            if visited.get(n, 0) == 0:
                if dfs(n):
                    return True
        return False

    def topological_sort(self) -> List[str]:
        """Compute valid linear sequence respecting directed precedence edges."""
        if self.has_cycle():
            # If cycle detected, break cycles by falling back to node names
            return sorted(list(self.nodes))

        in_degree = {n: 0 for n in self.nodes}
        for n, successors in self.edges.items():
            for succ in successors:
                in_degree[succ] = in_degree.get(succ, 0) + 1

        # Queue of nodes with no incoming dependencies
        queue = sorted([n for n in self.nodes if in_degree[n] == 0])
        order = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for succ in sorted(list(self.edges.get(curr, set()))):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)
            queue.sort()

        if len(order) != len(self.nodes):
            # Unreached nodes due to disconnected cycles
            remaining = sorted(list(self.nodes - set(order)))
            order.extend(remaining)

        return order
