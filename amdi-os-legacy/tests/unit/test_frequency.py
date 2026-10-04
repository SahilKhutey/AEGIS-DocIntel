import pytest
import uuid
from src.engines.geometry.element import ElementType, GeometricElement, BoundingBox
from src.engines.frequency.frequency_engine import FrequencyEngine


def make_elem(content, etype=ElementType.PARAGRAPH, is_template=False, y0=0.3, y1=0.6):
    return GeometricElement(
        element_id=str(uuid.uuid4()),
        doc_id="test",
        page=1,
        type=etype,
        content=content,
        is_template=is_template,
        bbox=BoundingBox(0.1, y0, 0.9, y1)
    )


def test_frequency_engine_fit():
    engine = FrequencyEngine()
    elements = [
        make_elem("cat dog bird"),
        make_elem("cat fish"),
        make_elem("cat dog")
    ]
    engine.fit(elements)
    
    assert "cat" in engine._idf
    assert "fish" in engine._idf
    assert engine._idf["fish"] > engine._idf["cat"]


def test_frequency_engine_assign_weights():
    engine = FrequencyEngine()
    elements = [
        make_elem("this is a unique term that only appears here"),
        make_elem("cat dog fish"),
        make_elem("cat dog fish"),
        make_elem("empty")
    ]
    imp_map = engine.assign_weights(elements)
    
    assert len(imp_map.weights) == 4
    for eid, weight in imp_map.weights.items():
        assert 0.0 <= weight <= 1.0


def test_frequency_engine_template_penalty():
    engine = FrequencyEngine()
    el_normal = make_elem("same boilerplate content text", is_template=False)
    el_template = make_elem("same boilerplate content text", is_template=True)
    el_dummy = make_elem("different text")
    
    elements = [el_normal, el_template, el_dummy]
    engine.fit(elements)
    engine.assign_weights(elements)
    
    assert el_template.importance_weight < el_normal.importance_weight


def test_frequency_engine_structural_bonus():
    engine = FrequencyEngine()
    el_para = make_elem("some statistics numbers table content data description", etype=ElementType.PARAGRAPH)
    el_table = make_elem("some statistics numbers table content data description", etype=ElementType.TABLE)
    el_dummy = make_elem("different random text")
    
    elements = [el_para, el_table, el_dummy]
    engine.fit(elements)
    engine.assign_weights(elements)
    
    assert el_table.importance_weight > el_para.importance_weight


def test_frequency_engine_empty_content():
    engine = FrequencyEngine()
    el_empty = make_elem("")
    el_rich = make_elem("very informative and extremely unique text block that represents a clean paragraph of high entropy and low redundancy")
    el_dummy = make_elem("some normal middle text")
    
    elements = [el_empty, el_rich, el_dummy]
    engine.fit(elements)
    engine.assign_weights(elements)
    
    assert el_empty.importance_weight < el_rich.importance_weight
