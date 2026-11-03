"""
tests/processing/reading_order/test_reading_order.py
===================================================
Tests ORD-001 through ORD-007 verifying reading order graph, topological sorting,
multi-column resolution, Kendall's tau evaluation, and schema conformance.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.processing.models import CoordinateSystem, LayoutRegion, ReadingOrderResult, RegionType
from aegis.processing.reading_order import (
    ReadingOrderEvaluator,
    ReadingOrderGraph,
    ReadingOrderResolver,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ORDERING_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "reading_order.schema.json"


@pytest.fixture
def ordering_schema():
    with open(ORDERING_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_ord_001_graph_topological_sort():
    """ORD-001: Verify directed graph precedence sorting and cycle handling."""
    graph = ReadingOrderGraph()
    graph.add_precedence("R1", "R2")
    graph.add_precedence("R2", "R3")
    graph.add_precedence("R3", "R4")

    assert graph.has_cycle() is False
    sorted_nodes = graph.topological_sort()
    assert sorted_nodes == ["R1", "R2", "R3", "R4"]

    # Test cycle detection
    cycle_graph = ReadingOrderGraph()
    cycle_graph.add_precedence("A", "B")
    cycle_graph.add_precedence("B", "C")
    cycle_graph.add_precedence("C", "A")
    assert cycle_graph.has_cycle() is True


def test_ord_002_kendall_tau_identical():
    """ORD-002: Verify identical sequence produces Kendall tau = 1.0 and pairwise accuracy = 1.0."""
    gt = ["R1", "R2", "R3", "R4", "R5"]
    pred = ["R1", "R2", "R3", "R4", "R5"]

    report = ReadingOrderEvaluator.evaluate(pred, gt)
    assert report.kendall_tau == 1.0
    assert report.pairwise_accuracy == 1.0
    assert report.sequence_similarity == 1.0
    assert report.column_interleaving_detected is False


def test_ord_003_kendall_tau_inverted():
    """ORD-003: Verify inverted sequence produces Kendall tau = -1.0 and pairwise accuracy = 0.0."""
    gt = ["R1", "R2", "R3", "R4"]
    pred = ["R4", "R3", "R2", "R1"]

    report = ReadingOrderEvaluator.evaluate(pred, gt)
    assert report.kendall_tau == -1.0
    assert report.pairwise_accuracy == 0.0
    assert report.column_interleaving_detected is True


def test_ord_004_two_column_resolver():
    """ORD-004: Verify resolver correctly orders left column before right column, avoiding interleaving."""
    coord_sys = CoordinateSystem(units="normalized", origin="top_left", page_width=100.0, page_height=100.0)

    # Left column: x in [0.05..0.45], y at 0.2 and 0.5
    # Right column: x in [0.55..0.95], y at 0.2 and 0.5
    regions = [
        LayoutRegion(region_id="COL2_P1", document_id="D1", page_number=1, region_type=RegionType.PARAGRAPH, bbox=[0.55, 0.2, 0.95, 0.4], coordinate_system=coord_sys),
        LayoutRegion(region_id="COL1_P1", document_id="D1", page_number=1, region_type=RegionType.PARAGRAPH, bbox=[0.05, 0.2, 0.45, 0.4], coordinate_system=coord_sys),
        LayoutRegion(region_id="COL2_P2", document_id="D1", page_number=1, region_type=RegionType.PARAGRAPH, bbox=[0.55, 0.5, 0.95, 0.7], coordinate_system=coord_sys),
        LayoutRegion(region_id="COL1_P2", document_id="D1", page_number=1, region_type=RegionType.PARAGRAPH, bbox=[0.05, 0.5, 0.45, 0.7], coordinate_system=coord_sys),
    ]

    resolver = ReadingOrderResolver(column_gap_threshold=0.10)
    result = resolver.resolve(regions, document_id="D1", page_number=1)

    expected = ["COL1_P1", "COL1_P2", "COL2_P1", "COL2_P2"]
    assert result.reading_order == expected


def test_ord_005_caption_relationship_association():
    """ORD-005: Verify resolver links adjacent figure and caption regions."""
    coord_sys = CoordinateSystem(units="normalized", origin="top_left", page_width=100.0, page_height=100.0)
    regions = [
        LayoutRegion(region_id="FIG_1", document_id="D1", page_number=1, region_type=RegionType.FIGURE, bbox=[0.1, 0.2, 0.9, 0.6], coordinate_system=coord_sys),
        LayoutRegion(region_id="CAP_1", document_id="D1", page_number=1, region_type=RegionType.CAPTION, bbox=[0.1, 0.62, 0.9, 0.68], coordinate_system=coord_sys),
    ]
    resolver = ReadingOrderResolver()
    result = resolver.resolve(regions, document_id="D1", page_number=1)

    assert len(result.relationships) == 1
    rel = result.relationships[0]
    assert rel.source_id == "FIG_1"
    assert rel.target_id == "CAP_1"
    assert rel.relation_type == "figure_to_caption"


def test_ord_006_ground_truth_sample_reading_order():
    """ORD-006: Verify reading order evaluation on sample DocLayNet page."""
    gt_file = REPO_ROOT / "audit" / "corpus" / "ground-truth" / "layout_ground_truth_sample.json"
    if not gt_file.exists():
        pytest.skip("Sample ground truth missing")

    with open(gt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sample = data["sample_pages"][0]
    gt_order = [f"R_{nid}" for nid in sample["reading_order"]]
    pred_order = list(gt_order)

    report = ReadingOrderEvaluator.evaluate(pred_order, gt_order, document_id=sample["page_id"])
    assert report.kendall_tau == 1.0
    assert report.pairwise_accuracy == 1.0


def test_ord_007_schema_conformance(ordering_schema):
    """ORD-007: Validate ReadingOrderResult against reading_order.schema.json."""
    res = ReadingOrderResult(
        document_id="DOC-ORDER-101",
        page_number=1,
        reading_order=["R-001", "R-002", "R-003"],
        ordering_method="layout_graph",
        confidence=0.95,
    )
    jsonschema.validate(res.to_schema_dict(), ordering_schema)
