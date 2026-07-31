"""
AEGIS-AMDI-OS — Matrix Object Schema
======================================
M[i, j] — Tables as mathematical matrices.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, Field, computed_field


class CellType(str, Enum):
    """Type of cell content."""
    TEXT = "text"
    NUMBER = "number"
    PERCENT = "percent"
    CURRENCY = "currency"
    DATE = "date"
    BOOLEAN = "boolean"
    EMPTY = "empty"
    FORMULA = "formula"


class TableCell(BaseModel):
    """A single cell in a table."""
    value: Any = None
    raw_text: str = ""
    cell_type: CellType = CellType.TEXT
    row: int = 0
    col: int = 0
    is_header: bool = False

    @computed_field
    @property
    def is_numeric(self) -> bool:
        return self.cell_type in (CellType.NUMBER, CellType.PERCENT, CellType.CURRENCY)


class TableMetadata(BaseModel):
    """Metadata about a table."""
    title: str | None = None
    caption: str | None = None
    units: str | None = None
    source: str | None = None
    footnotes: list[str] = Field(default_factory=list)


class MatrixObject(BaseModel):
    """
    Tables represented as mathematical matrices M[i, j].

    Supports:
    - Cell-by-cell storage
    - Pre-computed statistics (sum, mean, growth)
    - Column/row operations
    """

    # ===== Identity =====
    table_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str
    element_id: str | None = None  # Reference to GeometryObject
    page: int = 0

    # ===== Structure =====
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    cells: list[TableCell] = Field(default_factory=list)

    # ===== Computed matrix =====
    matrix: list[list[float | None]] | None = None

    # ===== Metadata =====
    metadata: TableMetadata = Field(default_factory=TableMetadata)

    # ===== Computed metrics =====
    column_sums: dict[str, float] = Field(default_factory=dict)
    column_means: dict[str, float] = Field(default_factory=dict)
    column_mins: dict[str, float] = Field(default_factory=dict)
    column_maxs: dict[str, float] = Field(default_factory=dict)
    growth_rates: dict[str, float] = Field(default_factory=dict)
    correlations: dict[str, dict[str, float]] = Field(default_factory=dict)

    # ===== Computed =====
    @computed_field
    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @computed_field
    @property
    def n_cols(self) -> int:
        return len(self.headers) if self.headers else (
            max(len(r) for r in self.rows) if self.rows else 0
        )

    @computed_field
    @property
    def shape(self) -> tuple[int, int]:
        return (self.n_rows, self.n_cols)

    @computed_field
    @property
    def is_numeric(self) -> bool:
        """True if all cells are numeric."""
        return self.matrix is not None and all(
            v is not None for row in (self.matrix or []) for v in row
        )

    # ===== Methods =====
    def to_numpy(self) -> np.ndarray:
        """Convert to NumPy array."""
        if self.matrix is None:
            return np.array([], dtype=np.float32)
        arr = np.array(self.matrix, dtype=np.float32)
        return arr

    def column(self, j: int) -> np.ndarray:
        """Get j-th column as numpy array."""
        arr = self.to_numpy()
        if arr.size == 0 or j >= arr.shape[1] if arr.ndim > 1 else 0:
            return np.array([])
        return arr[:, j] if arr.ndim > 1 else arr

    def row(self, i: int) -> np.ndarray:
        """Get i-th row as numpy array."""
        arr = self.to_numpy()
        if arr.size == 0 or i >= arr.shape[0]:
            return np.array([])
        return arr[i, :] if arr.ndim > 1 else arr

    def cell(self, i: int, j: int) -> Any:
        """Get cell at (i, j)."""
        if i < len(self.rows) and j < len(self.rows[i]):
            return self.rows[i][j]
        return None

    def to_llm_string(self) -> str:
        """Format for LLM context."""
        lines = [
            f"Table (page {self.page}, shape {self.n_rows}x{self.n_cols}):",
            f"  Headers: {self.headers}",
        ]
        arr = self.to_numpy()
        for i in range(self.n_rows):
            if arr.size > 0 and i < arr.shape[0]:
                row_str = "    [" + ", ".join(
                    f"{v:.4g}" if v is not None and not np.isnan(v) else "_"
                    for v in arr[i]
                ) + "]"
            else:
                row_str = "    " + ", ".join(str(v) for v in self.rows[i])
            lines.append(f"  Row {i}: {row_str}")
        # Add pre-computed metrics
        for col, s in self.column_sums.items():
            lines.append(f"  Col '{col}': sum={s:.4g}")
        for col, g in self.growth_rates.items():
            lines.append(f"  Col '{col}': growth={g * 100:.2f}%")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Convert to markdown table."""
        if not self.rows:
            return ""
        h = self.headers
        md = "| " + " | ".join(h) + " |\n"
        md += "|" + "|".join("---" for _ in h) + "|\n"
        for r in self.rows:
            md += "| " + " | ".join(str(c) for c in r) + " |\n"
        return md

    model_config = {"json_schema_extra": {
        "example": {
            "doc_id": "doc-123",
            "page": 12,
            "headers": ["Region", "2024", "2025"],
            "rows": [["India", "300", "500"], ["US", "200", "250"]],
        }
    }}
