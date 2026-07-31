"""
Hypergraph Table Representation Engine (Task C-3).

Constructs hypergraph representations for complex tabular structures with multi-level
headers, merged cells, and hierarchical cell bindings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Set, Any, Tuple, Optional
import numpy as np


@dataclass
class HyperCell:
    cell_id: str
    row_idx: int
    col_idx: int
    row_span: int = 1
    col_span: int = 1
    content: str = ""
    is_header: bool = False


@dataclass
class HyperEdge:
    edge_id: str
    edge_type: str  # "row", "column", "header_span", "hierarchical_binding"
    cell_ids: Set[str] = field(default_factory=set)


class TableHypergraph:
    """
    Represents table structure as a hypergraph H = (V, E) where:
    - V is the set of HyperCells.
    - E is the set of HyperEdges (rows, cols, spanned headers, cell bindings).
    """

    def __init__(self, table_id: str = ""):
        self.table_id = table_id
        self.cells: Dict[str, HyperCell] = {}
        self.hyperedges: Dict[str, HyperEdge] = {}

    def add_cell(self, cell: HyperCell) -> None:
        self.cells[cell.cell_id] = cell

    def add_hyperedge(self, edge: HyperEdge) -> None:
        self.hyperedges[edge.edge_id] = edge

    def get_incidence_matrix(self) -> np.ndarray:
        """
        Builds binary incidence matrix H of shape (|V|, |E|)
        H(v, e) = 1 if vertex v belongs to hyperedge e else 0.
        """
        vertices = list(self.cells.keys())
        edges = list(self.hyperedges.keys())
        
        if not vertices or not edges:
            return np.zeros((len(vertices), len(edges)), dtype=np.int8)

        v_map = {v_id: i for i, v_id in enumerate(vertices)}
        e_map = {e_id: j for j, e_id in enumerate(edges)}

        H = np.zeros((len(vertices), len(edges)), dtype=np.int8)
        for e_id, edge in self.hyperedges.items():
            col = e_map[e_id]
            for v_id in edge.cell_ids:
                if v_id in v_map:
                    row = v_map[v_id]
                    H[row, col] = 1
        return H

    def get_dual_hypergraph(self) -> TableHypergraph:
        """
        Computes dual hypergraph H* where hyperedges become vertices and vertices become hyperedges.
        """
        dual = TableHypergraph(table_id=f"{self.table_id}_dual")
        # Dual vertices derived from original edges
        for e_id, edge in self.hyperedges.items():
            dual_cell = HyperCell(
                cell_id=f"v_{e_id}",
                row_idx=0,
                col_idx=0,
                content=edge.edge_type,
            )
            dual.add_cell(dual_cell)

        # Dual edges derived from original vertices
        for v_id, cell in self.cells.items():
            containing_edges = {
                f"v_{e_id}" for e_id, edge in self.hyperedges.items() if v_id in edge.cell_ids
            }
            dual_edge = HyperEdge(
                edge_id=f"e_{v_id}",
                edge_type="dual_vertex_edge",
                cell_ids=containing_edges,
            )
            dual.add_hyperedge(dual_edge)

        return dual


class TableHypergraphEngine:
    """
    Engine to convert raw grid matrices or cell lists into TableHypergraph models.
    """

    def build_hypergraph(
        self,
        grid: List[List[str]],
        table_id: str = "table_1",
        header_rows: int = 1,
    ) -> TableHypergraph:
        hg = TableHypergraph(table_id=table_id)
        if not grid:
            return hg

        n_rows = len(grid)
        n_cols = max(len(row) for row in grid) if n_rows > 0 else 0

        # Create vertices (cells)
        for r in range(n_rows):
            for c in range(len(grid[r])):
                cell_id = f"c_{r}_{c}"
                is_hdr = r < header_rows
                cell = HyperCell(
                    cell_id=cell_id,
                    row_idx=r,
                    col_idx=c,
                    content=grid[r][c],
                    is_header=is_hdr,
                )
                hg.add_cell(cell)

        # Create row hyperedges
        for r in range(n_rows):
            r_edge_id = f"edge_row_{r}"
            row_cells = {f"c_{r}_{c}" for c in range(len(grid[r]))}
            hg.add_hyperedge(HyperEdge(edge_id=r_edge_id, edge_type="row", cell_ids=row_cells))

        # Create column hyperedges
        for c in range(n_cols):
            c_edge_id = f"edge_col_{c}"
            col_cells = {f"c_{r}_{c}" for r in range(n_rows) if c < len(grid[r])}
            hg.add_hyperedge(HyperEdge(edge_id=c_edge_id, edge_type="column", cell_ids=col_cells))

        # Create header binding hyperedges
        for r in range(header_rows):
            for c in range(n_cols):
                if c < len(grid[r]):
                    binding_edge_id = f"edge_hdr_bind_{r}_{c}"
                    # Connect header cell to all data cells in column c
                    bound_cells = {f"c_{hdr_r}_{c}" for hdr_r in range(header_rows) if c < len(grid[hdr_r])}
                    data_cells = {f"c_{data_r}_{c}" for data_r in range(header_rows, n_rows) if c < len(grid[data_r])}
                    all_bound = bound_cells | data_cells
                    hg.add_hyperedge(HyperEdge(edge_id=binding_edge_id, edge_type="hierarchical_binding", cell_ids=all_bound))

        return hg
