"""
tests/processing/layout/test_layout_accuracy.py
===============================================
Tests LAY-001 through LAY-007 verifying layout region taxonomy, IoU matching,
evaluator metrics (precision, recall, F1, mAP), visual overlays, and schema conformance.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.processing.layout import (
    LayoutDetector,
    LayoutEvaluator,
    LayoutVisualizer,
    compute_iou,
    normalize_region_type,
    to_normalized_coordinates,
)
from aegis.processing.models import CoordinateSystem, ExtractionBlock, LayoutRegion, PageTextExtraction, RegionType

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LAYOUT_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "layout.schema.json"


@pytest.fixture
def layout_schema():
    with open(LAYOUT_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_lay_001_iou_calculation():
    """LAY-001: Verify IoU calculation across identical, disjoint, and overlapping boxes."""
    box_a = [0.0, 0.0, 10.0, 10.0]  # area 100
    box_b = [0.0, 0.0, 10.0, 10.0]  # area 100
    assert compute_iou(box_a, box_b) == 1.0

    box_c = [20.0, 20.0, 30.0, 30.0]
    assert compute_iou(box_a, box_c) == 0.0

    # Half overlap: box_d [5, 0, 15, 10] -> intersection [5,0,10,10] = 50, union = 150 -> IoU 1/3
    box_d = [5.0, 0.0, 15.0, 10.0]
    assert round(compute_iou(box_a, box_d), 4) == round(50.0 / 150.0, 4)


def test_lay_002_taxonomy_normalization():
    """LAY-002: Verify mapping of DocLayNet/PubLayNet categories to canonical RegionType."""
    assert normalize_region_type("Page-header") == RegionType.HEADER
    assert normalize_region_type("Title") == RegionType.TITLE
    assert normalize_region_type("Section-header") == RegionType.SECTION_HEADER
    assert normalize_region_type("Text") == RegionType.PARAGRAPH
    assert normalize_region_type("Table") == RegionType.TABLE
    assert normalize_region_type("Picture") == RegionType.FIGURE


def test_lay_003_layout_evaluator_matching():
    """LAY-003: Test class-aware one-to-one matching and metric calculation."""
    coord_sys = CoordinateSystem(units="normalized", origin="top_left", page_width=100.0, page_height=100.0)

    gts = [
        LayoutRegion(region_id="GT-1", document_id="D1", page_number=1, region_type=RegionType.TITLE, bbox=[0.1, 0.1, 0.9, 0.2], coordinate_system=coord_sys),
        LayoutRegion(region_id="GT-2", document_id="D1", page_number=1, region_type=RegionType.PARAGRAPH, bbox=[0.1, 0.25, 0.9, 0.5], coordinate_system=coord_sys),
        LayoutRegion(region_id="GT-3", document_id="D1", page_number=1, region_type=RegionType.TABLE, bbox=[0.1, 0.55, 0.9, 0.85], coordinate_system=coord_sys),
    ]

    # Predictions: 1 exact match, 1 slight shift (high IoU), 1 false positive, 1 false negative (table missed)
    preds = [
        LayoutRegion(region_id="P-1", document_id="D1", page_number=1, region_type=RegionType.TITLE, bbox=[0.1, 0.1, 0.9, 0.2], coordinate_system=coord_sys),  # TP
        LayoutRegion(region_id="P-2", document_id="D1", page_number=1, region_type=RegionType.PARAGRAPH, bbox=[0.11, 0.26, 0.89, 0.49], coordinate_system=coord_sys),  # TP
        LayoutRegion(region_id="P-3", document_id="D1", page_number=1, region_type=RegionType.FIGURE, bbox=[0.1, 0.9, 0.5, 0.95], coordinate_system=coord_sys),  # FP
    ]

    evaluator = LayoutEvaluator(iou_threshold=0.50)
    report = evaluator.evaluate(preds, gts)

    assert len(report.matched_pairs) == 2
    assert report.class_metrics["title"].true_positives == 1
    assert report.class_metrics["paragraph"].true_positives == 1
    assert report.class_metrics["figure"].false_positives == 1
    assert report.class_metrics["table"].false_negatives == 1
    assert round(report.overall_precision, 4) == round(2 / 3, 4)
    assert round(report.overall_recall, 4) == round(2 / 3, 4)


def test_lay_004_detector_execution():
    """LAY-004: Detect header, title, and paragraph from extraction blocks."""
    blocks = [
        ExtractionBlock(block_id="B-1", text="Company Confidential Report", bbox=[50.0, 20.0, 500.0, 45.0]),  # Header
        ExtractionBlock(block_id="B-2", text="Annual Evaluation Summary 2026", bbox=[50.0, 80.0, 500.0, 115.0]),  # Title (height 35)
        ExtractionBlock(block_id="B-3", text="The portfolio experienced resilient expansion across all segments.", bbox=[50.0, 130.0, 500.0, 140.0]),  # Paragraph (height 10)
    ]
    page_extr = PageTextExtraction(
        document_id="DOC_LAYOUT_TEST",
        page_number=1,
        extraction_method="native_pdf",
        engine="test",
        engine_version="1.0",
        language=["en"],
        text="All text",
        blocks=blocks,
    )

    detector = LayoutDetector(header_breakpoint=0.08, footer_breakpoint=0.92, heading_height_thresholds=(20.0, 13.0))
    regions = detector.detect_regions(page_extr, page_width=612.0, page_height=792.0)

    assert len(regions) == 3
    assert regions[0].region_type == RegionType.HEADER
    assert regions[1].region_type == RegionType.TITLE
    assert regions[2].region_type == RegionType.PARAGRAPH


def test_lay_005_visual_overlay_export(tmp_path):
    """LAY-005: Generate and export visual SVG overlay for layout inspection."""
    coord_sys = CoordinateSystem(units="normalized", origin="top_left", page_width=612.0, page_height=792.0)
    gts = [LayoutRegion(region_id="GT-01", document_id="D1", page_number=1, region_type=RegionType.TITLE, bbox=[0.1, 0.1, 0.9, 0.2], coordinate_system=coord_sys)]
    preds = [LayoutRegion(region_id="PR-01", document_id="D1", page_number=1, region_type=RegionType.TITLE, bbox=[0.1, 0.1, 0.9, 0.2], coordinate_system=coord_sys)]

    evaluator = LayoutEvaluator(iou_threshold=0.50)
    report = evaluator.evaluate(preds, gts)

    svg_file = tmp_path / "overlay.svg"
    out = LayoutVisualizer.export_overlay(preds, gts, report, svg_file)
    assert out.exists()
    svg_text = out.read_text(encoding="utf-8")
    assert "<svg" in svg_text
    assert "gt-matched" in svg_text


def test_lay_006_ground_truth_sample_eval():
    """LAY-006: Evaluate DocLayNet ground truth sample file."""
    gt_file = REPO_ROOT / "audit" / "corpus" / "ground-truth" / "layout_ground_truth_sample.json"
    if not gt_file.exists():
        pytest.skip("Sample ground truth missing")

    with open(gt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sample = data["sample_pages"][0]
    coord_sys = CoordinateSystem(units="points", origin="top_left", page_width=sample["width"], page_height=sample["height"])

    gts = []
    for ann in sample["annotations"]:
        cat = normalize_region_type(ann["category"])
        # COCO bbox [x, y, w, h] to [x0, y0, x1, y1]
        x, y, w, h = ann["bbox"]
        gts.append(LayoutRegion(
            region_id=f"GT-{ann['id']}",
            document_id=sample["page_id"],
            page_number=1,
            region_type=cat,
            bbox=[x, y, x + w, y + h],
            coordinate_system=coord_sys,
        ))

    evaluator = LayoutEvaluator(iou_threshold=0.50)
    # Self-evaluation (perfect prediction)
    report = evaluator.evaluate(gts, gts)
    assert report.overall_f1 == 1.0
    assert report.mean_average_precision == 1.0


def test_lay_007_schema_conformance(layout_schema):
    """LAY-007: Validate LayoutRegion against layout.schema.json."""
    coord_sys = CoordinateSystem(units="normalized", origin="top_left", page_width=612.0, page_height=792.0)
    region = LayoutRegion(
        region_id="REGION-001",
        document_id="DOC-LAYOUT-100",
        page_number=1,
        region_type=RegionType.PARAGRAPH,
        bbox=[0.05, 0.10, 0.95, 0.35],
        coordinate_system=coord_sys,
        text_reference="BLOCK-001",
        confidence=0.92,
    )
    jsonschema.validate(region.to_schema_dict(), layout_schema)
