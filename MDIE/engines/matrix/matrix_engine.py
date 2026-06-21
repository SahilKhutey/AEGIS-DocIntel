"""
AEGIS-MDIE — Matrix Engine
============================
Tables as mathematical objects: M[i,j] = v with dependencies D(i,j).
Enables direct algebraic operations instead of token-level reasoning.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from MDIE.engines.geometry.element import ElementType, GeometricElement

log = logging.getLogger("mdie.matrix")

_NUM_RE = re.compile(r"^-?[\d,_]*\.?\d+(?:[eE][-+]?\d+)?[%$€£]?$")


def _parse_number(s: str) -> Optional[float]:
    """Try to convert a cell string to float. Returns None if not numeric."""
    s = s.strip().replace(",", "").replace("_", "").replace("$", "")
    s = s.replace("€", "").replace("£", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────────────
# TableMatrix
# ─────────────────────────────────────────────────────────────────

@dataclass
class TableMatrix:
    """
    Mathematical representation of a table.

    M = r × c matrix  where  M[i,j] = numeric_value or NaN.
    headers and row_labels preserved for human-readable output.
    """
    table_id:   str
    headers:    list[str]         = field(default_factory=list)
    row_labels: list[str]         = field(default_factory=list)
    raw_rows:   list[list[str]]   = field(default_factory=list)
    page:       int               = 0
    bbox:       Optional[tuple]   = None
    element_id: Optional[str]     = None

    # Computed lazily
    _M:    Optional[np.ndarray] = field(default=None, init=False, repr=False)
    _mask: Optional[np.ndarray] = field(default=None, init=False, repr=False)

    # ──────────────────────────────────────────────────────────────
    # Core numeric matrix
    # ──────────────────────────────────────────────────────────────

    def matrix(self) -> np.ndarray:
        """Build and cache the numeric matrix M[r,c]."""
        if self._M is not None:
            return self._M
        if not self.raw_rows:
            self._M    = np.empty((0, 0))
            self._mask = np.empty((0, 0), dtype=bool)
            return self._M
        r = len(self.raw_rows)
        c = max(len(row) for row in self.raw_rows)
        M    = np.full((r, c), np.nan, dtype=np.float64)
        mask = np.zeros((r, c), dtype=bool)
        for i, row in enumerate(self.raw_rows):
            for j, cell in enumerate(row):
                if j >= c:
                    break
                v = _parse_number(cell)
                if v is not None:
                    M[i, j]    = v
                    mask[i, j] = True
        self._M    = M
        self._mask = mask
        return M

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.raw_rows), max((len(r) for r in self.raw_rows), default=0))

    @property
    def numeric_density(self) -> float:
        if self._mask is None:
            self.matrix()
        return float(self._mask.sum()) / max(1, self._mask.size)

    # ──────────────────────────────────────────────────────────────
    # Column / Row operations
    # ──────────────────────────────────────────────────────────────

    def _col_idx(self, col: str | int) -> int:
        if isinstance(col, int):
            return col
        cl = col.lower()
        for i, h in enumerate(self.headers):
            if h.lower() == cl:
                return i
        raise KeyError(f"Column '{col}' not found in {self.headers}")

    def column(self, col: str | int) -> np.ndarray:
        j = self._col_idx(col)
        M = self.matrix()
        return M[:, j]

    def row(self, i: int) -> np.ndarray:
        return self.matrix()[i, :]

    def col_values(self, col: str | int) -> np.ndarray:
        """Non-NaN values of a column."""
        v = self.column(col)
        return v[~np.isnan(v)]

    # ──────────────────────────────────────────────────────────────
    # Algebraic operations
    # ──────────────────────────────────────────────────────────────

    def col_sum(self, col: str | int) -> float:
        return float(np.nansum(self.column(col)))

    def col_mean(self, col: str | int) -> float:
        vals = self.col_values(col)
        return float(np.mean(vals)) if len(vals) else float("nan")

    def col_std(self, col: str | int) -> float:
        vals = self.col_values(col)
        return float(np.std(vals)) if len(vals) else float("nan")

    def col_min(self, col: str | int) -> float:
        return float(np.nanmin(self.column(col)))

    def col_max(self, col: str | int) -> float:
        return float(np.nanmax(self.column(col)))

    def growth_rate(self, col: str | int) -> Optional[float]:
        """G = (last - first) / |first| for a column."""
        vals = self.col_values(col)
        if len(vals) < 2 or vals[0] == 0:
            return None
        return (vals[-1] - vals[0]) / abs(vals[0])

    def row_sum(self, i: int) -> float:
        return float(np.nansum(self.row(i)))

    def cell(self, i: int, col: str | int) -> Optional[float]:
        j = self._col_idx(col)
        v = self.matrix()[i, j]
        return float(v) if not np.isnan(v) else None

    # ──────────────────────────────────────────────────────────────
    # Dependency relation  D(i,j)
    # ──────────────────────────────────────────────────────────────

    def dependencies(self, i: int, j: int) -> dict[str, Optional[float]]:
        """
        D(i, j) = { M[i, j-1], M[i-1, j], M[i-1, j-1] }
        Tabular neighbours for structural reasoning.
        """
        M = self.matrix()
        def get(r, c):
            if 0 <= r < M.shape[0] and 0 <= c < M.shape[1]:
                v = M[r, c]
                return float(v) if not np.isnan(v) else None
            return None
        return {
            "left":     get(i,   j - 1),
            "above":    get(i-1, j    ),
            "diag":     get(i-1, j - 1),
            "right":    get(i,   j + 1),
            "below":    get(i+1, j    ),
        }

    # ──────────────────────────────────────────────────────────────
    # Serialization
    # ──────────────────────────────────────────────────────────────

    def to_markdown(self) -> str:
        h = self.headers or [f"C{i}" for i in range(self.shape[1])]
        lines = ["| " + " | ".join(h) + " |", "|" + "|".join("---" for _ in h) + "|"]
        for row in self.raw_rows:
            padded = (row + [""] * len(h))[: len(h)]
            lines.append("| " + " | ".join(padded) + " |")
        return "\n".join(lines)

    def to_llm_repr(self) -> str:
        """
        Math-aware LLM serialization:
        - Matrix literal with NaN → '_'
        - Pre-computed column statistics
        - Growth rates where applicable
        """
        M = self.matrix()
        if M.size == 0:
            return f"[Table {self.table_id} — empty]"

        lines = [
            f"[TABLE {self.table_id} | page {self.page} | "
            f"shape {self.shape[0]}×{self.shape[1]}]",
        ]
        if self.headers:
            lines.append("Headers: " + " | ".join(self.headers))
        lines.append("")

        # Matrix display
        lines.append("M =")
        for i in range(M.shape[0]):
            label = self.row_labels[i] if i < len(self.row_labels) else f"r{i}"
            row_str = ", ".join(
                f"{M[i,j]:.4g}" if not np.isnan(M[i,j]) else "_"
                for j in range(M.shape[1])
            )
            lines.append(f"  [{label}]: [{row_str}]")

        # Column statistics
        lines.append("\nColumn statistics:")
        n_cols = M.shape[1]
        for j, h in enumerate(self.headers[:n_cols]):
            col = M[:, j]
            valid = col[~np.isnan(col)]
            if len(valid) == 0:
                continue
            g = self.growth_rate(j)
            g_str = f" | growth={g*100:+.1f}%" if g is not None else ""
            lines.append(
                f"  {h}: sum={valid.sum():.4g} | mean={valid.mean():.4g} "
                f"| min={valid.min():.4g} | max={valid.max():.4g}{g_str}"
            )

        return "\n".join(lines)

    def answer_question(self, question: str) -> str:
        """
        Direct algebraic table QA without sending raw tokens to LLM.
        M(i,j) computations happen here, not in the LLM.
        """
        q = question.lower()

        # Identify target column
        target_col = None
        for h in self.headers:
            if h.lower() in q:
                target_col = h
                break

        if target_col is None:
            return self.to_llm_repr()

        try:
            if any(k in q for k in ("total", "sum")):
                return f"Total {target_col} = {self.col_sum(target_col):.4g}"
            if any(k in q for k in ("average", "mean")):
                return f"Average {target_col} = {self.col_mean(target_col):.4g}"
            if any(k in q for k in ("max", "highest", "largest")):
                return f"Max {target_col} = {self.col_max(target_col):.4g}"
            if any(k in q for k in ("min", "lowest", "smallest")):
                return f"Min {target_col} = {self.col_min(target_col):.4g}"
            if any(k in q for k in ("growth", "increase", "change")):
                g = self.growth_rate(target_col)
                if g is not None:
                    return f"Growth rate of {target_col} = {g*100:+.2f}%"
        except Exception as e:
            log.warning("Table QA failed for '%s': %s", target_col, e)

        return self.to_llm_repr()


# ─────────────────────────────────────────────────────────────────
# Matrix Engine
# ─────────────────────────────────────────────────────────────────

class MatrixEngine:
    """
    Extracts and manages all TableMatrix objects in a document.
    Provides math-aware QA without token overhead.
    """

    def __init__(self):
        self.tables:    list[TableMatrix] = []
        self._id_index: dict[str, TableMatrix] = {}

    def extract_from_elements(self, elements: list[GeometricElement]) -> list[TableMatrix]:
        """Parse all TABLE elements into TableMatrix objects."""
        for e in elements:
            if e.type == ElementType.TABLE:
                tm = self._parse_element(e)
                if tm:
                    self.tables.append(tm)
                    self._id_index[tm.table_id] = tm
        log.info("MatrixEngine: extracted %d tables", len(self.tables))
        return self.tables

    def _parse_element(self, e: GeometricElement) -> Optional[TableMatrix]:
        rows = self._parse_markdown(e.content)
        if not rows:
            return None
        headers    = rows[0] if rows else []
        data_rows  = rows[1:] if len(rows) > 1 else []
        row_labels = [r[0] if r else f"r{i}" for i, r in enumerate(data_rows)]

        tm = TableMatrix(
            table_id   = e.element_id,
            headers    = headers,
            row_labels = row_labels,
            raw_rows   = [r[1:] for r in data_rows],   # exclude label col
            page       = e.page,
            bbox       = e.bbox.to_tuple() if e.bbox else None,
            element_id = e.element_id,
        )
        return tm

    @staticmethod
    def _parse_markdown(md: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in md.splitlines():
            stripped = line.strip()
            if not stripped or set(stripped) <= set("|-: "):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if any(cells):
                rows.append(cells)
        return rows

    def get(self, table_id: str) -> Optional[TableMatrix]:
        return self._id_index.get(table_id)

    def tables_on_page(self, page: int) -> list[TableMatrix]:
        return [t for t in self.tables if t.page == page]

    def query(self, question: str) -> list[str]:
        """
        Query all tables and return non-trivial answers.
        Returns direct algebraic results, bypassing LLM tokenization.
        """
        answers = []
        for t in self.tables:
            ans = t.answer_question(question)
            if not ans.startswith("[TABLE"):
                answers.append(f"From table on page {t.page}:\n{ans}")
        return answers

    def to_llm_context(self, max_tables: int = 5) -> str:
        """Serialize tables for LLM context — math-aware format."""
        out = []
        for t in self.tables[:max_tables]:
            out.append(t.to_llm_repr())
        return "\n\n".join(out)

    def statistics(self) -> dict:
        return {
            "table_count":   len(self.tables),
            "total_cells":   sum(t.shape[0] * t.shape[1] for t in self.tables),
            "avg_density":   round(
                sum(t.numeric_density for t in self.tables) / max(1, len(self.tables)), 3
            ),
            "pages":         sorted({t.page for t in self.tables}),
        }
