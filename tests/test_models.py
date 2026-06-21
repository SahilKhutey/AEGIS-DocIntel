"""Tests for all Pydantic document data models."""
import os
import sys
from pathlib import Path
import pytest
import math
from datetime import datetime

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.models import (
    DocumentObject, DocumentFormat, DocumentStatus, DocumentSource,
    PageObject, PageLayout, PageOrientation,
    GeometryObject, BoundingBox, ElementType,
    MatrixObject, TableCell, TableMetadata, CellType,
    GraphObject, GraphNode, GraphEdge, GraphMetrics, NodeType, EdgeType,
    SemanticObject, Entity, Keyphrase, Topic, SentimentScore, EntityType, EmbeddingInfo,
    ContextObject, ContextPiece, ContextBudget, Citation, ContextSource,
    ExportObject, ExportMetadata, ExportSummary, ExportSemantic,
    ExportGeometry, ExportMatrix, ExportGraph, ExportTemplate,
    ExportTable, ExportGraphNode, ExportGraphEdge, ExportKeyPoint,
    ExportConfidence, ExportFormat, AgentType,
)


# ===== DocumentObject =====

def test_document_object_creation():
    doc = DocumentObject(filename="test.pdf", format=DocumentFormat.PDF)
    assert doc.filename == "test.pdf"
    assert doc.format == DocumentFormat.PDF
    assert doc.size_bytes == 0
    assert doc.doc_id != ""
    assert doc.content_hash != ""


def test_document_object_with_content():
    doc = DocumentObject(
        filename="report.pdf",
        format=DocumentFormat.PDF,
        raw_bytes=b"Hello world content",
        title="Annual Report",
        author="John Doe",
        tags=["financial", "2024"],
    )
    assert doc.title == "Annual Report"
    assert doc.size_bytes == 19
    assert "financial" in doc.tags


def test_document_object_hash_uniqueness():
    doc1 = DocumentObject(filename="a.pdf", raw_bytes=b"hello")
    doc2 = DocumentObject(filename="a.pdf", raw_bytes=b"hello")
    doc3 = DocumentObject(filename="a.pdf", raw_bytes=b"world")
    assert doc1.content_hash == doc2.content_hash
    assert doc1.content_hash != doc3.content_hash


def test_document_object_validation():
    # Language normalization
    doc = DocumentObject(filename="x.pdf", language="ENGLISH")
    assert doc.language == "en"


# ===== PageObject =====

def test_page_object_creation():
    page = PageObject(doc_id="doc-1", page_number=1, width=612, height=792)
    assert page.aspect_ratio == pytest.approx(612 / 792)
    assert page.area == 612 * 792
    assert page.text_density == 0


def test_page_object_with_text():
    page = PageObject(
        doc_id="doc-1", page_number=1, width=612, height=792,
        raw_text="Hello world " * 100,
    )
    assert page.text_density > 0


def test_page_object_validation():
    with pytest.raises(ValueError):
        PageObject(doc_id="d", page_number=0, width=612, height=792)
    with pytest.raises(ValueError):
        PageObject(doc_id="d", page_number=1, width=0, height=792)


# ===== BoundingBox & GeometryObject =====

def test_bounding_box():
    bb = BoundingBox(x0=0.1, y0=0.2, x1=0.9, y1=0.5)
    assert bb.width == pytest.approx(0.8)
    assert bb.height == pytest.approx(0.3)
    assert bb.area == pytest.approx(0.24)
    assert bb.center == (0.5, 0.35)


def test_bounding_box_iou():
    bb1 = BoundingBox(x0=0.0, y0=0.0, x1=0.8, y1=0.8)
    bb2 = BoundingBox(x0=0.4, y0=0.4, x1=1.0, y1=1.0)
    iou = bb1.iou(bb2)
    # Intersection: [0.4, 0.4] to [0.8, 0.8], area = 0.4*0.4 = 0.16
    # Union: 0.64 + 0.36 - 0.16 = 0.84
    # IoU: 0.16 / 0.84 = 4 / 21
    assert iou == pytest.approx(0.16 / 0.84, abs=1e-6)


def test_bounding_box_distance():
    bb1 = BoundingBox(x0=0.0, y0=0.0, x1=0.2, y1=0.2)
    bb2 = BoundingBox(x0=0.8, y0=0.8, x1=1.0, y1=1.0)
    d = bb1.distance_to(bb2)
    # Centers: (0.1, 0.1) and (0.9, 0.9)
    # Distance: √((0.8)² + (0.8)²) = √1.28
    assert d == pytest.approx(math.sqrt(1.28), abs=1e-6)


def test_bounding_box_validation():
    with pytest.raises(ValueError):
        BoundingBox(x0=1.0, y0=0.0, x1=0.0, y1=1.0)


def test_geometry_object():
    bb = BoundingBox(x0=0.1, y0=0.2, x1=0.9, y1=0.5)
    obj = GeometryObject(
        doc_id="doc-123",
        page=1,
        bbox=bb,
        type=ElementType.HEADING,
        content="Testing layout extraction",
    )
    assert obj.x_center == 0.5
    assert obj.y_center == 0.35
    assert obj.area_ratio == pytest.approx(0.24)


# ===== MatrixObject =====

def test_matrix_object():
    cells = [
        TableCell(value="A", row=0, col=0, is_header=True),
        TableCell(value=100.0, cell_type=CellType.NUMBER, row=1, col=0),
    ]
    mat = MatrixObject(
        doc_id="doc-1",
        headers=["A"],
        rows=[["100.0"]],
        cells=cells,
        matrix=[[100.0]]
    )
    assert mat.shape == (1, 1)
    arr = mat.to_numpy()
    assert arr[0, 0] == 100.0
    assert "Row 0" in mat.to_llm_string()
    assert "| A |" in mat.to_markdown()


# ===== GraphObject =====

def test_graph_object():
    nodes = [
        GraphNode(node_id="n1", type=NodeType.ELEMENT, label="Element 1", page=1),
        GraphNode(node_id="n2", type=NodeType.ELEMENT, label="Element 2", page=1)
    ]
    edges = [
        GraphEdge(src_id="n1", dst_id="n2", edge_type=EdgeType.FOLLOWS)
    ]
    graph = GraphObject(doc_id="doc-1", nodes=nodes, edges=edges)
    assert graph.n_nodes == 2
    assert graph.n_edges == 1
    assert graph.density == 0.5
    assert len(graph.get_neighbors("n1")) == 1


# ===== SemanticObject =====

def test_semantic_object():
    entities = [
        Entity(text="Google", type=EntityType.ORGANIZATION, page=1, confidence=0.99)
    ]
    keyphrases = [
        Keyphrase(text="cloud computing", score=0.95, page=1)
    ]
    sem = SemanticObject(
        doc_id="doc-1",
        text="Google cloud computing service details.",
        embedding=[0.1] * 1024,
        entities=entities,
        keyphrases=keyphrases
    )
    assert sem.n_entities == 1
    assert sem.n_keyphrases == 1
    assert sem.has_embedding is True
    assert sem.top_entities(1)[0].text == "Google"
    assert sem.top_keyphrases(1)[0].text == "cloud computing"


# ===== ContextObject =====

def test_context_object():
    piece = ContextPiece(
        content="Standard piece of retrieved context",
        source=ContextSource.TEXT,
        relevance_score=0.9,
        page=1
    )
    budget = ContextBudget()
    ctx = ContextObject(
        doc_id="doc-1",
        query="What is retrieval?",
        pieces=[piece],
        assembled_context="Standard piece of retrieved context",
        budget=budget
    )
    assert ctx.citation_count == 0
    assert len(ctx.to_llm_messages()) == 2


# ===== ExportObject =====

def test_export_object():
    meta = ExportMetadata(
        document_name="test.pdf",
        pages=10,
        doc_id="doc-1"
    )
    summary = ExportSummary(
        title="Summary of test",
        abstract="Long text summary"
    )
    ueo = ExportObject(
        metadata=meta,
        query="What is the abstract?",
        document_summary=summary,
        confidence=ExportConfidence(overall=0.95)
    )
    assert ueo.n_citations == 0
    assert ueo.confidence.overall == 0.95
    assert "# test.pdf" in ueo.to_markdown()
    assert ueo.to_json() != ""
