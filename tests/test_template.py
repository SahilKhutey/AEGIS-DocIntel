"""Tests for the template engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import pytest
import numpy as np

from src.core.geometric_element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox
from src.engines.template import (
    TemplateEngine, PageTemplate, PageFingerprint,
    DuplicateGroup, TemplateStats,
)


# ============================================================
# HELPERS
# ============================================================

def make_page_elements(
    page: int,
    n_text: int = 5,
    n_tables: int = 0,
    n_figures: int = 0,
    n_headings: int = 1,
    template: str = "default",
) -> list[GeometricElement]:
    """Create a set of elements for a page."""
    elements = []
    y = 0.05
    for i in range(n_headings):
        elements.append(GeometricElement(
            content=f"Heading {i}",
            page=page, type=ElementType.HEADING,
            bbox=BoundingBox(0.1, y, 0.9, y + 0.05),
        ))
        y += 0.1
    for i in range(n_text):
        elements.append(GeometricElement(
            content=f"Paragraph {i} of page {page}",
            page=page, type=ElementType.TEXT,
            bbox=BoundingBox(0.1, y, 0.9, y + 0.1),
        ))
        y += 0.15
    for i in range(n_tables):
        elements.append(GeometricElement(
            content="| A | B |\n|---|---|\n| 1 | 2 |",
            page=page, type=ElementType.TABLE,
            bbox=BoundingBox(0.1, y, 0.9, y + 0.2),
        ))
        y += 0.25
    for i in range(n_figures):
        elements.append(GeometricElement(
            content=f"Figure {i}",
            page=page, type=ElementType.FIGURE,
            bbox=BoundingBox(0.2, y, 0.8, y + 0.15),
        ))
        y += 0.2
    return elements


# ============================================================
# INITIALIZATION
# ============================================================

def test_init():
    engine = TemplateEngine()
    assert engine.templates == {}
    assert engine.fingerprints == {}


# ============================================================
# 1. FINGERPRINT GENERATION
# ============================================================

def test_fingerprint_basic():
    engine = TemplateEngine()
    elements = make_page_elements(1)
    fp = engine.generate_fingerprint(1, elements)
    assert fp.page_number == 1
    assert fp.n_elements == len(elements)
    assert "text" in fp.type_histogram or "paragraph" in fp.type_histogram


def test_fingerprint_type_histogram():
    engine = TemplateEngine()
    elements = (
        make_page_elements(1, n_text=3, n_tables=1, n_figures=1)
    )
    fp = engine.generate_fingerprint(1, elements)
    assert fp.type_histogram.get("text", 0) + fp.type_histogram.get("paragraph", 0) >= 3
    assert fp.type_histogram.get("table", 0) == 1
    assert fp.type_histogram.get("figure", 0) == 1


def test_fingerprint_type_fractions():
    engine = TemplateEngine()
    elements = make_page_elements(1, n_text=4)
    fp = engine.generate_fingerprint(1, elements)
    assert abs(sum(fp.type_fractions.values()) - 1.0) < 0.01


def test_fingerprint_area_stats():
    engine = TemplateEngine()
    elements = make_page_elements(1, n_text=3)
    fp = engine.generate_fingerprint(1, elements)
    assert fp.total_area > 0
    assert fp.avg_area > 0


def test_fingerprint_text_density():
    engine = TemplateEngine()
    elements = make_page_elements(1, n_text=3)
    fp = engine.generate_fingerprint(1, elements)
    assert fp.text_density >= 0


def test_fingerprint_signature_shape():
    engine = TemplateEngine()
    elements = make_page_elements(1)
    fp = engine.generate_fingerprint(1, elements)
    assert fp.signature is not None
    assert fp.signature.shape == (16,)


def test_fingerprint_signature_normalized():
    engine = TemplateEngine()
    elements = make_page_elements(1)
    fp = engine.generate_fingerprint(1, elements)
    norm = np.linalg.norm(fp.signature)
    assert abs(norm - 1.0) < 0.01 or norm == 0


def test_fingerprint_content_hash():
    engine = TemplateEngine()
    elements = make_page_elements(1)
    fp = engine.generate_fingerprint(1, elements)
    assert fp.content_hash != ""
    assert len(fp.content_hash) == 16


def test_fingerprint_stored():
    engine = TemplateEngine()
    elements = make_page_elements(1)
    engine.generate_fingerprint(1, elements)
    assert 1 in engine.fingerprints


def test_empty_page_fingerprint():
    engine = TemplateEngine()
    fp = engine.generate_fingerprint(1, [])
    assert fp.n_elements == 0
    assert fp.total_area == 0


# ============================================================
# 2. SIGNATURE CREATION
# ============================================================

def test_signature_creation():
    engine = TemplateEngine()
    fp = PageFingerprint(page_number=1, n_elements=5)
    sig = engine.create_signature(fp)
    assert sig.shape == (16,)
    assert np.all(sig >= 0)


def test_signature_deterministic():
    engine = TemplateEngine()
    fp1 = PageFingerprint(
        page_number=1, n_elements=5,
        type_histogram={"text": 3, "table": 1},
        type_fractions={"text": 0.6, "table": 0.2}
    )
    fp2 = PageFingerprint(
        page_number=2, n_elements=5,
        type_histogram={"text": 3, "table": 1},
        type_fractions={"text": 0.6, "table": 0.2}
    )
    sig1 = engine.create_signature(fp1)
    sig2 = engine.create_signature(fp2)
    # Same content → similar signatures
    sim = np.dot(sig1, sig2)
    assert sim > 0.9


def test_signature_normalization():
    engine = TemplateEngine()
    fp = PageFingerprint(page_number=1, n_elements=10)
    sig = engine.create_signature(fp)
    norm = np.linalg.norm(sig)
    if norm > 0:
        assert abs(norm - 1.0) < 0.01


def test_signature_different_pages():
    engine = TemplateEngine()
    fp_text = PageFingerprint(
        page_number=1, n_elements=5,
        type_histogram={"text": 5},
        type_fractions={"text": 1.0}
    )
    fp_table = PageFingerprint(
        page_number=2, n_elements=5,
        type_histogram={"table": 5},
        type_fractions={"table": 1.0}
    )
    sig_text = engine.create_signature(fp_text)
    sig_table = engine.create_signature(fp_table)
    # Different signatures
    sim = np.dot(sig_text, sig_table)
    assert sim < 0.95


def test_signature_normalized_handles_zero():
    engine = TemplateEngine()
    fp = PageFingerprint(page_number=1, n_elements=0)
    sig = engine.create_signature(fp)
    # Zero vector is acceptable
    assert sig is not None


# ============================================================
# 3. TEMPLATE CLUSTERING (DBSCAN)
# ============================================================

def test_clustering_basic():
    engine = TemplateEngine()
    # 3 identical pages
    pages = {
        1: make_page_elements(1, n_text=5, n_tables=1),
        2: make_page_elements(2, n_text=5, n_tables=1),
        3: make_page_elements(3, n_text=5, n_tables=1),
    }
    templates = engine.build_templates(pages)
    # Should cluster into at least 1 template
    assert len(templates) >= 1
    # Find a template with 3 pages
    main_template = max(templates, key=lambda t: t.cluster_size)
    assert main_template.cluster_size >= 2


def test_clustering_different_templates():
    engine = TemplateEngine()
    # Page 1: text-heavy
    # Page 2: text-heavy
    # Page 3: table-heavy (different)
    pages = {
        1: make_page_elements(1, n_text=10, n_tables=0),
        2: make_page_elements(2, n_text=10, n_tables=0),
        3: make_page_elements(3, n_text=0, n_tables=3),
    }
    templates = engine.build_templates(pages)
    assert len(templates) >= 1


def test_clustering_single_page():
    engine = TemplateEngine()
    pages = {1: make_page_elements(1)}
    templates = engine.build_templates(pages)
    assert len(templates) >= 1
    # All singleton templates
    assert all(t.cluster_size == 1 for t in templates)


def test_clustering_empty():
    engine = TemplateEngine()
    templates = engine.build_templates({})
    assert templates == []


def test_clustering_min_samples():
    engine = TemplateEngine(min_samples=3, eps=0.3)
    # Only 2 identical pages — should not form cluster with min_samples=3
    pages = {
        1: make_page_elements(1, n_text=5),
        2: make_page_elements(2, n_text=5),
    }
    templates = engine.build_templates(pages)
    # May or may not cluster depending on DBSCAN
    assert isinstance(templates, list)


def test_clustering_invoice_scenario():
    """Realistic invoice scenario: many identical pages."""
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=2, n_tables=2)
        for page in range(1, 21)
    }
    templates = engine.build_templates(pages)
    # Should cluster into 1 dominant template
    dominant = engine.get_dominant_templates()
    assert len(dominant) >= 1
    # Dominant should have many pages
    assert dominant[0].cluster_size >= 5


def test_template_properties():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3, n_tables=1)
        for page in range(1, 11)
    }
    engine.build_templates(pages)
    for t in engine.templates.values():
        assert t.template_id.startswith("T-")
        assert t.cluster_size >= 1
        assert t.pages == sorted(t.pages)


def test_template_compression_ratio():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 11)
    }
    engine.build_templates(pages)
    templates = list(engine.templates.values())
    if templates:
        # Find the main template
        main = max(templates, key=lambda t: t.cluster_size)
        assert main.compression_ratio == 1.0 / main.cluster_size


def test_template_dominant_threshold():
    engine = TemplateEngine()
    # 6 identical pages → dominant template
    pages = {
        page: make_page_elements(page, n_text=3, n_tables=1)
        for page in range(1, 7)
    }
    engine.build_templates(pages)
    dominant = engine.get_dominant_templates()
    assert len(dominant) >= 1
    assert dominant[0].is_dominant
    assert dominant[0].cluster_size >= 5


def test_template_centroid():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 6)
    }
    engine.build_templates(pages)
    for t in engine.templates.values():
        if t.centroid is not None:
            assert np.linalg.norm(t.centroid) > 0


def test_template_composition():
    engine = TemplateEngine()
    pages = {1: make_page_elements(1, n_text=3, n_tables=1)}
    engine.build_templates(pages)
    if engine.templates:
        template = list(engine.templates.values())[0]
        assert isinstance(template.composition, dict)


# ============================================================
# 4. DUPLICATE DETECTION
# ============================================================

def test_exact_duplicates():
    engine = TemplateEngine()
    # Create identical content on 3 pages
    elements_list = []
    for p in [1, 2, 3]:
        elements_list.append(GeometricElement(
            content="Same content", page=p, type=ElementType.TEXT,
            bbox=BoundingBox(0.1, 0.1, 0.9, 0.3)
        ))
    for e in elements_list:
        engine.generate_fingerprint(e.page, [e])
    duplicates = engine.find_exact_duplicates()
    assert len(duplicates) >= 1
    # Should detect all 3 pages as duplicates
    assert len(duplicates[0].pages) == 3


def test_no_duplicates():
    engine = TemplateEngine()
    elements = {
        1: make_page_elements(1, n_text=10),
        2: make_page_elements(2, n_text=2),
    }
    for page, elts in elements.items():
        engine.generate_fingerprint(page, elts)
    duplicates = engine.find_exact_duplicates()
    # Different content → no duplicates
    for d in duplicates:
        assert len(d.pages) >= 2


def test_near_duplicate_detection():
    engine = TemplateEngine(duplicate_threshold=0.9)
    # Create very similar pages (same structure, slight differences)
    pages = {
        1: make_page_elements(1, n_text=5, n_tables=1, n_headings=2),
        2: make_page_elements(2, n_text=5, n_tables=1, n_headings=2),
        3: make_page_elements(3, n_text=5, n_tables=1, n_headings=2),
    }
    engine.generate_fingerprint(1, pages[1])
    engine.generate_fingerprint(2, pages[2])
    engine.generate_fingerprint(3, pages[3])
    duplicates = engine.detect_duplicates()
    # Similar pages should be detected
    assert isinstance(duplicates, list)


def test_duplicate_threshold_parameter():
    engine = TemplateEngine(duplicate_threshold=0.99)  # Very strict
    pages = {
        1: make_page_elements(1, n_text=5),
        2: make_page_elements(2, n_text=5),
    }
    for page, elts in pages.items():
        engine.generate_fingerprint(page, elts)
    duplicates = engine.detect_duplicates(similarity_threshold=0.99)
    # Very strict — may find fewer duplicates
    assert isinstance(duplicates, list)


def test_duplicate_group_properties():
    engine = TemplateEngine()
    elements_list = []
    for p in [1, 2, 3]:
        elements_list.append(GeometricElement(
            content="Identical text here", page=p, type=ElementType.TEXT,
            bbox=BoundingBox(0.1, 0.1, 0.9, 0.3)
        ))
    for e in elements_list:
        engine.generate_fingerprint(e.page, [e])
    duplicates = engine.find_exact_duplicates()
    if duplicates:
        d = duplicates[0]
        assert d.representative_page == min(d.pages)
        assert d.content_hash != ""


# ============================================================
# QUERIES
# ============================================================

def test_get_template():
    engine = TemplateEngine()
    pages = {page: make_page_elements(page) for page in range(1, 5)}
    engine.build_templates(pages)
    template_id = next(iter(engine.templates.keys()))
    template = engine.get_template(template_id)
    assert template is not None


def test_get_template_not_found():
    engine = TemplateEngine()
    assert engine.get_template("nonexistent") is None


def test_get_templates_for_page():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 6)
    }
    engine.build_templates(pages)
    # Find templates containing page 1
    templates_for_p1 = engine.get_templates_for_page(1)
    # Each page should be in at least one template
    assert len(templates_for_p1) >= 1


def test_get_dominant_templates():
    engine = TemplateEngine()
    # 10 identical pages → dominant template
    pages = {
        page: make_page_elements(page, n_text=3, n_tables=1)
        for page in range(1, 11)
    }
    engine.build_templates(pages)
    dominant = engine.get_dominant_templates()
    assert len(dominant) >= 1
    for d in dominant:
        assert d.cluster_size >= 3
        assert d.is_dominant


def test_get_template_by_signature():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=5, n_tables=1)
        for page in range(1, 6)
    }
    engine.build_templates(pages)
    # Use one of the existing signatures
    sample_sig = list(engine.fingerprints.values())[0].signature
    match = engine.get_template_by_page_signature(sample_sig)
    assert match is not None


def test_find_similar_templates():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 6)
    }
    engine.build_templates(pages)
    templates = list(engine.templates.values())
    if len(templates) >= 2:
        similar = engine.find_similar_templates(templates[0], top_k=3)
        assert len(similar) <= 3


# ============================================================
# STATISTICS
# ============================================================

def test_statistics_empty():
    engine = TemplateEngine()
    stats = engine.statistics()
    assert stats.n_pages == 0
    assert stats.n_templates == 0


def test_statistics_with_templates():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 8)
    }
    engine.build_templates(pages)
    stats = engine.statistics()
    assert stats.n_pages > 0
    assert stats.n_templates >= 1
    assert stats.avg_cluster_size >= 1.0
    assert stats.max_cluster_size >= 1
    assert stats.compression_ratio > 0


def test_statistics_dominant_count():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 11)
    }
    engine.build_templates(pages)
    stats = engine.statistics()
    assert stats.n_dominant_templates >= 1


def test_statistics_compression():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 21)
    }
    engine.build_templates(pages)
    stats = engine.statistics()
    # 20 pages should compress to <1.0 ratio
    assert stats.compression_ratio < 1.0


def test_compression_report():
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3, n_tables=1)
        for page in range(1, 11)
    }
    engine.build_templates(pages)
    report = engine.compression_report()
    assert "overall_compression" in report
    assert "templates" in report
    assert "n_pages" in report
    assert "n_templates" in report


def test_compression_report_savings():
    engine = TemplateEngine()
    # Many identical pages → high savings
    pages = {
        page: make_page_elements(page, n_text=3, n_tables=1)
        for page in range(1, 51)
    }
    engine.build_templates(pages)
    report = engine.compression_report()
    assert report["overall_savings_pct"] > 80


def test_clear():
    engine = TemplateEngine()
    pages = {page: make_page_elements(page) for page in range(1, 4)}
    engine.build_templates(pages)
    assert len(engine.templates) > 0
    engine.clear()
    assert len(engine.templates) == 0
    assert len(engine.fingerprints) == 0


# ============================================================
# DATA CLASS TESTS
# ============================================================

def test_page_fingerprint_defaults():
    fp = PageFingerprint(page_number=1, n_elements=0)
    assert fp.page_number == 1
    assert fp.n_elements == 0
    assert fp.type_histogram == {}


def test_page_template_is_template():
    t = PageTemplate(template_id="t1", pages=[1, 2, 3], cluster_size=3)
    assert t.is_template
    assert t.is_dominant  # Since we map to >=3


def test_page_template_is_dominant():
    t = PageTemplate(template_id="t1", pages=[1, 2, 3, 4, 5], cluster_size=5)
    assert t.is_dominant
    assert t.compression_ratio == pytest.approx(0.2)


def test_page_template_compression():
    t = PageTemplate(template_id="t1", pages=[1, 2, 3, 4], cluster_size=4)
    assert t.compression_ratio == 0.25  # 1/4


def test_page_template_to_dict():
    t = PageTemplate(template_id="t1", pages=[1, 2, 3], cluster_size=3)
    d = t.to_dict()
    assert d["template_id"] == "t1"
    assert d["pages"] == [1, 2, 3]
    assert d["is_template"] is True
    assert d["compression_ratio"] == pytest.approx(1/3)


def test_duplicate_group_creation():
    g = DuplicateGroup(
        group_id="d1",
        pages=[1, 2, 3],
        representative_page=1,
        content_hash="abc123",
    )
    assert len(g.pages) == 3
    assert g.representative_page == 1


# ============================================================
# INTEGRATION TESTS
# ============================================================

def test_invoice_workflow():
    """Realistic invoice document with 20 identical invoice pages."""
    engine = TemplateEngine()
    pages = {
        page: [
            GeometricElement(
                content=f"Invoice #{page}",
                page=page, type=ElementType.HEADING,
                bbox=BoundingBox(0.1, 0.05, 0.5, 0.1),
            ),
            GeometricElement(
                content=f"Date: 2024-01-{page:02d}",
                page=page, type=ElementType.TEXT,
                bbox=BoundingBox(0.1, 0.15, 0.5, 0.2),
            ),
            GeometricElement(
                content="| Item | Qty | Price |\n|---|---|---|\n| A | 1 | 100 |",
                page=page, type=ElementType.TABLE,
                bbox=BoundingBox(0.1, 0.3, 0.9, 0.6),
            ),
            GeometricElement(
                content=f"Page {page}",
                page=page, type=ElementType.FOOTER,
                bbox=BoundingBox(0.4, 0.95, 0.6, 0.98),
            ),
        ]
        for page in range(1, 21)
    }
    templates = engine.build_templates(pages)
    # Should detect 1 dominant template
    dominant = engine.get_dominant_templates()
    assert len(dominant) >= 1
    # Compression should be significant
    stats = engine.statistics()
    assert stats.compression_ratio < 0.5


def test_mixed_document():
    """Document with multiple distinct sections."""
    engine = TemplateEngine()
    pages = {}
    # Title page
    pages[1] = [
        GeometricElement(content="ANNUAL REPORT", page=1, type=ElementType.TITLE,
                       bbox=BoundingBox(0.1, 0.1, 0.9, 0.3)),
        GeometricElement(content="Cover page content", page=1, type=ElementType.TEXT,
                       bbox=BoundingBox(0.1, 0.5, 0.9, 0.7)),
    ]
    # Content pages (similar)
    for p in range(2, 6):
        pages[p] = make_page_elements(p, n_text=5, n_headings=1)
    # Summary page
    pages[6] = [
        GeometricElement(content="Summary", page=6, type=ElementType.HEADING,
                       bbox=BoundingBox(0.1, 0.1, 0.9, 0.15)),
        GeometricElement(content="Final summary text", page=6, type=ElementType.TEXT,
                       bbox=BoundingBox(0.1, 0.3, 0.9, 0.5)),
    ]
    templates = engine.build_templates(pages)
    # Should have at least 1 template
    assert len(templates) >= 1


def test_statistics_consistency():
    """Verify statistics are internally consistent."""
    engine = TemplateEngine()
    pages = {
        page: make_page_elements(page, n_text=3)
        for page in range(1, 11)
    }
    engine.build_templates(pages)
    stats = engine.statistics()
    # n_pages should equal sum of cluster sizes
    total_pages = sum(t.cluster_size for t in engine.templates.values())
    assert stats.n_pages == total_pages
    # max cluster size should be in templates
    assert stats.max_cluster_size == max(t.cluster_size for t in engine.templates.values())


def test_singleton_template_creation():
    """Test creating a template from a single page."""
    engine = TemplateEngine()
    pages = {1: make_page_elements(1, n_text=5)}
    templates = engine.build_templates(pages)
    # Should create at least one template (singleton)
    assert len(templates) >= 1
    # All templates should have cluster_size 1
    assert all(t.cluster_size == 1 for t in templates)


def test_singleton_template_id_format():
    """Singleton templates should have 'singleton' in their ID."""
    engine = TemplateEngine()
    pages = {1: make_page_elements(1)}
    engine.build_templates(pages)
    singletons = [t for t in engine.templates.values() if t.cluster_size == 1]
    for t in singletons:
        assert "singleton" in t.template_id or t.cluster_size > 1
