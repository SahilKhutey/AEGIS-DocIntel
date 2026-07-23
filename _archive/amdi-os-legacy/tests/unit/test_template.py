import pytest
import numpy as np
import uuid
from src.engines.geometry.element import ElementType, GeometricElement, BoundingBox
from src.engines.template.template_engine import TemplateEngine, PageTemplate


def make_elem(page, etype=ElementType.PARAGRAPH, content="Some generic text", y0=0.3, y1=0.6):
    return GeometricElement(
        element_id=str(uuid.uuid4()),
        doc_id="test",
        page=page,
        type=etype,
        content=content,
        bbox=BoundingBox(0.1, y0, 0.9, y1)
    )


def test_page_template_similarity():
    sig1 = np.random.rand(20)
    sig1 = sig1 / np.linalg.norm(sig1)
    
    tmpl = PageTemplate(
        template_id="T01",
        pages=[1, 2],
        cluster_size=2,
        signature=sig1
    )
    
    assert pytest.approx(tmpl.similarity(sig1)) == 1.0
    
    sig2 = np.zeros(20)
    sig2[0] = 1.0
    sig_ortho = np.zeros(20)
    sig_ortho[1] = 1.0
    tmpl_ortho = PageTemplate("T02", signature=sig2)
    assert pytest.approx(tmpl_ortho.similarity(sig_ortho)) == 0.0


def test_template_engine_page_signature_is_unit_vector():
    engine = TemplateEngine()
    elements = [make_elem(page=1), make_elem(page=1)]
    sig = engine._page_sig(elements)
    assert len(sig) == 20
    assert pytest.approx(np.linalg.norm(sig)) == 1.0


def test_template_engine_clustering():
    engine = TemplateEngine(similarity_threshold=0.95, min_cluster=2)
    
    elements = []
    for p in [1, 2, 3]:
        elements.extend([
            make_elem(page=p, etype=ElementType.HEADING, y0=0.1, y1=0.15),
            make_elem(page=p, etype=ElementType.PARAGRAPH, y0=0.2, y1=0.6)
        ])
        
    elements.extend([
        make_elem(page=4, etype=ElementType.TABLE, y0=0.2, y1=0.8)
    ])
    
    templates = engine.build(elements)
    
    assert len(templates) == 1
    tmpl = templates[0]
    assert tmpl.cluster_size == 3
    assert tmpl.pages == [1, 2, 3]
    
    assert engine.page_template(4) is None
    assert engine.page_template(1) is tmpl


def test_template_score():
    engine = TemplateEngine(min_cluster=2)
    elements = []
    # Dominant template needs to span >= 3 pages
    for p in [1, 2, 3]:
        el1 = make_elem(page=p)
        el2 = make_elem(page=p)
        el2.is_template = True
        elements.extend([el1, el2])
        
    engine.build(elements)
    
    el_boiler = elements[1] # is_template = True
    el_content = elements[0] # is_template = False
    
    score_boiler = engine.template_score(el_boiler)
    score_content = engine.template_score(el_content)
    
    assert score_boiler < 0.3
    assert score_content > 0.6


def test_compression_factor():
    engine = TemplateEngine(similarity_threshold=0.99, min_cluster=2)
    elements = []
    # 3 identical pages
    for p in [1, 2, 3]:
        elements.extend([make_elem(page=p)])
    # 1 unique page with different layout/number of elements
    elements.extend([
        make_elem(page=4, etype=ElementType.TABLE, y0=0.1, y1=0.2),
        make_elem(page=4, etype=ElementType.HEADING, y0=0.3, y1=0.4),
        make_elem(page=4, etype=ElementType.FIGURE, y0=0.5, y1=0.8)
    ])
    
    engine.build(elements)
    
    # 4 pages total: 1 cluster of 3 pages (represented by 1 template), 1 unique page.
    # Total pages = 4
    # Covered pages = 3, unique = 4 - 3 + 1 = 2.
    # Compression factor = 2 / 4 = 0.5
    factor = engine.compression_factor(4)
    assert factor == 0.5


def test_statistics():
    engine = TemplateEngine(min_cluster=2)
    elements = []
    for p in [1, 2, 3]:
        elements.extend([make_elem(page=p)])
    engine.build(elements)
    
    stats = engine.statistics()
    assert stats["templates"] == 1
    assert stats["dominant"] == 1
    assert stats["pages_covered"] == 3
    assert stats["max_cluster"] == 3
