import pytest
from src.engines.geometry.element import BoundingBox, ElementType, GeometricElement
from src.engines.geometry.geometry_engine import GeometryEngine


def test_bounding_box_width_height():
    bbox = BoundingBox(0.1, 0.2, 0.5, 0.7)
    assert pytest.approx(bbox.width) == 0.4
    assert pytest.approx(bbox.height) == 0.5


def test_bounding_box_area():
    bbox = BoundingBox(0.1, 0.2, 0.5, 0.7)
    assert pytest.approx(bbox.area) == 0.20


def test_bounding_box_iou_identical():
    bbox = BoundingBox(0.1, 0.2, 0.5, 0.7)
    assert pytest.approx(bbox.iou(bbox)) == 1.0


def test_bounding_box_iou_no_overlap():
    bbox1 = BoundingBox(0.0, 0.0, 0.2, 0.2)
    bbox2 = BoundingBox(0.3, 0.3, 0.5, 0.5)
    assert bbox1.iou(bbox2) == 0.0


def test_bounding_box_normalization():
    bbox = BoundingBox(10.0, 20.0, 50.0, 60.0)
    norm = bbox.to_normalized(100.0, 200.0)
    assert pytest.approx(norm.x0) == 0.1
    assert pytest.approx(norm.y0) == 0.1
    assert pytest.approx(norm.x1) == 0.5
    assert pytest.approx(norm.y1) == 0.3


def test_geometry_engine_add_and_count():
    engine = GeometryEngine()
    engine.set_page_dims(1, 100, 200)
    elements = [
        GeometricElement(element_id=f"el-{i}", doc_id="doc1", page=1, content=f"Text {i}")
        for i in range(5)
    ]
    engine.add_many(elements)
    stats = engine.statistics()
    assert stats["total_pages"] == 1
    assert stats["total_elements"] == 5
    assert stats["avg_elements_per_page"] == 5.0


def test_geometry_engine_page_elements():
    engine = GeometryEngine()
    engine.set_page_dims(1, 100, 200)
    engine.set_page_dims(2, 100, 200)
    
    el1 = GeometricElement(element_id="el-1", doc_id="doc1", page=1, content="Page 1")
    el2 = GeometricElement(element_id="el-2", doc_id="doc1", page=2, content="Page 2")
    
    engine.add_many([el1, el2])
    
    p1_elems = engine.page_elements(1)
    p2_elems = engine.page_elements(2)
    
    assert len(p1_elems) == 1
    assert p1_elems[0].element_id == "el-1"
    assert len(p2_elems) == 1
    assert p2_elems[0].element_id == "el-2"


def test_geometry_relevance_page_match():
    engine = GeometryEngine()
    el = GeometricElement(element_id="el-1", page=2, type=ElementType.PARAGRAPH)
    
    # Matching page should get score bonus
    score_match = engine.geometry_relevance(query_pages=[2], element=el)
    score_neighbor = engine.geometry_relevance(query_pages=[3], element=el)
    score_no_match = engine.geometry_relevance(query_pages=[5], element=el)
    
    assert score_match > score_neighbor
    assert score_neighbor > score_no_match


def test_geometry_relevance_structural_bonus():
    engine = GeometryEngine()
    el_para = GeometricElement(element_id="el-1", page=1, type=ElementType.PARAGRAPH)
    el_table = GeometricElement(element_id="el-2", page=1, type=ElementType.TABLE)
    
    score_para = engine.geometry_relevance(query_pages=[1], element=el_para)
    score_table = engine.geometry_relevance(query_pages=[1], element=el_table)
    
    assert score_table > score_para


def test_geometric_element_token_count():
    el = GeometricElement(content="This is a test sentence with ten words or so.")
    assert el.token_count > 0
