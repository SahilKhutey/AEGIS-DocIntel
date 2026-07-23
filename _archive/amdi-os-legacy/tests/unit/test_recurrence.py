import pytest
import numpy as np
from src.engines.geometry.element import ElementType, GeometricElement, BoundingBox
from src.engines.recurrence.recurrence_engine import RecurrenceEngine, MinHasher


def make_elem(content, element_id=None, etype=ElementType.PARAGRAPH, page=1, y0=0.3, y1=0.6):
    return GeometricElement(
        element_id=element_id or str(np.random.randint(1000000)),
        doc_id="test",
        page=page,
        type=etype,
        content=content,
        bbox=BoundingBox(0.1, y0, 0.9, y1)
    )


def test_minhasher_signature_shape():
    hasher = MinHasher(n_perm=32)
    sig = hasher.signature({"hello", "world"})
    assert len(sig) == 32
    assert sig.dtype == np.int64


def test_identical_texts_jaccard():
    hasher = MinHasher(n_perm=64)
    tokens = {"apple", "banana", "cherry"}
    sig1 = hasher.signature(tokens)
    sig2 = hasher.signature(tokens)
    assert hasher.jaccard_estimate(sig1, sig2) == 1.0


def test_different_texts_jaccard():
    hasher = MinHasher(n_perm=64)
    tokens1 = {"apple", "banana", "cherry"}
    tokens2 = {"dog", "cat", "bird"}
    sig1 = hasher.signature(tokens1)
    sig2 = hasher.signature(tokens2)
    # They should have very low Jaccard similarity estimate
    assert hasher.jaccard_estimate(sig1, sig2) < 0.5


def test_recurrence_exact_duplicates():
    engine = RecurrenceEngine()
    # 3 identical elements -> should form a template group
    elements = [
        make_elem("Duplicate content here", element_id=f"el-{i}", page=i)
        for i in range(1, 4)
    ]
    rec_map = engine.detect(elements)
    
    assert rec_map.statistics()["groups"] == 1
    assert rec_map.statistics()["template_count"] == 3
    assert elements[0].recurrence_id is not None
    assert elements[0].is_template is True


def test_recurrence_not_template_if_few_duplicates():
    engine = RecurrenceEngine()
    # Only 2 identical elements -> forms a recurrence group but not marked template
    elements = [
        make_elem("Two copies of this text", element_id="el-1", page=1),
        make_elem("Two copies of this text", element_id="el-2", page=2)
    ]
    rec_map = engine.detect(elements)
    
    assert rec_map.statistics()["groups"] == 1
    assert rec_map.statistics()["template_count"] == 0
    assert elements[0].recurrence_id is not None
    assert elements[0].is_template is False


def test_header_footer_positional_template():
    engine = RecurrenceEngine()
    
    # Element positioned in the header area (y < 0.08)
    el_header = make_elem("Header Text", element_id="header-1", y0=0.01, y1=0.05)
    # Element positioned in the footer area (y > 0.92)
    el_footer = make_elem("Footer Page 1", element_id="footer-1", y0=0.93, y1=0.98)
    # Ordinary element
    el_normal = make_elem("Normal text", element_id="normal-1", y0=0.2, y1=0.5)
    
    rec_map = engine.detect([el_header, el_footer, el_normal])
    
    assert el_header.is_template is True
    assert el_footer.is_template is True
    assert el_normal.is_template is False
    assert "header-1" in rec_map.template_ids
    assert "footer-1" in rec_map.template_ids


def test_recurrence_scores():
    engine = RecurrenceEngine()
    
    el_normal = make_elem("Unique normal content", element_id="unique-1")
    el_header = make_elem("Header", element_id="header-1", y0=0.01, y1=0.04)
    
    # 2 copies of some near duplicate text
    el_near1 = make_elem("Near duplicate text of something interesting", element_id="near-1", page=1)
    el_near2 = make_elem("Near duplicate text of something interesting", element_id="near-2", page=2)
    
    elements = [el_normal, el_header, el_near1, el_near2]
    engine.detect(elements)
    
    score_unique = engine.recurrence_score(el_normal)
    score_header = engine.recurrence_score(el_header)
    score_recurrence = engine.recurrence_score(el_near1)
    
    assert score_unique > 0.7
    assert score_header < 0.5
    assert score_recurrence < score_unique
