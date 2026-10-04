'''
AEGIS-MIOS — Computational Geometry
====================================
Geometric algorithms:
- Convex Hull (Graham Scan)
- Voronoi Cell Areas (via Delaunay Triangulation)
- K-Dimensional Tree (KD-Tree) with Nearest Neighbor Search
'''

from __future__ import annotations

import numpy as np
from scipy.spatial import Delaunay


def convex_hull(points: np.ndarray) -> np.ndarray:
    '''
    Compute the Convex Hull of a set of 2D points using the Graham Scan algorithm.
    Returns the points on the hull in counter-clockwise order.
    '''
    n = len(points)
    if n < 3:
        return points

    # Find the bottom-most point (and left-most if tied)
    pivot_idx = np.lexsort((points[:, 0], points[:, 1]))[0]
    pivot = points[pivot_idx]

    # Helper function to compute polar angle
    def polar_angle_and_dist(p):
        diff = p - pivot
        angle = np.arctan2(diff[1], diff[0])
        dist = np.dot(diff, diff)
        return angle, dist

    # Sort other points by polar angle, then by distance
    other_indices = [i for i in range(n) if i != pivot_idx]
    sorted_indices = sorted(
        other_indices,
        key=lambda idx: polar_angle_and_dist(points[idx]),
    )

    # Orientation check: cross product of vectors AB and BC
    # > 0 for CCW, 0 for collinear, < 0 for CW
    def ccw(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    hull = [pivot, points[sorted_indices[0]]]

    for idx in sorted_indices[1:]:
        p = points[idx]
        while len(hull) > 1 and ccw(hull[-2], hull[-1], p) <= 0:
            hull.pop()
        hull.append(p)

    return np.array(hull)


def voronoi_areas(points: np.ndarray) -> np.ndarray:
    '''
    Estimate Voronoi cell area for each point.
    To avoid infinite boundary cells, we approximate cell area as 1/3
    of the area of all Delaunay triangles incident to each point.
    '''
    n = len(points)
    areas = np.zeros(n)
    if n < 3:
        return areas

    tri = Delaunay(points)

    # Compute area of each simplex (triangle)
    for simplex in tri.simplices:
        p0, p1, p2 = points[simplex[0]], points[simplex[1]], points[simplex[2]]
        # Triangle area using cross product formula
        area = 0.5 * abs(p0[0] * (p1[1] - p2[1]) + p1[0] * (p2[1] - p0[1]) + p2[0] * (p0[1] - p1[1]))

        # Distribute 1/3 area to each vertex
        areas[simplex[0]] += area / 3.0
        areas[simplex[1]] += area / 3.0
        areas[simplex[2]] += area / 3.0

    return areas


class KDTreeNode:
    '''Node in a K-Dimensional Tree.'''

    def __init__(self, point: np.ndarray, axis: int, left: KDTreeNode | None = None, right: KDTreeNode | None = None):
        self.point = point
        self.axis = axis
        self.left = left
        self.right = right


class KDTree:
    '''K-Dimensional Tree for fast spatial queries.'''

    def __init__(self, points: np.ndarray):
        self.k = points.shape[1] if len(points) > 0 else 2
        self.root = self._build_tree(points, depth=0)

    def _build_tree(self, points: np.ndarray, depth: int) -> KDTreeNode | None:
        n = len(points)
        if n == 0:
            return None

        axis = depth % self.k
        # Sort points by the axis dimension and find median
        sorted_indices = np.argsort(points[:, axis])
        median_idx = sorted_indices[n // 2]

        return KDTreeNode(
            point=points[median_idx],
            axis=axis,
            left=self._build_tree(points[sorted_indices[:n // 2]], depth + 1),
            right=self._build_tree(points[sorted_indices[n // 2 + 1:]], depth + 1),
        )

    def nearest_neighbor(self, query: np.ndarray) -> tuple[np.ndarray | None, float]:
        '''Find the nearest point to the query vector. Returns (nearest_point, distance).'''
        best_point = None
        best_dist = float('inf')

        def search(node: KDTreeNode | None):
            nonlocal best_point, best_dist
            if node is None:
                return

            # Compute distance to current node's point
            dist = np.linalg.norm(query - node.point)
            if dist < best_dist:
                best_dist = dist
                best_point = node.point

            axis = node.axis
            # Decide which subtree to search first
            if query[axis] < node.point[axis]:
                near_branch = node.left
                far_branch = node.right
            else:
                near_branch = node.right
                far_branch = node.left

            search(near_branch)

            # Check if we need to search the far branch
            if abs(query[axis] - node.point[axis]) < best_dist:
                search(far_branch)

        search(self.root)
        return best_point, best_dist
