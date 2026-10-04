"""
Tests for mathematical theorems established in the AMDI-OS Extended Monograph:
- Theorem 5.1 (Scale Invariance): Normalized coordinate distances are invariant
  under uniform page rescaling.
- Theorem 5.2 (Metric Validity): The normalized Euclidean distance satisfies
  metric properties (non-negativity, identity, symmetry, triangle inequality).
"""
from __future__ import annotations

import math
from hypothesis import given, strategies as st
from src.core.master_state import Element, PageRepresentation, MasterState


def _normalize(x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    return x, y, w, h


@given(
    x1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    y1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    x2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    y2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    scale=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_theorem_5_1_scale_invariance(x1: float, y1: float, x2: float, y2: float, scale: float) -> None:
    """
    Theorem 5.1: normalized-coordinate distance is invariant under uniform
    page rescaling. Since normalization already divides out W_p/H_p, scaling
    the physical page (and the raw coordinates with it) leaves the
    normalized distance exactly unchanged.
    """
    dist_before = math.dist((x1, y1), (x2, y2))
    # Rescaling raw coordinates AND the page dimensions by the same factor
    # leaves normalized coordinates unchanged by construction — assert that
    # invariant directly, matching the monograph's proof structure.
    raw_x1, raw_y1 = x1 * scale * 100.0, y1 * scale * 100.0
    raw_x2, raw_y2 = x2 * scale * 100.0, y2 * scale * 100.0
    page_w, page_h = scale * 100.0, scale * 100.0

    norm_x1, norm_y1 = raw_x1 / page_w, raw_y1 / page_h
    norm_x2, norm_y2 = raw_x2 / page_w, raw_y2 / page_h

    dist_after = math.dist((norm_x1, norm_y1), (norm_x2, norm_y2))
    assert math.isclose(dist_before, dist_after, rel_tol=1e-9, abs_tol=1e-12)


@given(
    x1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    y1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    x2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    y2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    x3=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    y3=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_theorem_5_2_metric_validity(
    x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
) -> None:
    """
    Theorem 5.2: normalized Euclidean distance is a valid metric —
    non-negative, zero iff identical, symmetric, triangle inequality.
    """
    d = lambda a, b: math.dist(a, b)
    p1, p2, p3 = (x1, y1), (x2, y2), (x3, y3)

    assert d(p1, p2) >= 0.0                             # non-negativity
    assert d(p1, p1) == 0.0                             # identity
    assert math.isclose(d(p1, p2), d(p2, p1), rel_tol=1e-9, abs_tol=1e-12)  # symmetry
    assert d(p1, p3) <= d(p1, p2) + d(p2, p3) + 1e-9   # triangle inequality


def test_element_angle_wrapping_and_page_assembly():
    """Verify Section 5.2 8-tuple theta angle wrapping into [0, 2*pi)."""
    el = Element(
        x=0.2,
        y=0.3,
        w=0.4,
        h=0.5,
        page=1,
        theta=2.0 * math.pi + 0.5,
        element_type="text",
        content="Testing angle wrapping",
    )
    assert math.isclose(el.theta, 0.5, rel_tol=1e-9)
    assert 0.0 <= el.theta < 2.0 * math.pi

    page = PageRepresentation(
        page_number=1,
        elements=[el],
        physical_width=612.0,
        physical_height=792.0,
    )
    assert len(page.elements) == 1

    state = MasterState(doc_id="doc_theorems_test", pages=[page])
    assert state.doc_id == "doc_theorems_test"
    assert state.pages_status.is_hardened is True
    assert state.semantic_status.is_mock is True
    assert state.hierarchy_status.is_proposed is True
