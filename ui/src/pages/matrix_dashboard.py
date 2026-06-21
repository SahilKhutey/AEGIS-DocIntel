"""
Matrix Dashboard
=================

Visualizes tables, statistics, and matrix engine outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class TableSummary:
    """A summary of an extracted table."""

    table_id: str
    document_id: str
    page: int
    headers: List[str]
    row_count: int
    col_count: int
    data_preview: List[List[Any]] = field(default_factory=list)
    statistics: Dict[str, float] = field(default_factory=dict)
    completeness: float = 1.0
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "table_id": self.table_id,
            "document_id": self.document_id,
            "page": self.page,
            "headers": self.headers,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "data_preview": self.data_preview,
            "statistics": {k: round(v, 4) for k, v in self.statistics.items()},
            "completeness": round(self.completeness, 4),
            "confidence": round(self.confidence, 4),
        }


@dataclass
class MatrixViewData:
    """Data for matrix dashboard."""

    document_id: str
    tables: List[TableSummary] = field(default_factory=list)
    total_rows: int = 0
    total_cols: int = 0
    average_completeness: float = 1.0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "tables": [t.to_dict() for t in self.tables],
            "total_rows": self.total_rows,
            "total_cols": self.total_cols,
            "average_completeness": round(self.average_completeness, 4),
            "num_tables": len(self.tables),
        }


class MatrixDashboard:
    """Matrix dashboard backend API."""

    def __init__(self) -> None:
        self.documents: Dict[str, MatrixViewData] = {}

    def add_table(
        self,
        document_id: str,
        table: TableSummary,
    ) -> None:
        if document_id not in self.documents:
            self.documents[document_id] = MatrixViewData(document_id=document_id)
        view = self.documents[document_id]
        view.tables.append(table)
        view.total_rows += table.row_count
        view.total_cols = max(view.total_cols, table.col_count)

    def get_view(self, document_id: str) -> MatrixViewData:
        if document_id not in self.documents:
            return MatrixViewData(document_id=document_id)
        view = self.documents[document_id]
        if view.tables:
            view.average_completeness = float(
                np.mean([t.completeness for t in view.tables])
            )
        return view

    def compute_statistics(
        self,
        table_id: str,
        matrix: np.ndarray,
    ) -> Dict[str, float]:
        """Compute statistics for a numeric matrix."""
        if matrix.size == 0:
            return {}
        return {
            "mean": float(matrix.mean()),
            "median": float(np.median(matrix)),
            "std": float(matrix.std()),
            "min": float(matrix.min()),
            "max": float(matrix.max()),
            "sum": float(matrix.sum()),
        }
