"""
AMDI-OS Advanced Analytics: Knowledge Graph
===========================================

Constructs, queries, and analyzes relationship networks (entities, documents, 
topics) and exports visual graph representations (nodes and edges).
"""

from typing import Dict, List, Set, Tuple, Optional, Any


class GraphNode:
    """
    Represents a node in the Knowledge Graph.
    """
    def __init__(self, node_id: str, label: str, node_type: str, properties: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.label = label
        self.node_type = node_type
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.node_id,
            "label": self.label,
            "type": self.node_type,
            "properties": self.properties,
        }


class GraphEdge:
    """
    Represents a directed or undirected edge in the Knowledge Graph.
    """
    def __init__(self, source: str, target: str, rel_type: str, weight: float = 1.0, properties: Optional[Dict[str, Any]] = None):
        self.source = source
        self.target = target
        self.rel_type = rel_type
        self.weight = weight
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.rel_type,
            "weight": self.weight,
            "properties": self.properties,
        }


class KnowledgeGraph:
    """
    In-memory knowledge graph representation and analysis engine.
    """
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        # Maps node_id -> set of target node_ids (outgoing)
        self.adjacency: Dict[str, Dict[str, GraphEdge]] = {}
        # Maps node_id -> set of source node_ids (incoming)
        self.in_adjacency: Dict[str, Dict[str, GraphEdge]] = {}

    def add_node(self, node_id: str, label: str, node_type: str, properties: Optional[Dict[str, Any]] = None) -> GraphNode:
        """
        Adds a new node or updates properties of an existing one.
        """
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(node_id, label, node_type, properties)
            self.adjacency[node_id] = {}
            self.in_adjacency[node_id] = {}
        else:
            self.nodes[node_id].label = label
            self.nodes[node_id].node_type = node_type
            if properties:
                self.nodes[node_id].properties.update(properties)
        return self.nodes[node_id]

    def add_edge(self, source: str, target: str, rel_type: str, weight: float = 1.0, properties: Optional[Dict[str, Any]] = None) -> GraphEdge:
        """
        Adds a directed edge between source and target. Creates nodes if they do not exist.
        """
        if source not in self.nodes:
            self.add_node(source, source, "Unknown")
        if target not in self.nodes:
            self.add_node(target, target, "Unknown")

        edge = GraphEdge(source, target, rel_type, weight, properties)
        self.adjacency[source][target] = edge
        self.in_adjacency[target][source] = edge
        return edge

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[Tuple[str, GraphEdge]]:
        """
        Retrieves neighbors of a node.
        direction: 'out' (outgoing), 'in' (incoming), or 'both'
        """
        neighbors = []
        if node_id not in self.nodes:
            return neighbors

        if direction in ("out", "both"):
            for target_id, edge in self.adjacency[node_id].items():
                neighbors.append((target_id, edge))
        if direction in ("in", "both"):
            for source_id, edge in self.in_adjacency[node_id].items():
                # Avoid duplicates in undirected interpretation
                if direction == "in" or source_id not in self.adjacency[node_id]:
                    neighbors.append((source_id, edge))
        return neighbors

    def get_shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        """
        Computes the shortest path between start and end nodes using BFS.
        Treats edges as undirected.
        """
        if start not in self.nodes or end not in self.nodes:
            return None
        if start == end:
            return [start]

        visited = {start}
        queue = [[start]]

        while queue:
            path = queue.pop(0)
            node = path[-1]

            # Merge outgoing and incoming targets
            neighbors = set(self.adjacency[node].keys()) | set(self.in_adjacency[node].keys())
            for neighbor in neighbors:
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    def get_degree_centrality(self) -> Dict[str, float]:
        """
        Calculates degree centrality for all nodes.
        Centrality is normalized by N - 1, where N is the total number of nodes.
        """
        n = len(self.nodes)
        if n <= 1:
            return {node_id: 0.0 for node_id in self.nodes}

        centrality = {}
        for node_id in self.nodes:
            degree = len(self.adjacency[node_id]) + len(self.in_adjacency[node_id])
            centrality[node_id] = degree / (n - 1)
        return centrality

    def get_subgraph_around_node(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Extracts a subgraph within a certain depth (radius) from a center node.
        Returns visual representation data format {"nodes": [...], "edges": [...]}.
        """
        if node_id not in self.nodes:
            return {"nodes": [], "edges": []}

        subgraph_nodes: Set[str] = {node_id}
        current_layer = {node_id}

        for _ in range(depth):
            next_layer = set()
            for curr in current_layer:
                neighbors = set(self.adjacency[curr].keys()) | set(self.in_adjacency[curr].keys())
                next_layer.update(neighbors)
            next_layer -= subgraph_nodes
            subgraph_nodes.update(next_layer)
            current_layer = next_layer

        # Build list of nodes and edges
        nodes_list = [self.nodes[nid].to_dict() for nid in subgraph_nodes]
        edges_list = []
        visited_edges = set()

        for nid in subgraph_nodes:
            # Add outgoing edges that target nodes in the subgraph
            for target_id, edge in self.adjacency[nid].items():
                if target_id in subgraph_nodes:
                    edge_key = (nid, target_id, edge.rel_type)
                    if edge_key not in visited_edges:
                        edges_list.append(edge.to_dict())
                        visited_edges.add(edge_key)

        return {
            "nodes": nodes_list,
            "edges": edges_list
        }

    def to_visualization_json(self) -> Dict[str, Any]:
        """
        Exports the entire graph to visual JSON.
        """
        nodes_list = [node.to_dict() for node in self.nodes.values()]
        edges_list = []
        for source in self.adjacency:
            for target in self.adjacency[source]:
                edges_list.append(self.adjacency[source][target].to_dict())
        return {
            "nodes": nodes_list,
            "edges": edges_list
        }
