"""
tests/processing/tables/test_table_reconstruction.py
===================================================
Tests TAB-001 through TAB-007 verifying table grid validation, cell accuracy,
numeric matching, TEDS structural similarity, and schema conformance.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.processing.models import TableCellModel, TableReconstruction
from aegis.processing.tables import (
    TableEvaluationReport,
    TableEvaluator,
    TableExtractor,
    TableGridValidator,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TABLE_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "table.schema.json"


@pytest.fixture
def table_schema():
    with open(TABLE_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_tab_001_grid_construction_and_validation():
    """TAB-001: Verify grid validation catches invalid spans and cell collisions."""
    valid_table = TableReconstruction(
        table_id="T1",
        document_id="D1",
        page_number=1,
        bbox=[50.0, 50.0, 400.0, 200.0],
        row_count=2,
        column_count=2,
        cells=[
            TableCellModel(cell_id="C00", row_index=0, column_index=0, text="Item", bbox=[50.0, 50.0, 200.0, 100.0]),
            TableCellModel(cell_id="C01", row_index=0, column_index=1, text="Price", bbox=[200.0, 50.0, 400.0, 100.0]),
            TableCellModel(cell_id="C10", row_index=1, column_index=0, text="Widget", bbox=[50.0, 100.0, 200.0, 200.0]),
            TableCellModel(cell_id="C11", row_index=1, column_index=1, text="$10.00", bbox=[200.0, 100.0, 400.0, 200.0]),
        ],
        header_rows=[0],
        source_reference="D1:P1",
    )
    is_valid, errs = TableGridValidator.validate(valid_table)
    assert is_valid is True
    assert len(errs) == 0

    # Collision: two cells at (0, 0)
    invalid_table = TableReconstruction(
        table_id="T_COLLISION",
        document_id="D1",
        page_number=1,
        bbox=[0.0, 0.0, 100.0, 100.0],
        row_count=2,
        column_count=2,
        cells=[
            TableCellModel(cell_id="C_A", row_index=0, column_index=0, text="A", bbox=[0.0, 0.0, 50.0, 50.0]),
            TableCellModel(cell_id="C_B", row_index=0, column_index=0, text="B", bbox=[0.0, 0.0, 50.0, 50.0]),
        ],
        header_rows=[0],
        source_reference="D1:P1",
    )
    is_valid_inv, errs_inv = TableGridValidator.validate(invalid_table)
    assert is_valid_inv is False
    assert any("Cell collision" in e for e in errs_inv)


def test_tab_002_table_to_html_serialization():
    """TAB-002: Verify HTML table serialization with proper th/td and spans."""
    table = TableReconstruction(
        table_id="T2",
        document_id="D1",
        page_number=1,
        bbox=[0.0, 0.0, 100.0, 100.0],
        row_count=2,
        column_count=2,
        cells=[
            TableCellModel(cell_id="C0", row_index=0, column_index=0, column_span=2, role="column_header", text="Full Header", bbox=[0.0, 0.0, 100.0, 50.0]),
            TableCellModel(cell_id="C1", row_index=1, column_index=0, text="Data 1", bbox=[0.0, 50.0, 50.0, 100.0]),
            TableCellModel(cell_id="C2", row_index=1, column_index=1, text="Data 2", bbox=[50.0, 50.0, 100.0, 100.0]),
        ],
        header_rows=[0],
        source_reference="D1:P1",
    )
    html = TableGridValidator.to_html(table)
    assert "<table>" in html
    assert '<th colspan="2">Full Header</th>' in html
    assert "<td>Data 1</td>" in html


def test_tab_003_cell_accuracy_and_numeric_matching():
    """TAB-003: Verify exact match and normalized numeric value matching."""
    gt = TableExtractor.from_grid_data(
        table_id="GT_TAB",
        document_id="DOC1",
        page_number=1,
        headers=["Year", "Revenue", "Margin"],
        data_rows=[["2023", "$383,285", "29.8%"]],
    )

    pred = TableExtractor.from_grid_data(
        table_id="PRED_TAB",
        document_id="DOC1",
        page_number=1,
        headers=["Year", "Revenue", "Margin"],
        data_rows=[["2023", "383285", "29.8%"]],  # numeric match on 383285 vs $383,285
    )

    report = TableEvaluator.evaluate(pred, gt)
    assert report.grid_valid is True
    assert report.structure_accuracy == 1.0
    assert report.cell_numeric_accuracy == 1.0
    # Exact match: 5 out of 6 match exact string ('Year', 'Revenue', 'Margin', '2023', '29.8%')
    assert round(report.cell_exact_match_ratio, 4) == round(5 / 6, 4)


def test_tab_004_teds_score_identical_and_perturbed():
    """TAB-004: Verify TEDS score is 1.0 for identical tables and decreases with errors."""
    gt = TableExtractor.from_grid_data(
        table_id="T_A",
        document_id="D1",
        page_number=1,
        headers=["Col A", "Col B"],
        data_rows=[["Val 1", "Val 2"], ["Val 3", "Val 4"]],
    )
    # Identical
    report_identical = TableEvaluator.evaluate(gt, gt)
    assert report_identical.teds_score == 1.0

    # Perturbed prediction
    pred_perturbed = TableExtractor.from_grid_data(
        table_id="T_B",
        document_id="D1",
        page_number=1,
        headers=["Col A", "Different Header"],
        data_rows=[["Val 1", "Val 2"], ["Changed Val", "Val 4"]],
    )
    report_perturbed = TableEvaluator.evaluate(pred_perturbed, gt)
    assert 0.0 < report_perturbed.teds_score < 1.0


def test_tab_005_ground_truth_sample_evaluation():
    """TAB-005: Evaluate PubTabNet sample table from ground truth fixture."""
    gt_file = REPO_ROOT / "audit" / "corpus" / "ground-truth" / "table_ground_truth_sample.json"
    if not gt_file.exists():
        pytest.skip("Sample ground truth missing")

    with open(gt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sample = data["sample_tables"][0]
    gt_table = TableExtractor.from_grid_data(
        table_id=sample["table_id"],
        document_id="PUB-056",
        page_number=1,
        headers=sample["headers"],
        data_rows=sample["data"],
    )

    report = TableEvaluator.evaluate(gt_table, gt_table)
    assert report.teds_score == 1.0
    assert report.cell_exact_match_ratio == 1.0
    assert report.cell_numeric_accuracy == 1.0
    assert report.total_gt_cells == 12


def test_tab_006_extractor_from_grid_data():
    """TAB-006: Verify TableExtractor properly assigns row/col indices and cell roles."""
    tab = TableExtractor.from_grid_data(
        table_id="TAB_GEN",
        document_id="D_GEN",
        page_number=1,
        headers=["H1", "H2"],
        data_rows=[["A", "B"]],
    )
    assert tab.row_count == 2
    assert tab.column_count == 2
    assert len(tab.cells) == 4
    assert tab.cells[0].role == "column_header"
    assert tab.cells[2].role == "data"


def test_tab_007_schema_conformance(table_schema):
    """TAB-007: Validate TableReconstruction against table.schema.json."""
    tab = TableExtractor.from_grid_data(
        table_id="TABLE-SCHEMA-TEST",
        document_id="DOC-99",
        page_number=2,
        headers=["Metric", "Value"],
        data_rows=[["Accuracy", "99.4%"]],
    )
    jsonschema.validate(tab.to_schema_dict(), table_schema)
