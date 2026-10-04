import pytest
import numpy as np
from src.engines.geometry.element import ElementType, GeometricElement
from src.engines.matrix.matrix_engine import MatrixEngine, TableMatrix


def test_table_matrix_properties():
    headers = ["Year", "Revenue", "Expense"]
    data = np.array([
        [2021.0, 1000000.0, 800000.0],
        [2022.0, 1200000.0, 900000.0],
        [2023.0, 1500000.0, 1100000.0]
    ])
    raw_rows = [
        ["2021", "$1M", "$800K"],
        ["2022", "$1.2M", "$900K"],
        ["2023", "$1.5M", "$1.1M"]
    ]
    
    tbl = TableMatrix(
        matrix_id="M0001",
        element_id="el-1",
        page=1,
        headers=headers,
        data=data,
        raw_rows=raw_rows
    )
    
    assert tbl.n_rows == 3
    assert tbl.n_cols == 3


def test_table_matrix_operations():
    headers = ["Year", "Revenue", "Expense"]
    data = np.array([
        [2021.0, 100.0, 80.0],
        [2022.0, 120.0, 90.0],
        [2023.0, 150.0, 110.0]
    ])
    raw_rows = [
        ["2021", "100", "80"],
        ["2022", "120", "90"],
        ["2023", "150", "110"]
    ]
    tbl = TableMatrix("M01", "el-1", 1, headers, data, raw_rows)
    
    assert tbl.sum("Revenue") == 370.0
    assert tbl.avg("Revenue") == 370.0 / 3
    assert tbl.max_val("Expense") == 110.0
    assert tbl.min_val("Expense") == 80.0
    assert pytest.approx(tbl.growth("Revenue")) == 50.0  # (150-100)/100 * 100


def test_parse_num_helper():
    assert MatrixEngine._parse_num("123") == 123.0
    assert MatrixEngine._parse_num("$1,000") == 1000.0
    assert MatrixEngine._parse_num("2.5M") == 2500000.0
    assert MatrixEngine._parse_num("100K") == 100000.0
    assert MatrixEngine._parse_num("3.5B") == 3500000000.0
    assert np.isnan(MatrixEngine._parse_num("N/A"))


def test_matrix_engine_extract_from_elements():
    engine = MatrixEngine()
    
    table_content = """| Product | Q1 Sales | Q2 Sales |
|---|---|---|
| Widget A | 100K | 120K |
| Widget B | 80K | 90K |"""
    
    el = GeometricElement(
        element_id="el-1",
        page=1,
        type=ElementType.TABLE,
        content=table_content
    )
    
    tables = engine.extract_from_elements([el])
    assert len(tables) == 1
    
    tbl = tables[0]
    assert tbl.headers == ["Product", "Q1 Sales", "Q2 Sales"]
    assert tbl.n_rows == 2
    # Q1 Sales column numeric values: [100000, 80000]
    assert np.array_equal(tbl.column("Q1 Sales"), np.array([100000.0, 80000.0]))


def test_matrix_engine_query():
    engine = MatrixEngine()
    
    table_content = """| Month | Expenses |
|---|---|
| Jan | 5000 |
| Feb | 6000 |
| Mar | 7000 |"""
    
    el = GeometricElement(
        element_id="el-1",
        page=1,
        type=ElementType.TABLE,
        content=table_content
    )
    
    engine.extract_from_elements([el])
    
    answers_sum = engine.query("what is the total expenses?")
    assert len(answers_sum) == 1
    assert "SUM" in answers_sum[0]
    assert "18000.00" in answers_sum[0]
    
    answers_avg = engine.query("average expenses")
    assert len(answers_avg) == 1
    assert "AVG" in answers_avg[0]
    assert "6000.00" in answers_avg[0]


def test_matrix_score():
    engine = MatrixEngine()
    
    table_content = """| Year | Profit |
|---|---|
| 2021 | 10K |
| 2022 | 15K |"""
    
    el = GeometricElement(
        element_id="el-1",
        page=1,
        type=ElementType.TABLE,
        content=table_content
    )
    
    engine.extract_from_elements([el])
    
    # Matching header Profit
    score_match = engine.matrix_score("what was the profit?", el)
    # Generic numerical query
    score_numerical = engine.matrix_score("calculate total revenue", el)
    # Paragraph element should have very low score
    el_para = GeometricElement(element_id="el-2", type=ElementType.PARAGRAPH, content="Some text")
    score_para = engine.matrix_score("what was the profit?", el_para)
    
    assert score_match == 0.90
    assert score_numerical == 0.55
    assert score_para < 0.1
