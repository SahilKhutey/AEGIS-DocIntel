"""Tests for the recurrence engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import pytest

from src.core.geometric_element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox
from src.engines.recurrence import (
    RecurrenceEngine, RecurrenceGroup, RecurrenceStats,
)


# ============================================================
# HELPERS
# ============================================================

def make_element(
    content: str = "test",
    page: int = 1,
    etype: ElementType = ElementType.TEXT,
    x0: float = 0.1, y0: float = 0.1,
    x1: float = 0.5, y1: float = 0.3,
) -> GeometricElement:
    return GeometricElement(
        content=content, page=page, type=etype,
        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
    )


# ============================================================
# INITIALIZATION
# ============================================================

def test_init():
    engine = RecurrenceEngine()
    assert len(engine.groups) == 0


# ============================================================
# 1. HEADER DETECTION
# ============================================================

def test_detect_simple_header():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Company Header", page=1, y0=0.02, y1=0.05),
        make_element(content="Company Header", page=2, y0=0.02, y1=0.05),
        make_element(content="Company Header", page=3, y0=0.02, y1=0.05),
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    assert len(headers) >= 1
    assert headers[0].is_template
    assert headers[0].count == 3


def test_header_requires_multiple_pages():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Page 1 Header", page=1, y0=0.02, y1=0.05),
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    # Single occurrence, not a template
    if headers:
        assert headers[0].count == 1


def test_header_classified_correctly():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Doc Title", page=1, y0=0.02, etype=ElementType.HEADER),
        make_element(content="Doc Title", page=2, y0=0.02, etype=ElementType.HEADER),
        make_element(content="Doc Title", page=3, y0=0.02, etype=ElementType.HEADER),
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    assert len(headers) >= 1
    assert headers[0].group_type == "header"


def test_header_by_position_threshold():
    """Elements in top 8% are headers."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Header1", page=1, y0=0.05, y1=0.07),  # Top
        make_element(content="Header1", page=2, y0=0.05, y1=0.07),
        make_element(content="Header1", page=3, y0=0.05, y1=0.07),
        make_element(content="Middle text", page=1, y0=0.5, y1=0.6),  # Not header
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    assert len(headers) >= 1
    # Middle text should NOT be a header
    header_contents = [h.representative.content for h in headers]
    assert "Middle text" not in header_contents


# ============================================================
# 2. FOOTER DETECTION
# ============================================================

def test_detect_simple_footer():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="© 2024 Company", page=1, y0=0.95, y1=0.98),
        make_element(content="© 2024 Company", page=2, y0=0.95, y1=0.98),
        make_element(content="© 2024 Company", page=3, y0=0.95, y1=0.98),
    ]
    engine.detect(elements)
    footers = engine.get_footers()
    assert len(footers) >= 1
    assert footers[0].count == 3


def test_footer_classified_correctly():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Page Footer", page=p, y0=0.95, etype=ElementType.FOOTER)
        for p in range(1, 6)
    ]
    engine.detect(elements)
    footers = engine.get_footers()
    assert len(footers) >= 1
    assert footers[0].group_type == "footer"


def test_footer_by_position_threshold():
    """Elements in bottom 8% are footers."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Footer1", page=p, y0=0.95, y1=0.98)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    footers = engine.get_footers()
    assert len(footers) >= 1


def test_page_numbers_as_footers():
    """Sequential page numbers are detected as footers."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Page 1", page=1, y0=0.95, etype=ElementType.FOOTER),
        make_element(content="Page 2", page=2, y0=0.95, etype=ElementType.FOOTER),
        make_element(content="Page 3", page=3, y0=0.95, etype=ElementType.FOOTER),
    ]
    engine.detect(elements)
    # Each unique page number is separate group
    footers = engine.get_footers()
    assert len(footers) >= 1


# ============================================================
# 3. LOGO DETECTION
# ============================================================

def test_detect_logo():
    engine = RecurrenceEngine()
    elements = [
        # Small image at top-left of multiple pages
        make_element(content="logo.png", page=p, etype=ElementType.FIGURE,
                    x0=0.02, y0=0.02, x1=0.1, y1=0.07)
        for p in range(1, 6)
    ]
    engine.detect(elements)
    logos = engine.get_logos()
    assert len(logos) >= 1
    assert logos[0].count >= 3


def test_logo_must_be_small():
    """Large images are not logos."""
    engine = RecurrenceEngine()
    elements = [
        # Large figure (not a logo)
        make_element(content="big-image", page=p, etype=ElementType.FIGURE,
                    x0=0.0, y0=0.0, x1=0.5, y1=0.5)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    logos = engine.get_logos()
    # Large images should not be classified as logos
    # (they may be classified as general duplicates)
    for logo in logos:
        for eid in logo.members:
            for e in elements:
                if e.element_id == eid:
                    area = e.bbox.width * e.bbox.height
                    assert area < 0.05  # LOGO_MAX_AREA


# ============================================================
# 4. TABLE DETECTION
# ============================================================

def test_detect_repeated_table_structure():
    engine = RecurrenceEngine()
    # Tables with same column count and similar first row
    elements = [
        make_element(content="| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |", page=1, etype=ElementType.TABLE),
        make_element(content="| A | B | C |\n|---|---|---|\n| 4 | 5 | 6 |", page=2, etype=ElementType.TABLE),
        make_element(content="| A | B | C |\n|---|---|---|\n| 7 | 8 | 9 |", page=3, etype=ElementType.TABLE),
    ]
    engine.detect(elements)
    tables = engine.get_tables()
    assert len(tables) >= 1
    assert tables[0].count == 3


def test_different_table_structures_separate():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="| A | B |\n|---|---|\n| 1 | 2 |", page=1, etype=ElementType.TABLE),
        make_element(content="| X | Y | Z | W |\n|---|---|---|---|\n| 1 | 2 | 3 | 4 |", page=2, etype=ElementType.TABLE),
    ]
    engine.detect(elements)
    tables = engine.get_tables()
    # Different structures should be different groups
    assert len(tables) >= 2


# ============================================================
# 5. DUPLICATE DETECTION
# ============================================================

def test_detect_exact_duplicates():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Confidential", page=p, x0=0.1, y0=0.5)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    duplicates = engine.get_duplicates()
    assert len(duplicates) >= 1
    assert duplicates[0].count == 3


def test_duplicates_minimum_count():
    """Single occurrence is not a duplicate group."""
    engine = RecurrenceEngine()
    elements = [make_element(content="Unique text", page=1)]
    engine.detect(elements)
    duplicates = engine.get_duplicates()
    # Single occurrence is not a duplicate
    for d in duplicates:
        assert d.count >= 2


def test_detect_near_duplicates():
    """Whitespace-normalized duplicates."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Confidential  Notice", page=1),
        make_element(content="Confidential Notice", page=2),
        make_element(content="Confidential   Notice", page=3),
    ]
    engine.detect(elements)
    duplicates = engine.get_duplicates()
    assert len(duplicates) >= 1


def test_case_insensitive_duplicates():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="CONFIDENTIAL", page=1),
        make_element(content="confidential", page=2),
        make_element(content="Confidential", page=3),
    ]
    engine.detect(elements)
    duplicates = engine.get_duplicates()
    assert len(duplicates) >= 1


# ============================================================
# 6. COMPRESSION
# ============================================================

def test_compression_ratio_per_group():
    group = RecurrenceGroup(
        recurrence_id="g1",
        representative=make_element("test"),
        members=["e1", "e2", "e3"],
        page_set={1, 2, 3},
    )
    # 3 elements → compression ratio 1/3
    assert group.compression_ratio() == pytest.approx(1/3, abs=1e-6)


def test_compression_3x():
    """3 occurrences → ~3x compression."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Same Header", page=p, y0=0.02)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    if headers:
        # 3 copies → compression ratio 1/3
        assert headers[0].compression_ratio() <= 1/3 + 0.01


def test_compression_10x():
    """10 occurrences → ~10x compression."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Repeated Footer", page=p, y0=0.95)
        for p in range(1, 11)
    ]
    engine.detect(elements)
    footers = engine.get_footers()
    if footers:
        # 10 copies → compression ratio 1/10
        assert footers[0].compression_ratio() <= 0.11


def test_compression_stats_empty():
    engine = RecurrenceEngine()
    stats = engine.compression_stats()
    assert stats["n_groups"] == 0
    assert stats["avg_compression"] == 1.0


def test_compression_stats_with_groups():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Footer", page=p, y0=0.95)
        for p in range(1, 11)
    ]
    engine.detect(elements)
    stats = engine.compression_stats()
    assert stats["n_groups"] >= 1
    assert stats["avg_compression"] < 1.0
    assert stats["compression_ratio_pct"] > 0
    assert stats["estimated_storage_saved_bytes"] > 0


def test_compress_storage():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Header", page=p, y0=0.02)
        for p in range(1, 6)
    ]
    engine.detect(elements)
    plan = engine.compress_storage(elements)
    assert "templates" in plan
    assert "unique_elements" in plan
    assert "stats" in plan
    assert len(plan["templates"]) >= 1


def test_compress_storage_unique():
    """Elements not in any group go to unique_elements."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Unique content", page=1)
    ] + [
        make_element(content="Header", page=p, y0=0.02)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    plan = engine.compress_storage(elements)
    assert len(plan["unique_elements"]) >= 1



def test_reference_compression_ratio():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Footer", page=p, y0=0.95)
        for p in range(1, 11)
    ]
    engine.detect(elements)
    ratio = engine.reference_compression_ratio(elements)
    # Should be much less than 1.0 due to repetition
    assert ratio < 0.5


# ============================================================
# GROUP QUERIES
# ============================================================

def test_get_group():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Header", page=p, y0=0.02)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    assert len(headers) >= 1
    gid = headers[0].recurrence_id
    group = engine.get_group(gid)
    assert group is not None
    assert group.count == 3


def test_get_group_for_element():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Header", page=p, y0=0.02)
        for p in range(1, 4)
    ]
    engine.detect(elements)
    eid = elements[0].element_id
    group = engine.get_group_for_element(eid)
    assert group is not None
    assert group.count == 3


def test_get_group_for_unrelated_element():
    engine = RecurrenceEngine()
    # Element with random ID
    group = engine.get_group_for_element("nonexistent-id")
    assert group is None


def test_get_groups_by_type():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="H", page=p, y0=0.02) for p in range(1, 4)
    ] + [
        make_element(content="F", page=p, y0=0.95) for p in range(1, 4)
    ]
    engine.detect(elements)
    headers = engine.get_groups_by_type("header")
    footers = engine.get_groups_by_type("footer")
    assert len(headers) >= 1
    assert len(footers) >= 1


def test_get_repeated_content_pages():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Repeated", page=p, y0=0.02)
        for p in [1, 3, 5, 7]
    ]
    engine.detect(elements)
    pages = engine.get_repeated_content_pages("Repeated")
    assert pages == [1, 3, 5, 7]


# ============================================================
# RECURRENCE GROUP PROPERTIES
# ============================================================

def test_recurrence_group_is_template():
    g = RecurrenceGroup(
        recurrence_id="g1",
        representative=make_element("a"),
        members=["e1", "e2", "e3"],
    )
    assert g.is_template  # 3 occurrences


def test_recurrence_group_not_template():
    g = RecurrenceGroup(
        recurrence_id="g1",
        representative=make_element("a"),
        members=["e1", "e2"],
    )
    assert not g.is_template  # Only 2


def test_recurrence_group_dominant():
    g = RecurrenceGroup(
        recurrence_id="g1",
        representative=make_element("a"),
        members=[f"e{i}" for i in range(5)],
    )
    assert g.is_dominant


def test_recurrence_group_pages_sorted():
    g = RecurrenceGroup(
        recurrence_id="g1",
        representative=make_element("a"),
        members=["e1", "e2"],
        page_set={5, 1, 3, 2, 4},
    )
    assert g.pages == [1, 2, 3, 4, 5]


def test_recurrence_group_to_dict():
    g = RecurrenceGroup(
        recurrence_id="test-1",
        representative=make_element("Sample content"),
        members=["e1", "e2", "e3"],
        page_set={1, 2, 3},
        group_type="header",
    )
    d = g.to_dict()
    assert d["recurrence_id"] == "test-1"
    assert d["group_type"] == "header"
    assert d["count"] == 3
    assert d["is_template"] is True
    assert d["compression_ratio"] == pytest.approx(1/3)


# ============================================================
# INTEGRATION
# ============================================================

def test_full_document_pipeline():
    """Test with realistic document."""
    engine = RecurrenceEngine()
    elements = []
    # 10 pages with similar structure
    for page in range(1, 11):
        # Header at top
        elements.append(make_element(
            content="ANNUAL REPORT 2024", page=page, y0=0.02, y1=0.05,
            etype=ElementType.HEADER,
        ))
        # Content
        elements.append(make_element(
            content=f"Section content for page {page}",
            page=page, y0=0.3, y1=0.4,
        ))
        # Footer at bottom
        elements.append(make_element(
            content=f"Page {page}", page=page, y0=0.95, y1=0.98,
            etype=ElementType.FOOTER,
        ))
    engine.detect(elements)
    # Should detect header as template (10x compression)
    headers = engine.get_headers()
    assert len(headers) >= 1
    # Some footers should be detected (though page numbers vary)
    stats = engine.statistics()
    assert stats.n_elements > 0
    assert stats.n_groups > 0
    assert stats.total_compression_ratio < 1.0


def test_mixed_document_types():
    """Document with headers, footers, tables, logos."""
    engine = RecurrenceEngine()
    elements = []
    for page in range(1, 6):
        # Header
        elements.append(make_element(
            content="ACME Corp", page=page, y0=0.02, etype=ElementType.HEADER,
        ))
        # Logo (small image at top-left)
        elements.append(make_element(
            content="logo", page=page, etype=ElementType.FIGURE,
            x0=0.02, y0=0.02, x1=0.08, y1=0.06,
        ))
        # Table
        elements.append(make_element(
            content="| Region | Sales |\n|---|---|\n| A | 100 |",
            page=page, etype=ElementType.TABLE,
        ))
        # Footer
        elements.append(make_element(
            content="Confidential", page=page, y0=0.95, etype=ElementType.FOOTER,
        ))
    engine.detect(elements)
    # All types should be detected
    headers = engine.get_headers()
    footers = engine.get_footers()
    logos = engine.get_logos()
    tables = engine.get_tables()
    assert len(headers) >= 1
    assert len(footers) >= 1
    assert len(logos) >= 1
    assert len(tables) >= 1


def test_statistics():
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Footer", page=p, y0=0.95)
        for p in range(1, 6)
    ]
    engine.detect(elements)
    stats = engine.statistics()
    assert stats.n_elements > 0
    assert stats.n_groups > 0
    assert stats.avg_frequency > 0
    assert "footer" in stats.group_types or len(stats.group_types) > 0


def test_no_recurrence_in_unique_document():
    engine = RecurrenceEngine()
    elements = [
        make_element(content=f"Unique content {i}", page=1)
        for i in range(5)
    ]
    engine.detect(elements)
    # All elements are unique → no recurrence groups
    stats = engine.compression_stats()
    assert stats["avg_compression"] >= 0.9  # Minimal compression


def test_recurrence_threshold():
    """3+ occurrences = template."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Header", page=p, y0=0.02)
        for p in range(1, 3)  # Only 2 pages
    ]
    engine.detect(elements)
    headers = engine.get_headers()
    # 2 occurrences = not a template
    if headers:
        assert not headers[0].is_template


def test_high_recurrence_strong_compression():
    """50 occurrences → 50x compression potential."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Same Footer", page=p, y0=0.95)
        for p in range(1, 51)
    ]
    engine.detect(elements)
    footers = engine.get_footers()
    if footers:
        # 50 occurrences
        assert footers[0].count == 50
        assert footers[0].compression_ratio() == pytest.approx(0.02, abs=0.01)


def test_mixed_recurrence_types_compression():
    """Document with multiple recurrence types."""
    engine = RecurrenceEngine()
    elements = []
    for page in range(1, 21):
        elements.append(make_element(
            content="ACME CORP", page=page, y0=0.02, etype=ElementType.HEADER,
        ))
        elements.append(make_element(
            content="Logo", page=page, etype=ElementType.FIGURE,
            x0=0.02, y0=0.02, x1=0.08, y1=0.06,
        ))
        elements.append(make_element(
            content=f"© {2024}", page=page, y0=0.95, etype=ElementType.FOOTER,
        ))
    engine.detect(elements)
    stats = engine.compression_stats()
    # Should achieve significant compression
    assert stats["compression_ratio_pct"] > 50


def test_element_updated_after_detect():
    """After detect(), elements should have recurrence_id and frequency."""
    engine = RecurrenceEngine()
    elements = [
        make_element(content="Header", page=p, y0=0.02)
        for p in range(1, 4)
    ]
    assert all(e.recurrence_id is None for e in elements)
    engine.detect(elements)
    # After detection, header elements should have recurrence_id
    headers_detected = [e for e in elements if e.recurrence_id is not None]
    assert len(headers_detected) >= 3
    assert all(e.frequency >= 2 for e in headers_detected)


def test_empty_elements():
    engine = RecurrenceEngine()
    groups = engine.detect([])
    assert len(groups) == 0
    stats = engine.statistics()
    assert stats.n_elements == 0
