"""
Enhanced Table Extractor
=========================

Improved table extraction with structure understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class CellType(Enum):
    """Type of table cell."""

    HEADER = "header"
    DATA = "data"
    EMPTY = "empty"
    MERGED = "merged"


@dataclass
class TableCell:
    """A single cell in a table."""

    row: int
    col: int
    value: str
    cell_type: CellType = CellType.DATA
    confidence: float = 1.0


@dataclass
class TableStructure:
    """Structured table representation."""

    headers: List[str]
    rows: List[List[str]]
    cells: List[TableCell] = field(default_factory=list)
    row_count: int = 0
    col_count: int = 0
    completeness: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "headers": self.headers,
            "rows": self.rows,
            "row_count": self.row_count,
            "col_count": self.col_count,
            "completeness": self.completeness,
            "metadata": self.metadata,
        }

    def get_column(self, col_idx: int) -> List[str]:
        return [row[col_idx] if col_idx < len(row) else "" for row in self.rows]

    def get_numeric_column(self, col_idx: int) -> List[Optional[float]]:
        result: List[Optional[float]] = []
        for row in self.rows:
            if col_idx < len(row):
                try:
                    result.append(float(row[col_idx].replace(",", "").replace("$", "").replace("%", "")))
                except (ValueError, AttributeError):
                    result.append(None)
            else:
                result.append(None)
        return result


class EnhancedTableExtractor:
    """
    Enhanced table extraction with structure detection.
    """

    def __init__(self, detect_headers: bool = True) -> None:
        self.detect_headers = detect_headers

    def extract(self, raw_data: List[List[str]]) -> TableStructure:
        """Extract structured table from raw 2D data."""
        if not raw_data or not raw_data[0]:
            return TableStructure(
                headers=[], rows=[], row_count=0, col_count=0, completeness=0.0
            )
        # clean data
        cleaned = [[str(cell).strip() if cell else "" for cell in row] for row in raw_data]
        # detect headers
        if self.detect_headers:
            headers, data_rows = self._detect_headers(cleaned)
        else:
            headers = cleaned[0] if cleaned else []
            data_rows = cleaned[1:] if len(cleaned) > 1 else []
        # build cells
        cells: List[TableCell] = []
        for r, row in enumerate(data_rows):
            for c, value in enumerate(row):
                if c < len(headers):
                    cell_type = CellType.DATA
                    cells.append(TableCell(
                        row=r, col=c, value=value,
                        cell_type=cell_type, confidence=1.0
                    ))
        # compute completeness
        total_cells = len(data_rows) * len(headers) if headers else 0
        non_empty = sum(1 for c in cells if c.value)
        completeness = non_empty / max(total_cells, 1)
        # align columns
        n_cols = max(len(headers), max((len(r) for r in data_rows), default=0))
        for r, row in enumerate(data_rows):
            while len(row) < n_cols:
                row.append("")
        return TableStructure(
            headers=headers,
            rows=data_rows,
            cells=cells,
            row_count=len(data_rows),
            col_count=n_cols,
            completeness=completeness,
            metadata={
                "has_headers": self.detect_headers and bool(headers),
                "extraction_method": "enhanced",
            },
        )

    def _detect_headers(
        self, data: List[List[str]]
    ) -> Tuple[List[str], List[List[str]]]:
        """Detect header row vs data rows."""
        if len(data) <= 1:
            return data[0] if data else [], []
        # heuristic: first row is headers if:
        # 1. cells are short (< 30 chars avg)
        # 2. next row has more numeric content
        first_row = data[0]
        second_row = data[1] if len(data) > 1 else []
        first_avg_len = np.mean([len(str(c)) for c in first_row]) if first_row else 0
        second_numeric_ratio = (
            sum(1 for c in second_row if self._is_numeric(c)) / len(second_row)
            if second_row else 0
        )
        first_numeric_ratio = (
            sum(1 for c in first_row if self._is_numeric(c)) / len(first_row)
            if first_row else 0
        )
        is_header = (
            first_avg_len < 30
            and first_numeric_ratio < 0.3
            and second_numeric_ratio > first_numeric_ratio
        ) or first_avg_len < 20
        if is_header:
            return first_row, data[1:]
        return [], data

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        if value is None:
            return False
        s = str(value).strip().replace(",", "").replace("$", "").replace("%", "")
        try:
            float(s)
            return True
        except (ValueError, AttributeError):
            return False

    def detect_column_types(self, table: TableStructure) -> List[str]:
        """Detect column types (numeric, text, date)."""
        types: List[str] = []
        for col_idx in range(table.col_count):
            col_data = table.get_column(col_idx)
            numeric_count = sum(
                1 for v in col_data if self._is_numeric(v)
            )
            date_count = sum(
                1 for v in col_data if self._looks_like_date(v)
            )
            if date_count > numeric_count and date_count > len(col_data) * 0.5:
                types.append("date")
            elif numeric_count >= len(col_data) * 0.5:
                types.append("numeric")
            else:
                types.append("text")
        return types

    @staticmethod
    def _looks_like_date(value: Any) -> bool:
        import re
        if not value:
            return False
        s = str(value).strip()
        return bool(
            re.match(r"\d{4}-\d{2}-\d{2}", s)
            or re.match(r"\d{1,2}/\d{1,2}/\d{2,4}", s)
            or re.match(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", s)
        )
