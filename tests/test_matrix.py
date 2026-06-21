"""Tests for the matrix engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import math
import pytest
import numpy as np

from src.engines.geometry.element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox
from src.engines.matrix import (
    MatrixEngine, TableMatrix, TableCell,
    _try_numeric, _is_numeric,
)


# ============================================================
# HELPERS
# ============================================================

def make_table_element(content: str, page: int = 1) -> GeometricElement:
    return GeometricElement(
        content=content, page=page, type=ElementType.TABLE,
        bbox=BoundingBox(0.1, 0.1, 0.9, 0.5),
    )


SAMPLE_TABLE = """| Region | 2024 | 2025 |
|--------|------|------|
| India  | 300  | 500  |
| US     | 200  | 250  |
| EU     | 100  | 150  |
| Total  | 600  | 900  |"""


# ============================================================
# NUMERIC PARSING
# ============================================================

def test_try_numeric_simple():
    assert _try_numeric("100") == 100.0
    assert _try_numeric("100.5") == 100.5
    assert _try_numeric("-50") == -50.0


def test_try_numeric_with_commas():
    assert _try_numeric("1,000") == 1000.0
    assert _try_numeric("1,000,000") == 1000000.0


def test_try_numeric_with_currency():
    assert _try_numeric("$100") == 100.0
    assert _try_numeric("€50") == 50.0
    assert _try_numeric("£75") == 75.0
    assert _try_numeric("¥1000") == 1000.0


def test_try_numeric_with_suffixes():
    assert _try_numeric("1K") == 1000.0
    assert _try_numeric("1M") == 1_000_000.0
    assert _try_numeric("1B") == 1_000_000_000.0
    assert _try_numeric("1T") == 1_000_000_000_000.0


def test_try_numeric_percentages():
    assert _try_numeric("50%") == 0.5
    assert _try_numeric("100%") == 1.0
    assert _try_numeric("25.5%") == 0.255


def test_try_numeric_invalid():
    assert _try_numeric("abc") is None
    assert _try_numeric("") is None
    assert _try_numeric("12abc") is None
    assert _try_numeric(None) is None


def test_is_numeric():
    assert _is_numeric("100")
    assert _is_numeric("$50.5")
    assert _is_numeric("1M")
    assert not _is_numeric("hello")
    assert not _is_numeric("")
    assert not _is_numeric("abc123")


# ============================================================
# TABLE CELL
# ============================================================

def test_cell_creation():
    cell = TableCell(value=100, raw_text="100", row=0, col=0, is_numeric=True)
    assert cell.value == 100
    assert cell.is_numeric
    assert not cell.is_missing


def test_cell_missing():
    cell = TableCell(value=None, raw_text="", row=0, col=0, is_missing=True)
    assert cell.is_missing


def test_cell_header():
    cell = TableCell(raw_text="Region", is_header=True)
    assert cell.is_header


# ============================================================
# TABLE PARSING
# ============================================================

def test_parse_md_table_basic():
    engine = MatrixEngine()
    rows = engine._parse_md_table(SAMPLE_TABLE)
    assert len(rows) == 5  # 1 header + 4 data
    assert rows[0] == ["Region", "2024", "2025"]
    assert rows[1] == ["India", "300", "500"]


def test_parse_md_table_separator_skipped():
    engine = MatrixEngine()
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    rows = engine._parse_md_table(md)
    assert len(rows) == 2
    assert rows[0] == ["A", "B"]
    assert rows[1] == ["1", "2"]


def test_parse_md_table_empty():
    engine = MatrixEngine()
    assert engine._parse_md_table("") == []


def test_parse_md_table_no_table():
    engine = MatrixEngine()
    assert engine._parse_md_table("Just text\nMore text") == []


def test_parse_md_table_irregular_columns():
    """Handle rows with varying column counts."""
    engine = MatrixEngine()
    md = "| A | B |\n|---|---|\n| 1 | 2 | 3 |\n| 4 |"
    rows = engine._parse_md_table(md)
    assert len(rows) == 3
    assert rows[0] == ["A", "B"]


def test_parse_md_table_extra_spaces():
    engine = MatrixEngine()
    md = "|   A   |   B   |\n| --- | --- |\n|  1  |  2  |"
    rows = engine._parse_md_table(md)
    assert rows[0] == ["A", "B"]  # Whitespace stripped


# ============================================================
# 1. TABLE DETECTION
# ============================================================

def test_find_tables_basic():
    engine = MatrixEngine()
    elements = [make_table_element(SAMPLE_TABLE)]
    tables = engine.find_tables(elements)
    assert len(tables) == 1
    assert tables[0].headers == ["Region", "2024", "2025"]


def test_find_tables_multiple():
    engine = MatrixEngine()
    elements = [
        make_table_element(SAMPLE_TABLE, page=1),
        make_table_element(SAMPLE_TABLE, page=2),
    ]
    tables = engine.find_tables(elements)
    assert len(tables) == 2


def test_find_tables_no_tables():
    engine = MatrixEngine()
    elements = [
        GeometricElement(content="Not a table", page=1, type=ElementType.TEXT),
        GeometricElement(content="Just text", page=1, type=ElementType.HEADING),
    ]
    tables = engine.find_tables(elements)
    assert len(tables) == 0


def test_find_tables_ignores_invalid_markdown():
    engine = MatrixEngine()
    elements = [make_table_element("This is not a table format")]
    tables = engine.find_tables(elements)
    assert len(tables) == 0


def test_find_tables_from_text():
    engine = MatrixEngine()
    text = """Some intro text.

| Header | Value |
|--------|-------|
| A      | 100   |
| B      | 200   |

More text after."""
    tables = engine.find_tables_from_text(text)
    assert len(tables) == 1
    assert tables[0].headers == ["Header", "Value"]


# ============================================================
# 2. CELL EXTRACTION
# ============================================================

def test_cell_extraction():
    engine = MatrixEngine()
    elements = [make_table_element(SAMPLE_TABLE)]
    tables = engine.find_tables(elements)
    table = tables[0]
    assert table.headers[0] == "Region"
    assert table.headers[1] == "2024"
    assert table.headers[2] == "2025"


def test_numeric_cell_extraction():
    engine = MatrixEngine()
    elements = [make_table_element(SAMPLE_TABLE)]
    tables = engine.find_tables(elements)
    table = tables[0]
    v = table.numeric_cell(0, 1)  # First data row, second col
    assert v == 300.0


def test_cells_objects():
    engine = MatrixEngine()
    elements = [make_table_element(SAMPLE_TABLE)]
    tables = engine.find_tables(elements)
    table = tables[0]
    assert len(table.cells) > 0
    cell = next((c for c in table.cells if c.row == 0 and c.col == 1), None)
    assert cell is not None
    assert cell.is_numeric
    assert cell.value == 300.0


# ============================================================
# 3. AGGREGATION
# ============================================================

def test_column_sum():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])
    assert table.column_sum(0) == 4.0  # 1+3
    assert table.column_sum(1) == 6.0  # 2+4


def test_column_sum_with_nan():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A"], rows=[["1"], ["abc"], ["3"]])
    assert table.column_sum(0) == 4.0


def test_row_sum():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A", "B"], rows=[["10", "20"]])
    assert table.row_sum(0) == 30.0


def test_column_mean():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A"], rows=[["10"], ["20"], ["30"]])
    assert table.column_mean(0) == 20.0


def test_column_min_max():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A"], rows=[["5"], ["1"], ["9"], ["3"]])
    assert table.column_min(0) == 1.0
    assert table.column_max(0) == 9.0


def test_column_median():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A"], rows=[["1"], ["5"], ["3"]])
    assert table.column_median(0) == 3.0


def test_column_aggregations():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Values"],
        rows=[["10"], ["20"], ["30"], ["40"]],
    )
    stats = table.column_aggregations(0)
    assert stats["sum"] == 100.0
    assert stats["mean"] == 25.0
    assert stats["min"] == 10.0
    assert stats["max"] == 40.0
    assert stats["median"] == 25.0
    assert stats["count"] == 4


def test_column_quantile():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[[str(i)] for i in range(1, 101)],
    )
    assert table.column_quantile(0, 0.5) == 50.5  # Median
    assert table.column_quantile(0, 0.25) == 25.75  # Q1


def test_all_column_stats():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A", "B"],
        rows=[["1", "10"], ["2", "20"], ["3", "30"]],
    )
    stats = table.all_column_stats()
    assert "A" in stats
    assert "B" in stats
    assert stats["A"]["sum"] == 6.0
    assert stats["B"]["mean"] == 20.0


# ============================================================
# 4. STATISTICS
# ============================================================

def test_statistics_basic():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["1"], ["2"], ["3"], ["4"], ["5"]],
    )
    stats = table.statistics()
    assert stats["shape"] == (5, 1)
    assert stats["total_cells"] == 5
    assert stats["numeric_cells"] == 5
    assert stats["missing_cells"] == 0
    assert stats["completeness"] == 1.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["mean"] == 3.0
    assert stats["std"] == pytest.approx(1.581, abs=0.01)


def test_statistics_with_missing():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["1"], ["abc"], ["3"], ["xyz"]],
    )
    stats = table.statistics()
    assert stats["numeric_cells"] == 2
    assert stats["missing_cells"] == 2
    assert stats["completeness"] == 0.5


def test_statistics_empty_table():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1")
    stats = table.statistics()
    assert stats["shape"] == (0, 0)
    assert stats["total_cells"] == 0


def test_statistics_std_with_one_value():
    engine = MatrixEngine()
    table = TableMatrix(table_id="t1", headers=["A"], rows=[["5"]])
    stats = table.statistics()
    assert stats["std"] == 0.0


def test_statistics_quantiles():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[[str(i)] for i in range(1, 11)],  # 1-10
    )
    stats = table.statistics()
    assert stats["q25"] == pytest.approx(3.25, abs=0.01)
    assert stats["q75"] == pytest.approx(7.75, abs=0.01)
    assert stats["iqr"] == pytest.approx(4.5, abs=0.01)


def test_statistics_skewness():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["1"], ["1"], ["1"], ["10"]],
    )
    stats = table.statistics()
    assert stats["skewness"] > 0.0


# ============================================================
# 5. GROWTH ANALYSIS
# ============================================================

def test_growth_rate_positive():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Revenue"],
        rows=[["2020", "100"], ["2024", "150"]],
    )
    assert table.growth_rate(1) == 0.5


def test_growth_rate_negative():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Revenue"],
        rows=[["2020", "200"], ["2024", "100"]],
    )
    assert table.growth_rate(1) == -0.5


def test_growth_rate_zero():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Revenue"],
        rows=[["2020", "100"], ["2024", "100"]],
    )
    assert table.growth_rate(1) == 0.0


def test_growth_rate_no_change_zero_start():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["0"], ["100"]],
    )
    assert table.growth_rate(0) is None


def test_growth_rate_between():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Value"],
        rows=[["2020", "100"], ["2022", "150"], ["2024", "200"]],
    )
    assert table.growth_rate_between(1, 0, 2) == 1.0


def test_period_growth_rates():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Value"],
        rows=[["2020", "100"], ["2021", "110"], ["2022", "121"], ["2023", "133"]],
    )
    rates = table.period_growth_rates(1)
    assert len(rates) == 3
    assert rates[0] == pytest.approx(0.1, abs=0.001)
    assert rates[1] == pytest.approx(0.1, abs=0.001)
    assert rates[2] == pytest.approx(0.099, abs=0.001)


def test_cagr():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Value"],
        rows=[["2020", "100"], ["2024", "200"]],
    )
    cagr = table.cagr(1)
    assert cagr == pytest.approx(0.2599, abs=0.001)


def test_cagr_zero():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Value"],
        rows=[["2020", "100"], ["2024", "100"]],
    )
    assert table.cagr(1) == 0.0


def test_growth_summary():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["Year", "Revenue"],
        rows=[["2020", "100"], ["2024", "200"]],
    )
    summary = table.growth_summary(1)
    assert summary["column"] == "Revenue"
    assert summary["first_value"] == 100.0
    assert summary["last_value"] == 200.0
    assert summary["absolute_change"] == 100.0
    assert summary["relative_change"] == 1.0
    assert summary["trend"] == "increasing"


def test_trend_detection():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["100"], ["80"], ["60"], ["40"]],
    )
    assert table._trend(0) == "decreasing"


def test_absolute_change():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["10"], ["25"], ["40"]],
    )
    assert table.absolute_change(0) == 30.0


# ============================================================
# 6. CORRELATION ANALYSIS
# ============================================================

def test_correlation_perfect_positive():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["1", "2"], ["2", "4"], ["3", "6"], ["4", "8"]],  # Y = 2X
    )
    assert table.correlation(0, 1) == pytest.approx(1.0, abs=1e-6)


def test_correlation_perfect_negative():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["1", "10"], ["2", "8"], ["3", "6"], ["4", "4"]],  # Y = -2X + 12
    )
    assert table.correlation(0, 1) == pytest.approx(-1.0, abs=1e-6)


def test_correlation_no_relationship():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["1", "5"], ["2", "1"], ["3", "8"], ["4", "3"]],
    )
    c = table.correlation(0, 1)
    assert -0.5 < c < 0.5


def test_correlation_with_missing_values():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["1", "2"], ["abc", "4"], ["3", "6"], ["4", "xyz"]],
    )
    c = table.correlation(0, 1)
    assert c is not None


def test_correlation_constant_column():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["5", "1"], ["5", "2"], ["5", "3"]],
    )
    assert table.correlation(0, 1) is None


def test_correlation_insufficient_data():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["1", "2"]],
    )
    assert table.correlation(0, 1) is None


def test_correlation_spearman():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["X", "Y"],
        rows=[["1", "100"], ["2", "50"], ["3", "25"], ["4", "12"]],
    )
    spearman = table.correlation(0, 1, method="spearman")
    assert spearman == pytest.approx(-1.0, abs=0.01)


def test_correlation_matrix():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A", "B", "C"],
        rows=[["1", "10", "100"], ["2", "20", "50"], ["3", "30", "10"]],
    )
    corr = table.correlation_matrix()
    assert corr.shape == (3, 3)
    assert corr[0, 1] == pytest.approx(1.0)
    assert corr[0, 2] < 0.0


def test_highly_correlated_pairs():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A", "B", "C"],
        rows=[["1", "2", "100"], ["2", "4", "50"], ["3", "6", "10"]],
    )
    pairs = table.highly_correlated_pairs(threshold=0.9)
    assert len(pairs) >= 1
    # A and B are perfectly correlated (1.0)
    assert pairs[0][0] == 0 and pairs[0][1] == 1


def test_covariance_matrix():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A", "B"],
        rows=[["1", "10"], ["2", "20"], ["3", "30"]],
    )
    cov = table.covariance_matrix()
    assert cov.shape == (2, 2)
    assert cov[0, 0] > 0.0


def test_to_llm_string():
    table = TableMatrix(
        table_id="t1", headers=["A", "B"],
        rows=[["1", "10"], ["2", "20"]],
    )
    s = table.to_llm_string()
    assert "Headers: ['A', 'B']" in s
    assert "Row 0" in s


def test_to_markdown():
    table = TableMatrix(
        table_id="t1", headers=["A", "B"],
        rows=[["1", "10"], ["2", "20"]],
    )
    md = table.to_markdown()
    assert "| A | B |" in md
    assert "| 1 | 10 |" in md


def test_to_dict():
    table = TableMatrix(
        table_id="t1", headers=["A"],
        rows=[["1"], ["2"]],
    )
    d = table.to_dict()
    assert d["table_id"] == "t1"
    assert d["shape"] == [2, 1]
    assert "statistics" in d


def test_query_table_sum():
    engine = MatrixEngine()
    table = TableMatrix(
        table_id="t1", headers=["A", "Revenue"],
        rows=[["1", "100"], ["2", "200"]],
    )
    ans = engine.query_table(table, "what is total Revenue?")
    assert "300" in ans


def test_all_column_sums():
    engine = MatrixEngine()
    elements = [make_table_element(SAMPLE_TABLE)]
    engine.find_tables(elements)
    sums = engine.all_column_sums()
    # Checks headers like t<id>.<header>
    assert len(sums) > 0


def test_overall_statistics():
    engine = MatrixEngine()
    elements = [make_table_element(SAMPLE_TABLE)]
    engine.find_tables(elements)
    stats = engine.statistics()
    assert stats["n_tables"] == 1
    assert stats["completeness"] > 0.5
