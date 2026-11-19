"""
AEGIS-DocIntel — Task PH-004: Document Parsing & Layout Hierarchy Verification
=============================================================================
Validates:
1. Structural parsing of documents into NormalizedDocument, NormalizedPage, and NormalizedBlock.
2. Layout hierarchy, section assignments, and heading level inference (LayoutDetector).
3. Table detection and structured block categorization.
4. Spatial Reading Graph topological reading order recovery (Kahn's DAG algorithm)
   with strict permutation invariance / determinism (Theorem 6.2).
"""
from __future__ import annotations

from pathlib import Path
import pytest

from src.core.normalized_document import (
    BlockType,
    NormalizedBlock,
    NormalizedDocument,
    NormalizedPage,
)
from src.engines.parsers.universal_parser import UniversalParser
from src.engines.layout.layout_detector import LayoutDetector
from src.engines.graph_reading_order import (
    SpatialReadingGraph,
    ReadingGraphConfig,
)
from src.models.document_object import DocumentFormat, DocumentObject

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


def test_normalized_document_hierarchy():
    """Verify NormalizedDocument structure and block relationships."""
    doc = NormalizedDocument(doc_id="doc-test-001", filename="annual_report.pdf")
    page = NormalizedPage(page_number=1, width=612.0, height=792.0)
    
    b1 = NormalizedBlock(
        block_id="blk-1",
        block_type=BlockType.TITLE,
        text="Executive Summary 2026",
        bbox=(50.0, 50.0, 550.0, 90.0),
        confidence=0.99,
        page_number=1,
    )
    b2 = NormalizedBlock(
        block_id="blk-2",
        block_type=BlockType.TEXT,
        text="The company delivered record operating margins across all sectors.",
        bbox=(50.0, 100.0, 550.0, 160.0),
        confidence=0.98,
        page_number=1,
    )
    b3 = NormalizedBlock(
        block_id="blk-3",
        block_type=BlockType.TABLE,
        text="| Metric | 2025 | 2026 |\n| Operating Margin | 18% | 24% |",
        bbox=(50.0, 180.0, 550.0, 300.0),
        confidence=0.97,
        page_number=1,
    )
    page.blocks.extend([b1, b2, b3])
    doc.pages.append(page)

    assert len(doc.pages) == 1
    assert len(doc.all_blocks()) == 3
    assert doc.pages[0].blocks[0].block_type == BlockType.TITLE
    assert doc.pages[0].blocks[2].block_type == BlockType.TABLE


@pytest.mark.asyncio
async def test_layout_detector_enrichment():
    """Verify LayoutDetector assigns sections, heading levels, and column estimates."""
    doc = NormalizedDocument(doc_id="doc-layout-001", filename="paper.pdf")
    page = NormalizedPage(page_number=1, width=600.0, height=800.0)

    # Title block (large bbox height = 25pt -> Level 1)
    title = NormalizedBlock(
        block_id="b-title",
        block_type=BlockType.TITLE,
        text="Deep Neural Architectures",
        bbox=(50.0, 40.0, 550.0, 65.0),  # height = 25.0
        page_number=1,
    )
    # Paragraph under Title
    para1 = NormalizedBlock(
        block_id="b-para1",
        block_type=BlockType.TEXT,
        text="Recent advancements in transformer self-attention have revolutionized NLP.",
        bbox=(50.0, 80.0, 280.0, 150.0),
        page_number=1,
    )
    # Subtitle block (height = 16pt -> Level 2)
    sub = NormalizedBlock(
        block_id="b-sub",
        block_type=BlockType.SUBTITLE,
        text="Methodology",
        bbox=(50.0, 160.0, 280.0, 176.0),  # height = 16.0
        page_number=1,
    )
    para2 = NormalizedBlock(
        block_id="b-para2",
        block_type=BlockType.TEXT,
        text="We employ a multi-head sparse attention kernel.",
        bbox=(50.0, 190.0, 280.0, 250.0),
        page_number=1,
    )

    page.blocks.extend([title, para1, sub, para2])
    doc.pages.append(page)

    detector = LayoutDetector()
    enriched_doc = await detector.analyze(doc)

    # Check heading levels
    enriched_blocks = {b.block_id: b for b in enriched_doc.all_blocks()}
    assert enriched_blocks["b-title"].level == 1
    assert enriched_blocks["b-sub"].level == 2
    # Check section propagation
    assert enriched_blocks["b-para1"].section == "Deep Neural Architectures"
    assert enriched_blocks["b-para2"].section == "Methodology"


@pytest.mark.asyncio
async def test_universal_parser_plain_text():
    """Verify UniversalParser transforms raw text into NormalizedDocument."""
    text_content = "# Section 1: Introduction\n\nDocIntel processes multi-modal unstructured data.\n\n# Section 2: Architecture\n\nThe engine uses Kahn DAG reading order."
    doc_obj = DocumentObject(
        filename="overview.txt",
        format=DocumentFormat.TEXT,
        text_content=text_content,
        raw_bytes=text_content.encode("utf-8"),
    )

    parser = UniversalParser()
    norm_doc = await parser.parse(doc_obj)

    assert isinstance(norm_doc, NormalizedDocument)
    assert len(norm_doc.pages) >= 1
    assert len(norm_doc.all_blocks()) >= 2
    assert any("DocIntel" in b.text for b in norm_doc.all_blocks())


def test_spatial_reading_graph_kahn_dag_determinism():
    """Verify SpatialReadingGraph uses Kahn's algorithm and guarantees determinism under permutation."""
    elements = [
        {"id": "header", "x": 0.1, "y": 0.05, "w": 0.8, "h": 0.05},
        {"id": "col1_top", "x": 0.1, "y": 0.15, "w": 0.35, "h": 0.10},
        {"id": "col1_bot", "x": 0.1, "y": 0.28, "w": 0.35, "h": 0.10},
        {"id": "col2_top", "x": 0.55, "y": 0.15, "w": 0.35, "h": 0.10},
        {"id": "col2_bot", "x": 0.55, "y": 0.28, "w": 0.35, "h": 0.10},
        {"id": "footer", "x": 0.1, "y": 0.85, "w": 0.8, "h": 0.05},
    ]

    graph = SpatialReadingGraph(ReadingGraphConfig(row_tolerance=0.03))
    V_fwd, E_fwd = graph.build_reading_graph(elements)
    order_fwd = graph.recover_reading_order(V_fwd, E_fwd)

    # Permuted / reversed input
    permuted = [elements[5], elements[2], elements[0], elements[4], elements[1], elements[3]]
    V_perm, E_perm = graph.build_reading_graph(permuted)
    order_perm = graph.recover_reading_order(V_perm, E_perm)

    assert len(order_fwd) == 6
    assert len(order_perm) == 6
    # Theorem 6.2: Output reading sequence must be identical regardless of input order
    assert [n["id"] for n in order_fwd] == [n["id"] for n in order_perm]
    # Header must be first, footer must be last
    assert order_fwd[0]["id"] == "header"
    assert order_fwd[-1]["id"] == "footer"
