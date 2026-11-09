import type { GraphEdge } from "../types";

/**
 * Cycle Detection in a Directed Acyclic Graph (DAG) using Depth First Search (DFS).
 * Returns true if a cycle is detected, false otherwise.
 */
export function hasDependencyCycle(
  nodeIds: string[],
  edges: GraphEdge[],
): boolean {
  // Build adjacency list
  const adj = new Map<string, string[]>();
  for (const id of nodeIds) {
    adj.set(id, []);
  }
  for (const edge of edges) {
    if (!adj.has(edge.from)) adj.set(edge.from, []);
    adj.get(edge.from)?.push(edge.to);
  }

  // 0: Unvisited, 1: Visiting (in recursion stack), 2: Visited
  const state = new Map<string, number>();
  for (const id of nodeIds) {
    state.set(id, 0);
  }

  function dfs(current: string): boolean {
    state.set(current, 1);

    const neighbors = adj.get(current) || [];
    for (const neighbor of neighbors) {
      const neighborState = state.get(neighbor) ?? 0;
      if (neighborState === 1) {
        // Cycle detected
        return true;
      }
      if (neighborState === 0) {
        if (dfs(neighbor)) return true;
      }
    }

    state.set(current, 2);
    return false;
  }

  for (const id of nodeIds) {
    if ((state.get(id) ?? 0) === 0) {
      if (dfs(id)) return true;
    }
  }

  return false;
}

/**
 * Performs a topological sort of the graph nodes.
 * Returns null if a cycle exists.
 */
export function topologicalSort(
  nodeIds: string[],
  edges: GraphEdge[],
): string[] | null {
  if (hasDependencyCycle(nodeIds, edges)) {
    return null;
  }

  const adj = new Map<string, string[]>();
  const inDegree = new Map<string, number>();

  for (const id of nodeIds) {
    adj.set(id, []);
    inDegree.set(id, 0);
  }

  for (const edge of edges) {
    adj.get(edge.from)?.push(edge.to);
    inDegree.set(edge.to, (inDegree.get(edge.to) || 0) + 1);
  }

  const queue: string[] = [];
  for (const [id, deg] of inDegree.entries()) {
    if (deg === 0) {
      queue.push(id);
    }
  }

  const result: string[] = [];
  while (queue.length > 0) {
    const node = queue.shift()!;
    result.push(node);

    for (const neighbor of adj.get(node) || []) {
      const newDeg = (inDegree.get(neighbor) || 1) - 1;
      inDegree.set(neighbor, newDeg);
      if (newDeg === 0) {
        queue.push(neighbor);
      }
    }
  }

  return result.length === nodeIds.length ? result : null;
}
