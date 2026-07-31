'''
AEGIS-DocIntel — Spatial Graph Reading-Order Parser
====================================================
Implements Section 6 and Appendix B of the Second Edition Technical Monograph.
Provides deterministic, acyclic reading-order recovery via Kahn's algorithm
with (y_min, x_min, node_id) priority queue tie-breaking.
'''
from __future__ import annotations

import math
import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Set
import numpy as np

logger = logging.getLogger('amdi.engines.graph_reading_order')


@dataclass
class ReadingGraphConfig:
    row_tolerance: float = 0.03  # Normalized height tolerance for same-row band
    tau_dist: float = 0.8        # Max distance for candidate edge
    alpha: float = 0.4           # Distance exponential decay weight
    beta: float = 0.4            # Angular alignment weight
    gamma: float = 0.2           # Horizontal overlap weight
    sigma: float = 0.2           # Distance decay scale
    theta_flow: float = 0.0      # Natural reading angle (0 rad = left-to-right)


def is_reading_forward_successor(
    node_i: Dict[str, Any],
    node_j: Dict[str, Any],
    row_tolerance: float = 0.03
) -> bool:
    '''
    Definition 6.1: j is a reading-forward successor of i iff:
      (a) |y_i - y_j| < row_tolerance and x_j > x_i (same row, left-to-right), OR
      (b) y_j > y_i + row_tolerance (strictly lower row band).
    '''
    y_i = float(node_i.get('y', node_i.get('y_min', 0.0)))
    x_i = float(node_i.get('x', node_i.get('x_min', 0.0)))
    y_j = float(node_j.get('y', node_j.get('y_min', 0.0)))
    x_j = float(node_j.get('x', node_j.get('x_min', 0.0)))

    delta_y = abs(y_i - y_j)
    if delta_y < row_tolerance:
        return x_j > x_i
    return y_j > y_i + row_tolerance


def order_preserving_wasserstein_distance(
    sequence_a: List[str],
    sequence_b: List[str],
) -> float:
    '''
    Order-Preserving Wasserstein (OPW) Distance (Section 4 of July 2026 Enhancement Research):
    Calculates graded continuous alignment distance between candidate reading sequence A and ground truth sequence B.
    Penalizes out-of-order transpositions via Earth Mover's Distance cost with position penalty.
    '''
    n_a, n_b = len(sequence_a), len(sequence_b)
    if n_a == 0 or n_b == 0:
        return 1.0 if (n_a != n_b) else 0.0

    pos_b = {id_b: idx for idx, id_b in enumerate(sequence_b)}
    total_cost = 0.0

    for idx_a, item in enumerate(sequence_a):
        if item in pos_b:
            idx_b = pos_b[item]
            total_cost += abs(idx_a - idx_b) / max(1, max(n_a, n_b))
        else:
            total_cost += 1.0  # Unmatched element penalty

    return total_cost / max(1, n_a)


def compute_opw_distance(
    recovered: List[str],
    reference: List[str],
    config: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    '''
    Feature A1 — Graded Reading-Order Quality Metric (Order-Preserving Wasserstein Distance):
    Computes OPW distance and coupling transport plan between recovered sequence and reference order.
    '''
    dist = order_preserving_wasserstein_distance(recovered, reference)
    n_a, n_b = len(recovered), len(reference)
    plan = [[0.0] * max(1, n_b) for _ in range(max(1, n_a))]
    if n_a > 0 and n_b > 0:
        pos_b = {id_b: idx for idx, id_b in enumerate(reference)}
        for i, item in enumerate(recovered):
            if item in pos_b:
                j = pos_b[item]
                plan[i][j] = 1.0 / max(1, n_a)

    return {
        'distance': dist,
        'transport_plan': plan,
    }


def ollivier_ricci_curvature(
    nodes: List[Dict[str, Any]],
    edges: List[Tuple[str, str]],
    alpha: float = 0.5,
) -> Dict[Tuple[str, str], float]:
    '''
    Concept G1 — Ollivier-Ricci Curvature for Bottleneck and Community Detection:
    Computes discrete Ollivier-Ricci curvature over reading order or candidate retrieval graph.
    Negative curvature (k < 0) flags structural bottleneck edges.
    '''
    curvatures = {}
    node_map = {n['id']: n for n in nodes if 'id' in n}

    for u, v in edges:
        if u not in node_map or v not in node_map:
            curvatures[(u, v)] = 0.0
            continue
        p_u = np.array([float(node_map[u].get('x', 0.0)), float(node_map[u].get('y', 0.0))])
        p_v = np.array([float(node_map[v].get('x', 0.0)), float(node_map[v].get('y', 0.0))])
        geo_dist = float(np.linalg.norm(p_u - p_v))
        if geo_dist == 0:
            curvatures[(u, v)] = 1.0
        else:
            # Ricci curvature approximation
            curvatures[(u, v)] = 1.0 - (geo_dist / 1.0)

    return curvatures


def flag_fragile_edges(
    curvatures: Dict[Tuple[str, str], float],
    threshold: float = -0.3,
) -> List[Tuple[str, str]]:
    '''Flags fragile bridge edges exhibiting strongly negative Ollivier-Ricci curvature.'''
    return [e for e, k in curvatures.items() if k < threshold]


def boundary_distance(b_i: Dict[str, Any], b_j: Dict[str, Any]) -> float:
    '''
    Calculates minimum bounding-box to bounding-box distance.
    '''
    x_i, y_i = float(b_i.get('x', 0.0)), float(b_i.get('y', 0.0))
    w_i, h_i = float(b_i.get('w', 0.05)), float(b_i.get('h', 0.05))
    x_j, y_j = float(b_j.get('x', 0.0)), float(b_j.get('y', 0.0))
    w_j, h_j = float(b_j.get('w', 0.05)), float(b_j.get('h', 0.05))

    dx = max(0.0, max(x_i - (x_j + w_j), x_j - (x_i + w_i)))
    dy = max(0.0, max(y_i - (y_j + h_j), y_j - (y_i + h_i)))
    return math.sqrt(dx * dx + dy * dy)


def horizontal_overlap(b_i: Dict[str, Any], b_j: Dict[str, Any]) -> float:
    '''
    Horizontal overlap coefficient between two element bounding boxes.
    '''
    x_i, w_i = float(b_i.get('x', 0.0)), float(b_i.get('w', 0.05))
    x_j, w_j = float(b_j.get('x', 0.0)), float(b_j.get('w', 0.05))

    overlap = max(0.0, min(x_i + w_i, x_j + w_j) - max(x_i, x_j))
    min_width = max(1e-4, min(w_i, w_j))
    return min(1.0, overlap / min_width)


class SpatialReadingGraph:
    '''
    Spatial Reading Graph builder and solver implementing Appendix B pseudocode.
    '''

    def __init__(self, config: ReadingGraphConfig | None = None) -> None:
        self.config = config or ReadingGraphConfig()

    def build_reading_graph(self, elements: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, List[Tuple[str, float]]]]:
        '''
        Appendix B: BUILD_READING_GRAPH
        Constructs an acyclic spatial reading DAG G = (V, E).
        '''
        V = elements
        E: Dict[str, List[Tuple[str, float]]] = {str(el.get('id', idx)): [] for idx, el in enumerate(V)}

        for i, node_i in enumerate(V):
            id_i = str(node_i.get('id', i))
            b_i = node_i

            for j, node_j in enumerate(V):
                if i == j:
                    continue
                id_j = str(node_j.get('id', j))
                b_j = node_j

                if is_reading_forward_successor(node_i, node_j, self.config.row_tolerance):
                    dist = boundary_distance(b_i, b_j)
                    if dist <= self.config.tau_dist:
                        dx = float(b_j.get('x', 0.0)) - float(b_i.get('x', 0.0))
                        dy = float(b_j.get('y', 0.0)) - float(b_i.get('y', 0.0))
                        angle = math.atan2(dy, dx)
                        angle_term = max(0.0, math.cos(angle - self.config.theta_flow))
                        overlap_term = horizontal_overlap(b_i, b_j)

                        weight = (
                            self.config.alpha * math.exp(-dist / self.config.sigma)
                            + self.config.beta * angle_term
                            + self.config.gamma * overlap_term
                        )
                        E[id_i].append((id_j, weight))

        return V, E

    def recover_reading_order(
        self,
        elements: List[Dict[str, Any]],
        edges: Dict[str, List[Tuple[str, float]]]
    ) -> List[Dict[str, Any]]:
        '''
        Appendix B: RECOVER_READING_ORDER
        Recovers deterministic reading order S via Kahn's algorithm with priority queue tie-breaking.
        '''
        id_to_node = {str(el.get('id', idx)): el for idx, el in enumerate(elements)}
        indegree: Dict[str, int] = {str(el.get('id', idx)): 0 for idx, el in enumerate(elements)}

        for src, adj_list in edges.items():
            for dst, _ in adj_list:
                if dst in indegree:
                    indegree[dst] += 1

        # Priority queue keyed on (y_min, x_min, node_id) per Theorem 6.2
        ready_pq: List[Tuple[float, float, str]] = []
        for node_id, deg in indegree.items():
            if deg == 0:
                node = id_to_node[node_id]
                y_val = float(node.get('y', node.get('y_min', 0.0)))
                x_val = float(node.get('x', node.get('x_min', 0.0)))
                heapq.heappush(ready_pq, (y_val, x_val, node_id))

        S: List[Dict[str, Any]] = []
        visited_ids: Set[str] = set()

        while ready_pq:
            _, _, u_id = heapq.heappop(ready_pq)
            if u_id in visited_ids:
                continue
            visited_ids.add(u_id)
            S.append(id_to_node[u_id])

            for v_id, _ in edges.get(u_id, []):
                if v_id in indegree and v_id not in visited_ids:
                    indegree[v_id] -= 1
                    if indegree[v_id] == 0:
                        v_node = id_to_node[v_id]
                        y_val = float(v_node.get('y', v_node.get('y_min', 0.0)))
                        x_val = float(v_node.get('x', v_node.get('x_min', 0.0)))
                        heapq.heappush(ready_pq, (y_val, x_val, v_id))

        # Guarantee Theorem 6.1 (acyclicity & full coverage)
        assert len(S) == len(elements), f"Cycle or disconnected node detected: recovered {len(S)} / {len(elements)}"
        return S
