"""
aegis.processing.tables.structure
=================================
Canonical table structure models, grid validators, and tree serialization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aegis.processing.models import TableCellModel, TableReconstruction


class TableGridValidator:
    """Validates structural invariants of reconstructed table grids."""

    @staticmethod
    def validate(table: TableReconstruction) -> Tuple[bool, List[str]]:
        """Verify grid consistency: non-negative indices, span bounds, no duplicate cell coordinates."""
        errors: List[str] = []
        occupied_slots: Dict[Tuple[int, int], str] = {}

        if table.row_count < 0 or table.column_count < 0:
            errors.append(f"Invalid table dimensions: {table.row_count}x{table.column_count}")

        for cell in table.cells:
            r = cell.row_index
            c = cell.column_index
            r_span = cell.row_span
            c_span = cell.column_span

            if r + r_span > table.row_count:
                errors.append(f"Cell {cell.cell_id} row span [{r}:{r+r_span}] exceeds row count {table.row_count}")
            if c + c_span > table.column_count:
                errors.append(f"Cell {cell.cell_id} col span [{c}:{c+c_span}] exceeds column count {table.column_count}")

            # Check overlap across grid coordinates
            for ri in range(r, r + r_span):
                for ci in range(c, c + c_span):
                    slot = (ri, ci)
                    if slot in occupied_slots:
                        errors.append(f"Cell collision at ({ri}, {ci}) between {occupied_slots[slot]} and {cell.cell_id}")
                    else:
                        occupied_slots[slot] = cell.cell_id

        return len(errors) == 0, errors

    @staticmethod
    def to_html(table: TableReconstruction) -> str:
        """Convert table reconstruction to HTML table representation for TEDS tree comparison."""
        grid: Dict[Tuple[int, int], Optional[TableCellModel]] = {}
        for r in range(table.row_count):
            for c in range(table.column_count):
                grid[(r, c)] = None

        cell_by_origin = {(cell.row_index, cell.column_index): cell for cell in table.cells}

        html = ["<table>"]
        for r in range(table.row_count):
            html.append("  <tr>")
            for c in range(table.column_count):
                if (r, c) in cell_by_origin:
                    cell = cell_by_origin[(r, c)]
                    tag = "th" if r in table.header_rows or cell.role in ["column_header", "row_header"] else "td"
                    attrs = []
                    if cell.row_span > 1:
                        attrs.append(f'rowspan="{cell.row_span}"')
                    if cell.column_span > 1:
                        attrs.append(f'colspan="{cell.column_span}"')
                    attr_str = " " + " ".join(attrs) if attrs else ""
                    html.append(f"    <{tag}{attr_str}>{cell.text}</{tag}>")
            html.append("  </tr>")
        html.append("</table>")
        return "\n".join(html)
