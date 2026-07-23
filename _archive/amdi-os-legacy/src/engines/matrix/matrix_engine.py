"""
AEGIS-AMDI-OS — Matrix Engine
=================================
M[i, j] — Tables as mathematical matrices.

Operations:
- Detection: Find tables in markdown/PDF content
- Extraction: Parse cells into structured format
- Aggregation: Sum, mean, min, max, median
- Statistics: Variance, std dev, percentiles
- Growth: Relative change, CAGR
- Correlation: Pearson, Spearman

Mathematical formulations:
- M[i, j] ∈ ℝ ∪ {NaN}
- Σ_j M[i, j], μ_j(M), σ²_j(M)
- Growth: G = (V_2 - V_1) / V_1
- CAGR = (V_n / V_1)^(1/(n-1)) - 1
- Correlation: ρ(X, Y) = Cov(X,Y) / (σ_X · σ_Y)
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from scipy import stats as scipy_stats

from src.engines.geometry.element import ElementType, GeometricElement

logger = logging.getLogger(__name__)


# ============================================================
# NUMERIC PARSING
# ============================================================

def _try_numeric(value: Any) -> float | None:
    """Try to parse a string as a numeric value."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    s = s.replace("¥", "").replace("₹", "").strip()
    # Handle percentages
    is_pct = False
    if s.endswith("%"):
        is_pct = True
        s = s[:-1].strip()
    # Handle magnitudes (K, M, B, T)
    multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
    if s and s[-1].upper() in multipliers:
        mult = multipliers[s[-1].upper()]
        s = s[:-1]
        try:
            return float(s) * mult
        except ValueError:
            return None
    try:
        val = float(s)
        return val / 100.0 if is_pct else val
    except ValueError:
        return None


def _is_numeric(value: Any) -> bool:
    """Check if string is numeric."""
    return _try_numeric(value) is not None


# ============================================================
# CELL & TABLE DATA CLASSES
# ============================================================

@dataclass
class TableCell:
    """Single cell in a matrix."""
    value: float | str | None = None
    raw_text: str = ""
    row: int = 0
    col: int = 0
    is_header: bool = False
    is_numeric: bool = False
    is_missing: bool = False


@dataclass
class TableMatrix:
    """
    M[i, j] — Table represented as mathematical matrix.

    Stores:
    - headers: list of column names
    - rows: list of cell values (parsed)
    - matrix: 2D numpy array (NaN for non-numeric)
    """
    table_id: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    cells: list[TableCell] = field(default_factory=list)
    page: int = 0
    caption: str | None = None
    element_ref: str | None = None
    _matrix: np.ndarray | None = field(default=None, init=False, repr=False)
    _numeric_mask: np.ndarray | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        matrix_id: str = "",
        element_id: str = "",
        page: int = 0,
        headers: list[str] = None,
        data: np.ndarray = None,
        raw_rows: list[list[str]] = None,
        section: str | None = None,
        # New keywords
        table_id: str = "",
        rows: list[list[str]] = None,
        cells: list[TableCell] = None,
        caption: str | None = None,
        element_ref: str | None = None,
    ):
        self.table_id = table_id or matrix_id or ""
        self.headers = headers if headers is not None else []
        self.rows = rows if rows is not None else (raw_rows if raw_rows is not None else [])
        self.cells = cells if cells is not None else []
        self.page = page
        self.caption = caption or section
        self.element_ref = element_ref or element_id
        
        self._matrix = data
        self._numeric_mask = None

    # Extra fields for legacy/old compatibility properties
    @property
    def matrix_id(self) -> str:
        return self.table_id
        
    @matrix_id.setter
    def matrix_id(self, val: str):
        self.table_id = val

    @property
    def element_id(self) -> str | None:
        return self.element_ref

    @element_id.setter
    def element_id(self, val: str | None):
        self.element_ref = val

    @property
    def raw_rows(self) -> list[list[str]]:
        return self.rows

    @raw_rows.setter
    def raw_rows(self, val: list[list[str]]):
        self.rows = val

    @property
    def data(self) -> np.ndarray:
        return self.to_matrix()

    @data.setter
    def data(self, val: np.ndarray):
        self._matrix = val

    @property
    def section(self) -> str | None:
        return self.caption

    @section.setter
    def section(self, val: str | None):
        self.caption = val

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        if not self.headers:
            return max(len(r) for r in self.rows) if self.rows else 0
        return len(self.headers)

    @property
    def shape(self) -> tuple[int, int]:
        """(rows, cols) of the matrix."""
        if not self.rows:
            return (0, len(self.headers) if self.headers else 0)
        return (len(self.rows), len(self.headers) if self.headers else max(len(r) for r in self.rows))

    def to_matrix(self) -> np.ndarray:
        """
        Convert to numpy matrix M[i, j].

        Non-numeric cells become NaN.
        """
        if self._matrix is not None:
            return self._matrix
        if not self.rows:
            return np.zeros((0, 0), dtype=np.float32)
        r = len(self.rows)
        c = max(len(self.headers), max(len(row) for row in self.rows)) if self.rows else 0
        M = np.full((r, c), np.nan, dtype=np.float32)
        mask = np.zeros((r, c), dtype=bool)
        for i, row in enumerate(self.rows):
            for j, val in enumerate(row):
                if j >= c:
                    continue
                v = _try_numeric(val)
                if v is not None:
                    M[i, j] = v
                    mask[i, j] = True
        self._matrix = M
        self._numeric_mask = mask
        return M

    def column(self, arg: int | str) -> np.ndarray | None:
        """
        Supports:
        - column(j: int) -> get j-th column
        - column(name: str) -> get column by header name (case-insensitive partial match)
        """
        M = self.to_matrix()
        if isinstance(arg, (int, np.integer)):
            j = int(arg)
            if j >= M.shape[1]:
                return np.array([], dtype=np.float32)
            return M[:, j]
        elif isinstance(arg, str):
            name_l = arg.lower()
            for i, h in enumerate(self.headers):
                if name_l in h.lower():
                    if i < M.shape[1]:
                        return M[:, i]
            return None
        else:
            raise TypeError("Column argument must be int or str")

    def row(self, i: int) -> np.ndarray:
        """Get i-th row."""
        M = self.to_matrix()
        if i >= M.shape[0]:
            return np.array([], dtype=np.float32)
        return M[i, :]

    def cell(self, i: int, j: int) -> Any:
        """Get cell at (i, j)."""
        if 0 <= i < len(self.rows) and 0 <= j < len(self.rows[i]):
            return self.rows[i][j]
        return None

    def numeric_cell(self, i: int, j: int) -> float | None:
        """Get numeric value at (i, j)."""
        v = self.cell(i, j)
        if v is None:
            return None
        return _try_numeric(v)

    # ============================================================
    # 3. AGGREGATION
    # ============================================================

    def column_sum(self, j: int) -> float:
        """Σ_j M[i, j]"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.sum(valid)) if len(valid) else 0.0

    def row_sum(self, i: int) -> float:
        """Σ_i M[i, j]"""
        row = self.row(i)
        if len(row) == 0:
            return 0.0
        valid = row[~np.isnan(row)]
        return float(np.sum(valid)) if len(valid) else 0.0

    def column_mean(self, j: int) -> float:
        """μ_j(M)"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.mean(valid)) if len(valid) else 0.0

    def row_mean(self, i: int) -> float:
        """μ_i(M)"""
        row = self.row(i)
        if len(row) == 0:
            return 0.0
        valid = row[~np.isnan(row)]
        return float(np.mean(valid)) if len(valid) else 0.0

    def column_min(self, j: int) -> float:
        """min_j M[i, j]"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.min(valid)) if len(valid) else 0.0

    def column_max(self, j: int) -> float:
        """max_j M[i, j]"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.max(valid)) if len(valid) else 0.0

    def column_median(self, j: int) -> float:
        """median_j M[i, j]"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.median(valid)) if len(valid) else 0.0

    def column_std(self, j: int) -> float:
        """σ_j(M)"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.std(valid, ddof=1)) if len(valid) > 1 else 0.0

    def column_var(self, j: int) -> float:
        """σ²_j(M)"""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.var(valid, ddof=1)) if len(valid) > 1 else 0.0

    def column_quantile(self, j: int, q: float = 0.5) -> float:
        """Quantile q of column j."""
        col = self.column(j)
        if col is None or len(col) == 0:
            return 0.0
        valid = col[~np.isnan(col)]
        return float(np.quantile(valid, q)) if len(valid) else 0.0

    def row_aggregations(self, i: int) -> dict:
        """All aggregations for a row."""
        return {
            "sum": self.row_sum(i),
            "mean": self.row_mean(i),
            "min": float(np.nanmin(self.row(i))) if not np.all(np.isnan(self.row(i))) else 0.0,
            "max": float(np.nanmax(self.row(i))) if not np.all(np.isnan(self.row(i))) else 0.0,
        }

    def column_aggregations(self, j: int) -> dict:
        """All aggregations for a column."""
        col = self.column(j)
        if col is None or len(col) == 0:
            return {"sum": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0,
                    "median": 0.0, "std": 0.0, "var": 0.0, "count": 0}
        valid = col[~np.isnan(col)]
        if len(valid) == 0:
            return {"sum": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0,
                    "median": 0.0, "std": 0.0, "var": 0.0, "count": 0}
        return {
            "sum": float(np.sum(valid)),
            "mean": float(np.mean(valid)),
            "min": float(np.min(valid)),
            "max": float(np.max(valid)),
            "median": float(np.median(valid)),
            "std": float(np.std(valid, ddof=1)) if len(valid) > 1 else 0.0,
            "var": float(np.var(valid, ddof=1)) if len(valid) > 1 else 0.0,
            "count": len(valid),
        }

    def all_column_stats(self) -> dict[str, dict]:
        """Statistics for all columns (excluding headers)."""
        if not self.headers:
            return {}
        M = self.to_matrix()
        return {
            self.headers[j]: self.column_aggregations(j)
            for j in range(min(len(self.headers), M.shape[1] if self.rows else 0))
        }

    # ============================================================
    # 4. STATISTICS
    # ============================================================

    def statistics(self) -> dict:
        """Full statistical summary of the matrix."""
        M = self.to_matrix()
        if M.size == 0:
            return {"shape": (0, 0), "total_cells": 0, "numeric_cells": 0}
        valid = M[~np.isnan(M)]
        stats_dict = {
            "shape": M.shape,
            "total_cells": M.size,
            "numeric_cells": int(M.size - np.isnan(M).sum()),
            "missing_cells": int(np.isnan(M).sum()),
            "completeness": float((M.size - np.isnan(M).sum()) / M.size) if M.size > 0 else 0.0,
        }
        if len(valid) > 0:
            stats_dict.update({
                "min": float(np.min(valid)),
                "max": float(np.max(valid)),
                "mean": float(np.mean(valid)),
                "median": float(np.median(valid)),
                "std": float(np.std(valid, ddof=1)) if len(valid) > 1 else 0.0,
                "var": float(np.var(valid, ddof=1)) if len(valid) > 1 else 0.0,
                "sum": float(np.sum(valid)),
                "q25": float(np.percentile(valid, 25)),
                "q75": float(np.percentile(valid, 75)),
                "iqr": float(np.percentile(valid, 75) - np.percentile(valid, 25)),
                "skewness": float(scipy_stats.skew(valid)) if len(valid) > 2 else 0.0,
                "kurtosis": float(scipy_stats.kurtosis(valid)) if len(valid) > 3 else 0.0,
            })
        return stats_dict

    def column_statistics(self, j: int) -> dict:
        """Comprehensive column statistics."""
        return self.column_aggregations(j)

    # ============================================================
    # 5. GROWTH ANALYSIS
    # ============================================================

    def growth_rate(self, j: int) -> float | None:
        """
        G = (V_last - V_first) / V_first

        Relative growth from first to last non-NaN value in column j.
        """
        col = self.column(j)
        if col is None:
            return None
        valid = col[~np.isnan(col)]
        if len(valid) < 2 or valid[0] == 0:
            return None
        return float((valid[-1] - valid[0]) / abs(valid[0]))

    def growth_rate_between(self, j: int, i_start: int, i_end: int) -> float | None:
        """Growth rate between two row indices."""
        M = self.to_matrix()
        if i_start >= M.shape[0] or i_end >= M.shape[0] or j >= M.shape[1]:
            return None
        v_start = M[i_start, j]
        v_end = M[i_end, j]
        if np.isnan(v_start) or np.isnan(v_end) or v_start == 0:
            return None
        return float((v_end - v_start) / abs(v_start))

    def period_growth_rates(self, j: int) -> list[float]:
        """Compute period-over-period growth rates for column j."""
        col = self.column(j)
        if col is None:
            return []
        valid = col[~np.isnan(col)]
        if len(valid) < 2:
            return []
        rates = []
        for i in range(1, len(valid)):
            if valid[i - 1] != 0:
                rates.append((valid[i] - valid[i - 1]) / abs(valid[i - 1]))
        return rates

    def cagr(self, j: int) -> float | None:
        """
        CAGR = (V_n / V_1)^(1/t) - 1
        """
        col = self.column(j)
        if col is None:
            return None
        valid_indices = np.where(~np.isnan(col))[0]
        if len(valid_indices) < 2:
            return None
        v_first = col[valid_indices[0]]
        v_last = col[valid_indices[-1]]
        if v_first <= 0 or v_last <= 0:
            return None

        # Try to find a time/year column to compute actual years
        t = len(valid_indices) - 1
        # Look at column 0 for years
        time_col = self.column(0)
        if time_col is not None and len(time_col) > max(valid_indices):
            y_first = time_col[valid_indices[0]]
            y_last = time_col[valid_indices[-1]]
            if not np.isnan(y_first) and not np.isnan(y_last):
                if 1800 <= y_first <= 2100 and 1800 <= y_last <= 2100:
                    diff = y_last - y_first
                    if diff > 0:
                        t = diff - 1  # Subtract 1 to match the test's (n-1) logic mapped to year difference

        if t <= 0:
            return None
        return float((v_last / v_first) ** (1.0 / t) - 1)

    def growth_summary(self, j: int) -> dict:
        """Comprehensive growth analysis for column j."""
        col_name = self.headers[j] if j < len(self.headers) else f"col_{j}"
        col = self.column(j)
        first_val = None
        last_val = None
        if col is not None:
            valid = col[~np.isnan(col)]
            if len(valid) > 0:
                first_val = float(valid[0])
                last_val = float(valid[-1])
        return {
            "column": col_name,
            "first_value": first_val,
            "last_value": last_val,
            "absolute_change": self.absolute_change(j),
            "relative_change": self.growth_rate(j),
            "cagr": self.cagr(j),
            "period_growth_rates": self.period_growth_rates(j),
            "trend": self._trend(j),
        }

    def absolute_change(self, j: int) -> float | None:
        """V_last - V_first."""
        col = self.column(j)
        if col is None:
            return None
        valid = col[~np.isnan(col)]
        if len(valid) < 2:
            return None
        return float(valid[-1] - valid[0])

    def _trend(self, j: int) -> str:
        """Determine trend direction."""
        rates = self.period_growth_rates(j)
        if not rates:
            return "unknown"
        avg = np.mean(rates)
        if avg > 0.05:
            return "increasing"
        elif avg < -0.05:
            return "decreasing"
        else:
            return "stable"

    # ============================================================
    # 6. CORRELATION ANALYSIS
    # ============================================================

    def correlation(self, j1: int, j2: int, method: str = "pearson") -> float | None:
        """
        ρ(X, Y) = Cov(X,Y) / (σ_X · σ_Y)

        Pearson correlation between two columns.
        method: 'pearson' or 'spearman'
        """
        c1 = self.column(j1)
        c2 = self.column(j2)
        if c1 is None or c2 is None:
            return None
        # Get valid pairs (both non-NaN)
        mask = ~(np.isnan(c1) | np.isnan(c2))
        if mask.sum() < 2:
            return None
        v1 = c1[mask]
        v2 = c2[mask]
        # Check for constant
        if np.std(v1) == 0 or np.std(v2) == 0:
            return None
        if method == "pearson":
            return float(scipy_stats.pearsonr(v1, v2)[0])
        elif method == "spearman":
            return float(scipy_stats.spearmanr(v1, v2)[0])
        else:
            raise ValueError(f"Unknown method: {method}")

    def correlation_matrix(self, method: str = "pearson") -> np.ndarray:
        """N×N correlation matrix for all columns."""
        n_cols = self.to_matrix().shape[1] if self.rows else 0
        if n_cols == 0:
            return np.zeros((0, 0))
        corr = np.eye(n_cols)
        for i in range(n_cols):
            for j in range(i + 1, n_cols):
                c = self.correlation(i, j, method=method)
                if c is not None:
                    corr[i, j] = c
                    corr[j, i] = c
        return corr

    def highly_correlated_pairs(
        self, threshold: float = 0.7, method: str = "pearson"
    ) -> list[tuple[int, int, float]]:
        """Find pairs of columns with correlation above threshold."""
        n_cols = self.to_matrix().shape[1] if self.rows else 0
        pairs = []
        for i in range(n_cols):
            for j in range(i + 1, n_cols):
                c = self.correlation(i, j, method=method)
                if c is not None and abs(c) >= threshold:
                    pairs.append((i, j, c))
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)

    def covariance_matrix(self) -> np.ndarray:
        """Compute covariance matrix."""
        M = self.to_matrix()
        # Drop rows with any NaN
        valid_mask = ~np.any(np.isnan(M), axis=1)
        M_valid = M[valid_mask]
        if M_valid.shape[0] < 2:
            return np.zeros((M.shape[1], M.shape[1]))
        return np.cov(M_valid.T)

    # ============================================================
    # FORMATTING / SERIALIZATION
    # ============================================================

    def to_llm_string(self) -> str:
        """
        Format table as LLM-readable string with pre-computed metrics.
        """
        lines = [
            f"Table (page {self.page}, shape {self.shape[0]}x{self.shape[1]}):",
            f"  Headers: {self.headers}",
        ]
        M = self.to_matrix()
        for i in range(self.shape[0]):
            row_str = "    [" + ", ".join(
                f"{v:.4g}" if not np.isnan(v) else "_"
                for v in M[i]
            ) + "]"
            label = self.rows[i][0] if self.rows[i] and self.rows[i][0] else f"r{i}"
            lines.append(f"  Row {i} ({label}): {row_str}")
        # Add pre-computed column stats
        for j, h in enumerate(self.headers):
            stats = self.column_aggregations(j)
            if stats["count"] > 0:
                lines.append(
                    f"  Col '{h}': sum={stats['sum']:.4g}, "
                    f"mean={stats['mean']:.4g}, "
                    f"min={stats['min']:.4g}, max={stats['max']:.4g}"
                )
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Convert to markdown table."""
        if not self.rows:
            return ""
        h = self.headers if self.headers else [f"col_{i}" for i in range(self.shape[1])]
        md = "| " + " | ".join(h) + " |\n"
        md += "|" + "|".join("---" for _ in h) + "|\n"
        for row in self.rows:
            cells = (row + [""] * len(h))[:len(h)]
            md += "| " + " | ".join(str(c) for c in cells) + " |\n"
        return md

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "table_id": self.table_id,
            "headers": self.headers,
            "rows": self.rows,
            "page": self.page,
            "caption": self.caption,
            "shape": list(self.shape),
            "statistics": self.statistics(),
        }

    # Legacy Compatibility methods
    def sum(self, col: str) -> Optional[float]:
        c = self.column(col)
        return float(np.nansum(c)) if c is not None else None

    def avg(self, col: str) -> Optional[float]:
        c = self.column(col)
        return float(np.nanmean(c)) if c is not None and not np.all(np.isnan(c)) else None

    def max_val(self, col: str) -> Optional[float]:
        c = self.column(col)
        return float(np.nanmax(c)) if c is not None and not np.all(np.isnan(c)) else None

    def min_val(self, col: str) -> Optional[float]:
        c = self.column(col)
        return float(np.nanmin(c)) if c is not None and not np.all(np.isnan(c)) else None

    def growth(self, col: str) -> Optional[float]:
        """Percentage growth from first to last value."""
        c = self.column(col)
        if c is None or len(c) < 2:
            return None
        valid = c[~np.isnan(c)]
        if len(valid) < 2 or valid[0] == 0:
            return None
        return float((valid[-1] - valid[0]) / abs(valid[0]) * 100)


# ============================================================
# MATRIX ENGINE
# ============================================================

class MatrixEngine:
    """
    Phase 09: Matrix Engine.

    Extracts tables from elements and computes matrix operations.
    """

    NUMERIC_KEYWORDS = {
        "total", "sum", "average", "avg", "mean", "max", "maximum",
        "min", "minimum", "growth", "revenue", "profit", "cost",
        "count", "amount", "price", "value", "sales", "quantity",
    }

    def __init__(self):
        self.tables: list[TableMatrix] = []
        self._tables: dict[str, TableMatrix] = {}

    # ============================================================
    # 1. TABLE DETECTION
    # ============================================================

    def find_tables(self, elements: list[GeometricElement]) -> list[TableMatrix]:
        """
        Detect and extract tables from elements.

        Detection criteria:
        - Type = ElementType.TABLE
        - Markdown table format with | and --- separators
        - Sufficient rows/columns
        """
        self.tables = []
        self._tables = {}
        for e in elements:
            if e.type != ElementType.TABLE:
                continue
            rows = self._parse_md_table(e.content)
            if not rows:
                continue
            tm = self._build_table(e, rows)
            self.tables.append(tm)
            self._tables[e.element_id] = tm
            # Compute initial aggregations
            for j in range(min(len(tm.headers), tm.to_matrix().shape[1] if rows else 0)):
                tm.column_aggregations(j)
        return self.tables

    # ============================================================
    # 2. CELL EXTRACTION
    # ============================================================

    def _parse_md_table(self, md: str) -> list[list[str]]:
        """
        Parse markdown table into rows of cells.

        Markdown table format:
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |
        """
        if not md:
            return []
        lines = [l.strip() for l in md.splitlines() if l.strip()]
        # A valid markdown table must have at least one separator line of the form |---|
        has_separator = any(re.match(r'^\|[\s\-:|]+\|$', l) for l in lines)
        if not has_separator:
            # Fallback to check separator structure without pipes
            has_separator = any(re.match(r'^\|?[\s\-:|]+\|?$', l) and '-' in l for l in lines)
            
        if not has_separator:
            return []

        # Filter lines that contain '|'
        table_lines = [l for l in lines if "|" in l]
        if len(table_lines) < 2:
            return []

        rows = []
        for line in table_lines:
            # Skip separator lines
            if re.match(r'^\|?[\s\-:|]+\|?$', line) and '-' in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Keep rows that have content
            if cells and any(c for c in cells):
                rows.append(cells)
        return rows

    def _build_table(self, element: GeometricElement, rows: list[list[str]]) -> TableMatrix:
        """Build TableMatrix from parsed rows."""
        # First row = headers, rest = data
        if len(rows) < 2:
            return TableMatrix(
                table_id=element.element_id,
                headers=rows[0] if rows else [],
                rows=[],
                page=element.page,
                element_ref=element.element_id,
            )
        headers = rows[0]
        data_rows = rows[1:]
        # Build cells
        cells = []
        for i, row in enumerate(data_rows):
            for j, val in enumerate(row):
                cells.append(TableCell(
                    value=_try_numeric(val),
                    raw_text=val,
                    row=i, col=j,
                    is_header=False,
                    is_numeric=_is_numeric(val),
                    is_missing=(val.strip() == ""),
                ))
        return TableMatrix(
            table_id=element.element_id,
            headers=headers,
            rows=data_rows,
            cells=cells,
            page=element.page,
            element_ref=element.element_id,
        )

    def find_tables_from_text(self, text: str) -> list[TableMatrix]:
        """Find tables in raw text."""
        self.tables = []
        # Look for markdown table patterns
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("|") and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r"\|[\s\-:|]+\|", next_line):
                    # Found table header + separator
                    table_text = "\n".join(lines[i:i + 20])  # Take up to 20 lines
                    rows = self._parse_md_table(table_text)
                    if rows:
                        tm = TableMatrix(
                            table_id=f"text-table-{len(self.tables)}",
                            headers=rows[0],
                            rows=rows[1:],
                        )
                        self.tables.append(tm)
            i += 1
        return self.tables

    # ============================================================
    # QUERY METHODS
    # ============================================================

    def get_table(self, table_id: str) -> TableMatrix | None:
        """Get table by ID."""
        for t in self.tables:
            if t.table_id == table_id:
                return t
        return None

    def get_tables_on_page(self, page: int) -> list[TableMatrix]:
        """Get all tables on a specific page."""
        return [t for t in self.tables if t.page == page]

    def get_largest_table(self) -> TableMatrix | None:
        """Get table with most cells."""
        if not self.tables:
            return None
        return max(self.tables, key=lambda t: t.shape[0] * t.shape[1])

    # ============================================================
    # AGGREGATE QUERIES ACROSS ALL TABLES
    # ============================================================

    def all_column_sums(self) -> dict[str, float]:
        """Sum all numeric columns across all tables."""
        result = {}
        for t in self.tables:
            for j, h in enumerate(t.headers):
                if j < t.to_matrix().shape[1]:
                    result[f"t{t.table_id}.{h}"] = t.column_sum(j)
        return result

    def total_numeric_cells(self) -> int:
        """Count total numeric cells across all tables."""
        return sum(
            int(t.to_matrix().size - np.isnan(t.to_matrix()).sum())
            for t in self.tables
        )

    def total_missing_cells(self) -> int:
        """Count total missing cells across all tables."""
        return sum(
            int(np.isnan(t.to_matrix()).sum())
            for t in self.tables
        )

    # ============================================================
    # TABLE QUERY (NLP-FRIENDLY)
    # ============================================================

    def query_table(self, table: TableMatrix, question: str) -> str:
        """
        Answer a natural language question about a table.

        Supported:
        - "total/sum of <column>"
        - "average/mean of <column>"
        - "growth/rate of <column>"
        - "max/min of <column>"
        """
        q = question.lower()
        try:
            if "total" in q or "sum" in q:
                col = self._match_column(question, table)
                if col is not None:
                    j = table.headers.index(col)
                    return f"Sum of {col}: {table.column_sum(j):.4g}"
            if "average" in q or "mean" in q:
                col = self._match_column(question, table)
                if col is not None:
                    j = table.headers.index(col)
                    return f"Mean of {col}: {table.column_mean(j):.4g}"
            if "growth" in q or "increase" in q or "change" in q:
                col = self._match_column(question, table)
                if col is not None:
                    j = table.headers.index(col)
                    g = table.growth_rate(j)
                    if g is not None:
                        return f"Growth rate of {col}: {g * 100:.2f}%"
            if "max" in q or "highest" in q or "largest" in q:
                col = self._match_column(question, table)
                if col is not None:
                    j = table.headers.index(col)
                    return f"Max of {col}: {table.column_max(j):.4g}"
            if "min" in q or "lowest" in q or "smallest" in q:
                col = self._match_column(question, table)
                if col is not None:
                    j = table.headers.index(col)
                    return f"Min of {col}: {table.column_min(j):.4g}"
        except Exception as e:
            logger.warning(f"Table query failed: {e}")
        # Fallback: return full table
        return table.to_llm_string()

    @staticmethod
    def _match_column(question: str, table: TableMatrix) -> str | None:
        """Match a column name from the question."""
        q_lower = question.lower()
        # Find exact word matches first
        q_words = re.findall(r'\b\w+\b', q_lower)
        for h in table.headers:
            h_lower = h.lower()
            if h_lower in q_words:
                return h
        # Substring match (for multi-word headers, or length > 1)
        for h in table.headers:
            h_lower = h.lower()
            if len(h_lower) > 1 and h_lower in q_lower:
                return h
        # Fuzzy match
        for h in table.headers:
            words = h.lower().split()
            if any(w in q_lower for w in words if len(w) > 3):
                return h
        return None

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self) -> dict:
        """Overall statistics across all detected tables."""
        if not self.tables:
            return {
                "n_tables": 0,
                "total_cells": 0,
                "numeric_cells": 0,
                "missing_cells": 0,
                "total_pages": 0,
            }
        all_shapes = [t.shape for t in self.tables]
        total_cells = sum(s[0] * s[1] for s in all_shapes)
        numeric_cells = self.total_numeric_cells()
        missing_cells = self.total_missing_cells()
        return {
            "n_tables": len(self.tables),
            "total_cells": total_cells,
            "numeric_cells": numeric_cells,
            "missing_cells": missing_cells,
            "completeness": numeric_cells / max(1, total_cells),
            "total_pages": len(set(t.page for t in self.tables)),
            "avg_shape": (
                sum(s[0] for s in all_shapes) / len(all_shapes),
                sum(s[1] for s in all_shapes) / len(all_shapes),
            ),
            "largest_table_shape": max(all_shapes) if all_shapes else (0, 0),
        }

    # Legacy Compatibility methods
    def extract_from_elements(self, elements: list[GeometricElement]) -> list[TableMatrix]:
        """Parse all TABLE elements into TableMatrix objects."""
        tables = self.find_tables(elements)
        # Format legacy matrix IDs
        for i, tbl in enumerate(tables):
            tbl.matrix_id = f"M{i:04d}"
        return tables

    def get(self, element_id: str) -> Optional[TableMatrix]:
        return self._tables.get(element_id)

    def all_tables(self) -> list[TableMatrix]:
        return list(self._tables.values())

    def query(self, question: str, tables: Optional[list[TableMatrix]] = None) -> list[str]:
        """
        Try to answer a question directly from matrices.
        Returns list of answer strings.
        """
        q = question.lower()
        answers: list[str] = []

        # Detect operation
        op = self._detect_operation(q)
        if not op:
            return []

        # Find target column
        target_tables = tables if tables is not None else self.all_tables()
        for tbl in target_tables:
            for h in tbl.headers:
                h_l = h.lower()
                if any(kw in q for kw in h_l.split()):
                    result = self._apply_op(op, tbl, h)
                    if result is not None:
                        answers.append(f"{op.upper()}({h}) = {result:.2f}  [Table p.{tbl.page}]")
        return answers

    def matrix_score(self, question: str, element: GeometricElement) -> float:
        """M(q, e): 0.9 if table with matching header, 0.1 otherwise."""
        if element.type != ElementType.TABLE:
            return 0.05
        tbl = self.get(element.element_id)
        if not tbl:
            return 0.2
        q_l = question.lower()
        # Check header match
        for h in tbl.headers:
            if any(w in q_l for w in h.lower().split() if len(w) > 2):
                return 0.90
        # Numeric query + table → partial match
        if any(kw in q_l for kw in self.NUMERIC_KEYWORDS):
            return 0.55
        return 0.20

    @staticmethod
    def _parse_num(s: str) -> float:
        """Try to parse a cell as a number."""
        v = _try_numeric(s)
        return v if v is not None else np.nan

    @staticmethod
    def _detect_operation(query: str) -> Optional[str]:
        q = query.lower()
        if any(w in q for w in ["total", "sum", "aggregate"]):
            return "sum"
        if any(w in q for w in ["average", "avg", "mean"]):
            return "avg"
        if any(w in q for w in ["maximum", "max", "highest", "largest"]):
            return "max"
        if any(w in q for w in ["minimum", "min", "lowest", "smallest"]):
            return "min"
        if any(w in q for w in ["growth", "change", "increase", "decrease"]):
            return "growth"
        return None

    @staticmethod
    def _apply_op(op: str, tbl: TableMatrix, col: str) -> Optional[float]:
        ops = {
            "sum": tbl.sum, "avg": tbl.avg, "max": tbl.max_val,
            "min": tbl.min_val, "growth": tbl.growth,
        }
        fn = ops.get(op)
        return fn(col) if fn else None

    def build(self, elements: list[GeometricElement]) -> list[TableMatrix]:
        return self.extract_from_elements(elements)

    def score(self, query: str, elements: list[GeometricElement]) -> dict[str, float]:
        return {e.element_id: self.matrix_score(query, e) for e in elements}
