"""Tests for the geometry engine."""
import math
import pytest
import numpy as np
from pathlib import Path
import sys

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.engines.geometry.element import GeometricElement, ElementType, BoundingBox
from src.engines.geometry.geometry_engine import GeometryEngine, SpatialStats


# ============================================================
# HELPERS
# ============================================================

def make_element(
    content: str = "test",
    page: int = 1,
    etype: ElementType = ElementType.TEXT,
    x0: float = 0.1, y0: float = 0.1,
    x1: float = 0.5, y1: float = 0.3,
    section: str = None,
) -> GeometricElement:
    """Factory for creating test elements."""
    return GeometricElement(
        content=content,
        page=page,
        type=etype,
        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
        section=section,
    )


# ============================================================
# INITIALIZATION
# ============================================================

def test_engine_init():
    engine = GeometryEngine()
    assert len(engine.elements) == 0
    assert engine.statistics().n_elements == 0


# ============================================================
# 1. COORDINATE EXTRACTION
# ============================================================

def test_extract_geometry_text_block():
    engine = GeometryEngine()
    page_dict = {
        "blocks": [
            {
                "type": 0,
                "bbox": (100, 100, 500, 200),
                "lines": [
                    {
                        "spans": [
                            {"text": "Hello "},
                            {"text": "World"},
                        ]
                    }
                ],
            }
        ]
    }
    elements = engine.extract_geometry(page_dict, page_number=1, page_width=612, page_height=792)
    assert len(elements) == 1
    assert elements[0].content == "Hello World"
    assert elements[0].bbox.x0 == 100
    assert elements[0].bbox.y0 == 100


def test_extract_geometry_multiple_blocks():
    engine = GeometryEngine()
    page_dict = {
        "blocks": [
            {"type": 0, "bbox": (100, 100, 500, 200),
             "lines": [{"spans": [{"text": "First"}]}]},
            {"type": 0, "bbox": (100, 300, 500, 400),
             "lines": [{"spans": [{"text": "Second"}]}]},
            {"type": 1, "bbox": (100, 500, 300, 700)},  # Image
        ]
    }
    elements = engine.extract_geometry(page_dict, page_number=1, page_width=612, page_height=792)
    assert len(elements) == 3
    assert elements[0].content == "First"
    assert elements[1].content == "Second"
    assert elements[2].type == ElementType.FIGURE


def test_extract_geometry_empty_block():
    engine = GeometryEngine()
    page_dict = {
        "blocks": [{"type": 0, "bbox": (100, 100, 500, 200), "lines": []}]
    }
    elements = engine.extract_geometry(page_dict, 1, 612, 792)
    assert len(elements) == 0


def test_extract_geometry_classifies_header():
    engine = GeometryEngine()
    # Block at very top of page (y0 < 5% of 792 = 39.6)
    page_dict = {
        "blocks": [
            {"type": 0, "bbox": (100, 10, 500, 30),
             "lines": [{"spans": [{"text": "Header"}]}]},
        ]
    }
    elements = engine.extract_geometry(page_dict, 1, 612, 792)
    assert elements[0].type == ElementType.HEADER


def test_extract_geometry_classifies_footer():
    engine = GeometryEngine()
    # Block at very bottom (y1 > 95% of 792 = 752.4)
    page_dict = {
        "blocks": [
            {"type": 0, "bbox": (100, 760, 500, 780),
             "lines": [{"spans": [{"text": "Footer"}]}]},
        ]
    }
    elements = engine.extract_geometry(page_dict, 1, 612, 792)
    assert elements[0].type == ElementType.FOOTER


def test_extract_geometry_classifies_title():
    engine = GeometryEngine()
    page_dict = {
        "blocks": [
            {"type": 0, "bbox": (100, 100, 500, 200),
             "lines": [{"spans": [{"text": "EXECUTIVE SUMMARY"}]}]},
        ]
    }
    elements = engine.extract_geometry(page_dict, 1, 612, 792)
    assert elements[0].type == ElementType.TITLE


def test_extract_geometry_classifies_heading():
    engine = GeometryEngine()
    page_dict = {
        "blocks": [
            {"type": 0, "bbox": (100, 100, 500, 130),
             "lines": [{"spans": [{"text": "Section Title"}]}]},
        ]
    }
    elements = engine.extract_geometry(page_dict, 1, 612, 792)
    assert elements[0].type == ElementType.HEADING


# ============================================================
# 2. COORDINATE NORMALIZATION
# ============================================================

def test_normalize_coordinates_basic():
    engine = GeometryEngine()
    e = make_element(x0=100, y0=100, x1=500, y1=200)
    engine.add(e)
    engine.normalize_coordinates(page=1, page_width=612, page_height=792)
    assert e.bbox.x0 == pytest.approx(100 / 612)
    assert e.bbox.y0 == pytest.approx(100 / 792)
    assert e.bbox.x1 == pytest.approx(500 / 612)
    assert e.bbox.y1 == pytest.approx(200 / 792)


def test_normalize_coordinates_zero_dimensions():
    engine = GeometryEngine()
    e = make_element()
    engine.add(e)
    # Should not crash with zero dimensions
    engine.normalize_coordinates(page=1, page_width=0, page_height=0)
    # Original bbox unchanged
    assert e.bbox.x0 == 0.1


def test_normalize_coordinates_all_elements_on_page():
    engine = GeometryEngine()
    e1 = make_element(content="A", x0=100, y0=100, x1=200, y1=150)
    e2 = make_element(content="B", x0=300, y0=200, x1=500, y1=300)
    e3 = make_element(content="C", x0=50, y0=400, x1=150, y1=450)
    engine.add_many([e1, e2, e3])
    engine.normalize_coordinates(page=1, page_width=1000, page_height=1000)
    # All should be normalized
    for e in [e1, e2, e3]:
        assert 0 <= e.bbox.x0 <= 1
        assert 0 <= e.bbox.y0 <= 1
        assert 0 <= e.bbox.x1 <= 1
        assert 0 <= e.bbox.y1 <= 1


def test_normalize_coordinates_scale_invariance():
    """Test Theorem 4.1: scale invariance of normalized distance."""
    engine = GeometryEngine()
    # Page 1: 1000x1000
    e1_p1 = make_element(content="A", page=1, x0=100, y0=100, x1=200, y1=200)
    e2_p1 = make_element(content="B", page=1, x0=800, y0=800, x1=900, y1=900)
    engine.add_many([e1_p1, e2_p1])
    engine.normalize_coordinates(page=1, page_width=1000, page_height=1000)
    d1 = engine.calculate_distance(e1_p1, e2_p1)
    # Reset and try different scale
    engine2 = GeometryEngine()
    e1_p1_2 = make_element(content="A", page=1, x0=10, y0=10, x1=20, y1=20)
    e2_p1_2 = make_element(content="B", page=1, x0=80, y0=80, x1=90, y1=90)
    engine2.add_many([e1_p1_2, e2_p1_2])
    engine2.normalize_coordinates(page=1, page_width=100, page_height=100)
    d2 = engine2.calculate_distance(e1_p1_2, e2_p1_2)
    # Same normalized distance
    assert abs(d1 - d2) < 0.01


def test_denormalize_bbox():
    engine = GeometryEngine()
    e = make_element()
    engine.add(e)
    engine.normalize_coordinates(page=1, page_width=612, page_height=792)
    raw = engine.denormalize_bbox(e.bbox, page=1)
    assert raw.x0 == pytest.approx(0.1, abs=0.01)
    assert raw.y0 == pytest.approx(0.1, abs=0.01)


# ============================================================
# 3. BOUNDING BOXES (IoU, area, etc.)
# ============================================================

def test_iou_no_overlap():
    engine = GeometryEngine()
    a = BoundingBox(0, 0, 0.5, 0.5)
    b = BoundingBox(0.6, 0.6, 1.0, 1.0)
    assert engine.iou(a, b) == 0.0


def test_iou_partial_overlap():
    engine = GeometryEngine()
    a = BoundingBox(0, 0, 0.5, 0.5)
    b = BoundingBox(0.25, 0.25, 0.75, 0.75)
    iou = engine.iou(a, b)
    # Intersection: 0.25 * 0.25 = 0.0625
    # Union: 0.25 + 0.25 - 0.0625 = 0.4375
    assert iou == pytest.approx(0.0625 / 0.4375, abs=1e-6)


def test_iou_complete_overlap():
    engine = GeometryEngine()
    a = BoundingBox(0, 0, 0.5, 0.5)
    b = BoundingBox(0, 0, 0.5, 0.5)
    assert engine.iou(a, b) == pytest.approx(1.0)


def test_iou_contained():
    engine = GeometryEngine()
    outer = BoundingBox(0, 0, 1, 1)
    inner = BoundingBox(0.25, 0.25, 0.75, 0.75)
    iou = engine.iou(inner, outer)
    assert iou == pytest.approx(0.25, abs=1e-6)


def test_iou_zero_area():
    engine = GeometryEngine()
    a = BoundingBox(0, 0, 0, 0)
    b = BoundingBox(0, 0, 1, 1)
    assert engine.iou(a, b) == 0.0


def test_contains():
    engine = GeometryEngine()
    outer = BoundingBox(0, 0, 1, 1)
    inner = BoundingBox(0.25, 0.25, 0.75, 0.75)
    assert engine.contains(outer, inner)
    assert not engine.contains(inner, outer)


def test_bbox_area():
    engine = GeometryEngine()
    bbox = BoundingBox(0.1, 0.2, 0.5, 0.6)
    assert engine.bbox_area(bbox) == pytest.approx(0.16, abs=1e-6)


def test_bbox_center():
    engine = GeometryEngine()
    bbox = BoundingBox(0, 0, 0.6, 0.4)
    cx, cy = engine.bbox_center(bbox)
    assert cx == pytest.approx(0.3)
    assert cy == pytest.approx(0.2)


# ============================================================
# 4. ALIGNMENT DETECTION
# ============================================================

def test_alignment_perfect():
    engine = GeometryEngine()
    e1 = make_element(x0=0.0, y0=0.0, x1=0.5, y1=0.5)
    e2 = make_element(x0=0.0, y0=0.0, x1=0.5, y1=0.5)
    assert engine.calculate_alignment(e1, e2) == pytest.approx(1.0)


def test_alignment_partial():
    engine = GeometryEngine()
    e1 = make_element(x0=0.0, y0=0.0, x1=0.5, y1=0.5)
    e2 = make_element(x0=0.0, y0=0.5, x1=0.5, y1=1.0)  # Directly below
    alignment = engine.calculate_alignment(e1, e2)
    assert 0 < alignment <= 1.0


def test_alignment_far_apart():
    engine = GeometryEngine()
    e1 = make_element(x0=0.0, y0=0.0, x1=0.1, y1=0.1)
    e2 = make_element(x0=0.9, y0=0.9, x1=1.0, y1=1.0)
    alignment = engine.calculate_alignment(e1, e2)
    assert alignment < 0.5


def test_alignment_no_bbox():
    engine = GeometryEngine()
    e1 = make_element()
    e2 = make_element()
    e1.bbox = None
    assert engine.calculate_alignment(e1, e2) == 0.0


def test_alignment_batch():
    engine = GeometryEngine()
    elements = [
        make_element(content=f"E{i}", x0=i*0.2, y0=0, x1=i*0.2+0.1, y1=0.5)
        for i in range(5)
    ]
    matrix = engine.calculate_alignment_batch(elements)
    assert matrix.shape == (5, 5)
    assert matrix[0, 0] == 0  # self
    assert matrix[2, 2] == 0  # self


# ============================================================
# 5. DISTANCE CALCULATION
# ============================================================

def test_distance_same_page():
    engine = GeometryEngine()
    e1 = make_element(x0=0.0, y0=0.0, x1=0.2, y1=0.2)
    e2 = make_element(x0=0.6, y0=0.6, x1=0.8, y1=0.8)
    d = engine.calculate_distance(e1, e2)
    # Centers: (0.1, 0.1) and (0.7, 0.7)
    # Distance: sqrt(0.36 + 0.36) = sqrt(0.72) ≈ 0.849
    assert d == pytest.approx(math.sqrt(0.72), abs=1e-3)


def test_distance_different_pages():
    engine = GeometryEngine()
    e1 = make_element(page=1, x0=0.0, y0=0.0, x1=0.2, y1=0.2)
    e2 = make_element(page=2, x0=0.0, y0=0.0, x1=0.2, y1=0.2)
    d = engine.calculate_distance(e1, e2)
    # Spatial: 0, Page: 1.5
    assert d == pytest.approx(1.5, abs=0.01)


def test_distance_custom_page_weight():
    engine = GeometryEngine()
    e1 = make_element(page=1)
    e2 = make_element(page=3)
    d = engine.calculate_distance(e1, e2, cross_page_weight=2.0)
    # 2 pages * 2.0 = 4.0
    assert d == pytest.approx(4.0, abs=0.01)


def test_distance_no_bbox():
    engine = GeometryEngine()
    e1 = make_element()
    e2 = make_element()
    e1.bbox = None
    assert engine.calculate_distance(e1, e2) == float("inf")


def test_distance_matrix():
    engine = GeometryEngine()
    elements = [make_element(content=f"E{i}") for i in range(3)]
    D = engine.distance_matrix(elements)
    assert D.shape == (3, 3)
    assert np.allclose(D, D.T)  # Symmetric
    assert np.allclose(np.diag(D), 0)  # Zero diagonal


def test_find_nearest():
    engine = GeometryEngine()
    e1 = make_element(content="target", x0=0.5, y0=0.5, x1=0.6, y1=0.6)
    e2 = make_element(content="near", x0=0.55, y0=0.55, x1=0.6, y1=0.6)
    e3 = make_element(content="far", x0=0.0, y0=0.0, x1=0.1, y1=0.1)
    engine.add_many([e1, e2, e3])
    nearest = engine.find_nearest(e1, k=2)
    assert len(nearest) == 2
    # Closest should be e2
    assert nearest[0][0].content == "near"


def test_find_nearest_same_page_only():
    engine = GeometryEngine()
    e1 = make_element(page=1)
    e2 = make_element(page=1, x0=0.1, y0=0.1, x1=0.2, y1=0.2)
    e3 = make_element(page=2, x0=0.0, y0=0.0, x1=0.1, y1=0.1)  # Different page
    engine.add_many([e1, e2, e3])
    nearest = engine.find_nearest(e1, k=5, same_page_only=True)
    # Should only include e2
    assert len(nearest) == 1
    assert nearest[0][0].page == 1


# ============================================================
# 6. READING ORDER
# ============================================================

def test_reading_order_basic():
    engine = GeometryEngine()
    e1 = make_element(content="Bottom", x0=0.0, y0=0.8, x1=0.5, y1=1.0)
    e2 = make_element(content="Top", x0=0.0, y0=0.0, x1=0.5, y1=0.2)
    e3 = make_element(content="Middle", x0=0.0, y0=0.4, x1=0.5, y1=0.6)
    order = engine.get_reading_order([e1, e2, e3])
    assert order[0].content == "Top"
    assert order[1].content == "Middle"
    assert order[2].content == "Bottom"


def test_reading_order_left_to_right():
    engine = GeometryEngine()
    e1 = make_element(content="Right", x0=0.5, y0=0.0, x1=0.7, y1=0.2)
    e2 = make_element(content="Left", x0=0.0, y0=0.0, x1=0.2, y1=0.2)
    order = engine.get_reading_order([e1, e2])
    assert order[0].content == "Left"
    assert order[1].content == "Right"


def test_reading_order_multi_page():
    engine = GeometryEngine()
    e1 = make_element(content="Page1", page=1, x0=0.0, y0=0.0, x1=0.5, y1=0.2)
    e2 = make_element(content="Page2", page=2, x0=0.0, y0=0.8, x1=0.5, y1=1.0)
    e3 = make_element(content="Page1bot", page=1, x0=0.0, y0=0.8, x1=0.5, y1=1.0)
    order = engine.get_reading_order([e2, e1, e3])
    # Page 1 elements first, then Page 2
    assert order[0].content == "Page1"
    assert order[1].content == "Page1bot"
    assert order[2].content == "Page2"


def test_reading_order_indices():
    engine = GeometryEngine()
    elements = [
        make_element(content="A", x0=0, y0=0.5),
        make_element(content="B", x0=0, y0=0.0),
        make_element(content="C", x0=0, y0=0.8),
    ]
    indices = engine.get_reading_order_indices(elements)
    # Order should be: B (idx 1), A (idx 0), C (idx 2)
    assert indices == [1, 0, 2]


# ============================================================
# BONUS: AREA IMPORTANCE
# ============================================================

def test_area_importance():
    engine = GeometryEngine()
    big = make_element(x0=0, y0=0, x1=0.8, y1=0.8)  # 0.64
    small = make_element(x0=0, y0=0, x1=0.2, y1=0.2)  # 0.04
    assert engine.area_importance(big) == pytest.approx(0.64)
    assert engine.area_importance(small) == pytest.approx(0.04)


def test_area_importance_weighted():
    engine = GeometryEngine()
    elements = [
        make_element(x0=0, y0=0, x1=0.5, y1=0.5),  # 0.25
        make_element(x0=0, y0=0, x1=0.5, y1=0.5),  # 0.25
    ]
    weights = engine.area_importance_weighted(elements)
    assert weights.sum() == pytest.approx(1.0)
    assert all(w == 0.5 for w in weights)


# ============================================================
# BONUS: SPATIAL NEIGHBORS
# ============================================================

def test_elements_above():
    engine = GeometryEngine()
    target = make_element(content="target", x0=0, y0=0.5, x1=0.5, y1=0.6)
    above1 = make_element(content="near-above", x0=0.1, y0=0.3, x1=0.4, y1=0.4)
    above2 = make_element(content="far-above", x0=0.1, y0=0.0, x1=0.4, y1=0.1)
    below = make_element(content="below", x0=0.1, y0=0.7, x1=0.4, y1=0.8)
    engine.add_many([target, above1, above2, below])
    above = engine.elements_above(target, k=5)
    assert len(above) == 2
    assert all("above" in e.content for e in above)


def test_elements_below():
    engine = GeometryEngine()
    target = make_element(content="target", x0=0, y0=0.0, x1=0.5, y1=0.2)
    below1 = make_element(content="near-below", x0=0.1, y0=0.3, x1=0.4, y1=0.4)
    below2 = make_element(content="far-below", x0=0.1, y0=0.7, x1=0.4, y1=0.8)
    engine.add_many([target, below1, below2])
    below = engine.elements_below(target, k=5)
    assert len(below) == 2
    # Should be sorted by distance
    assert below[0].content == "near-below"


def test_elements_left_right():
    engine = GeometryEngine()
    target = make_element(content="target", x0=0.4, y0=0.4, x1=0.6, y1=0.6)
    left = make_element(content="left", x0=0.0, y0=0.4, x1=0.2, y1=0.6)
    right = make_element(content="right", x0=0.8, y0=0.4, x1=1.0, y1=0.6)
    engine.add_many([target, left, right])
    L, R = engine.elements_left_right(target)
    assert len(L) == 1 and L[0].content == "left"
    assert len(R) == 1 and R[0].content == "right"


# ============================================================
# BONUS: SPATIAL DENSITY FIELD
# ============================================================

def test_spatial_density_field_basic():
    engine = GeometryEngine()
    elements = [
        make_element(x0=0, y0=0, x1=0.5, y1=0.5),
        make_element(x0=0, y0=0, x1=0.3, y1=0.3),
    ]
    field = engine.spatial_density_field(elements, grid_size=16)
    assert field.shape == (16, 16)
    # Field should be normalized
    assert field.max() <= 1.0


def test_spatial_density_field_empty():
    engine = GeometryEngine()
    field = engine.spatial_density_field([], grid_size=10)
    assert field.shape == (10, 10)
    assert field.max() == 0.0


# ============================================================
# INDEXING
# ============================================================

def test_add_and_get():
    engine = GeometryEngine()
    e = make_element(content="test")
    engine.add(e)
    retrieved = engine.get(e.element_id)
    assert retrieved is not None
    assert retrieved.content == "test"


def test_get_by_page():
    engine = GeometryEngine()
    e1 = make_element(content="A", page=1)
    e2 = make_element(content="B", page=1)
    e3 = make_element(content="C", page=2)
    engine.add_many([e1, e2, e3])
    page1 = engine.get_by_page(1)
    assert len(page1) == 2
    assert all(e.page == 1 for e in page1)


def test_get_by_type():
    engine = GeometryEngine()
    e1 = make_element(etype=ElementType.TABLE)
    e2 = make_element(etype=ElementType.TEXT)
    e3 = make_element(etype=ElementType.TABLE)
    engine.add_many([e1, e2, e3])
    tables = engine.get_by_type(ElementType.TABLE)
    assert len(tables) == 2


def test_get_by_section():
    engine = GeometryEngine()
    e1 = make_element(content="A", section="intro")
    e2 = make_element(content="B", section="intro")
    e3 = make_element(content="C", section="results")
    engine.add_many([e1, e2, e3])
    intro = engine.get_by_section("intro")
    assert len(intro) == 2


def test_statistics():
    engine = GeometryEngine()
    elements = [
        make_element(content="A", page=1, x0=0.1, y0=0.1, x1=0.5, y1=0.3),
        make_element(content="B", page=1, x0=0.5, y0=0.5, x1=0.9, y1=0.7),
        make_element(content="C", page=2, x0=0.1, y0=0.1, x1=0.5, y1=0.3),
    ]
    engine.add_many(elements)
    stats = engine.statistics()
    assert stats.n_elements == 3
    assert stats.n_pages == 2
    assert 0 < stats.mean_area <= 1.0


def test_clear():
    engine = GeometryEngine()
    engine.add(make_element())
    engine.clear()
    assert len(engine.elements) == 0


# ============================================================
# THEOREM VERIFICATION
# ============================================================

def test_theorem_4_1_scale_invariance():
    """Verify Theorem 4.1: Normalized distance is invariant to scaling."""
    engine = GeometryEngine()
    # Two pages, same content, different scales
    e1 = make_element(page=1, x0=100, y0=100, x1=200, y1=200)
    e2 = make_element(page=1, x0=800, y0=800, x1=900, y1=900)
    engine.add_many([e1, e2])
    engine.normalize_coordinates(page=1, page_width=1000, page_height=1000)
    d_1000 = engine.calculate_distance(e1, e2)
    # Same elements at 1/10 scale
    e3 = make_element(page=1, x0=10, y0=10, x1=20, y1=20)
    e4 = make_element(page=1, x0=80, y0=80, x1=90, y1=90)
    engine2 = GeometryEngine()
    engine2.add_many([e3, e4])
    engine2.normalize_coordinates(page=1, page_width=100, page_height=100)
    d_100 = engine2.calculate_distance(e3, e4)
    # Distances should be equal (within tolerance)
    assert abs(d_1000 - d_100) < 0.01


def test_theorem_5_1_triangle_inequality():
    """Verify Theorem 5.1: Triangle inequality for same-page elements."""
    engine = GeometryEngine()
    a = make_element(x0=0.0, y0=0.0, x1=0.1, y1=0.1)
    b = make_element(x0=0.5, y0=0.5, x1=0.6, y1=0.6)
    c = make_element(x0=1.0, y0=1.0, x1=1.0, y1=1.0)
    engine.add_many([a, b, c])
    d_ab = engine.calculate_distance(a, b)
    d_bc = engine.calculate_distance(b, c)
    d_ac = engine.calculate_distance(a, c)
    # Triangle inequality: d(a, c) <= d(a, b) + d(b, c)
    assert d_ac <= d_ab + d_bc + 0.01  # Small tolerance


def test_area_importance_bounds():
    """Area importance should be in [0, 1]."""
    engine = GeometryEngine()
    for _ in range(10):
        import random
        e = make_element(
            x0=random.random() * 0.5,
            y0=random.random() * 0.5,
            x1=random.random() * 0.5 + 0.5,
            y1=random.random() * 0.5 + 0.5,
        )
        engine.add(e)
        ar = engine.area_importance(e)
        assert 0 <= ar <= 1


def test_alignment_bounds():
    """Alignment should be in [0, 1]."""
    engine = GeometryEngine()
    import random
    for _ in range(20):
        e1 = make_element(
            x0=random.random(), y0=random.random(),
            x1=random.random(), y1=random.random(),
        )
        e2 = make_element(
            x0=random.random(), y0=random.random(),
            x1=random.random(), y1=random.random(),
        )
        a = engine.calculate_alignment(e1, e2)
        assert 0 <= a <= 1
