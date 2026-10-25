"""
tests/test_extraction_fidelity.py
===================================
P2.1 Document Extraction Fidelity & Source Provenance Verification:
Validates that:
1. Normalized elements preserve canonical SourceLocation (doc_id, page, section_path, source_format).
2. Layout-aware reading order distinguishes multi-column papers and flags spatial ambiguities.
3. Structured table representations and cell associations survive normalization.
4. Source provenance survives through chunking and downstream geometric elements.
"""
from __future__ import annotations

import pytest
from aegis_docprep.reading_order import layout_aware_reading_order
from src.core.normalized_document import (
    BlockType,
    NormalizedBlock,
    NormalizedDocument,
    NormalizedElement,
    NormalizedPage,
    SourceLocation,
)
from src.core.orchestrator import AMDIOrchestrator
from src.models.geometry_object import BoundingBox


def test_normalized_elements_and_source_location_provenance():
    """P2.1: NormalizedDocument generates canonical NormalizedElements with immutable SourceLocations."""
    doc_id = "doc-fidelity-123"
    p1 = NormalizedPage(
        page_number=1,
        width=612.0,
        height=792.0,
        blocks=[
            NormalizedBlock(
                block_id="b-title",
                type=BlockType.TITLE,
                text="Advanced Topological Deep Learning",
                bbox=BoundingBox(0.1, 0.05, 0.9, 0.12),
                page=1,
                section="Introduction",
            ),
            NormalizedBlock(
                block_id="b-p1",
                type=BlockType.TEXT,
                text="Geometric deep learning extends neural networks to non-Euclidean domains.",
                bbox=BoundingBox(0.1, 0.15, 0.48, 0.45),
                page=1,
                section="Introduction",
            ),
            NormalizedBlock(
                block_id="b-tbl",
                type=BlockType.TABLE,
                text="Model | Latency | Accuracy\nAMDI | 12ms | 98.4%",
                bbox=BoundingBox(0.52, 0.15, 0.90, 0.45),
                page=1,
                section="Results",
                metadata={
                    "table_structure": {
                        "rows": 2,
                        "cols": 3,
                        "headers": ["Model", "Latency", "Accuracy"],
                        "data": [["AMDI", "12ms", "98.4%"]],
                    }
                },
            ),
        ],
    )

    norm_doc = NormalizedDocument(
        doc_id=doc_id,
        filename="research_paper.pdf",
        pages=[p1],
        language="en",
        metadata={"format": "pdf"},
    )

    elements = norm_doc.to_normalized_elements(source_format="pdf")
    assert len(elements) == 3

    # Element 1: Title
    el0 = elements[0]
    assert isinstance(el0, NormalizedElement)
    assert el0.element_id == "b-title"
    assert el0.kind == "heading"
    assert el0.reading_order == 0
    assert isinstance(el0.location, SourceLocation)
    assert el0.location.document_id == doc_id
    assert el0.location.page_number == 1
    assert el0.location.element_id == "b-title"
    assert el0.location.section_path == ("Introduction",)
    assert el0.location.source_format == "pdf"

    # Element 2: Paragraph
    el1 = elements[1]
    assert el1.element_id == "b-p1"
    assert el1.kind == "paragraph"
    assert el1.reading_order == 1

    # Element 3: Table
    el2 = elements[2]
    assert el2.element_id == "b-tbl"
    assert el2.kind == "table"
    assert el2.reading_order == 2
    assert el2.location.section_path == ("Results",)
    assert "table_structure" in el2.metadata
    assert el2.metadata["table_structure"]["headers"] == ["Model", "Latency", "Accuracy"]


def test_geometric_element_source_location_survival():
    """P2.1: GeometricElements constructed by the orchestrator retain valid SourceLocations."""
    orchestrator = AMDIOrchestrator(config={"embedding_dim": 64})
    doc_id = "doc-geo-456"

    norm_doc = NormalizedDocument(
        doc_id=doc_id,
        filename="annual_filing.pdf",
        pages=[
            NormalizedPage(
                page_number=2,
                blocks=[
                    NormalizedBlock(
                        block_id="blk-exec-sum",
                        type=BlockType.HEADING,
                        text="Executive Summary & Guidance",
                        bbox=BoundingBox(0.1, 0.1, 0.9, 0.18),
                        page=2,
                        section="Management Guidance",
                        metadata={"parent_id": "root-section"},
                    )
                ],
            )
        ],
        metadata={"format": "pdf"},
    )

    geo_elements = orchestrator._to_elements(norm_doc, tenant_id="tenant-acme")
    assert len(geo_elements) == 1
    geo = geo_elements[0]

    assert geo.doc_id == doc_id
    assert geo.tenant_id == "tenant-acme"
    assert geo.page == 2
    assert geo.section == "Management Guidance"
    assert geo.parent_id == "root-section"

    # Verify source_location property
    loc = geo.source_location
    assert isinstance(loc, SourceLocation)
    assert loc.document_id == doc_id
    assert loc.page_number == 2
    assert loc.element_id == "blk-exec-sum"
    assert loc.section_path == ("Management Guidance",)
    assert loc.source_format == "pdf"


def test_two_column_layout_aware_reading_order():
    """P2.1: Layout-aware reading order clusters columns and preserves true reading flow."""
    title = {"id": "title", "x": 0.1, "y": 0.05, "w": 0.8, "h": 0.08}
    col1_top = {"id": "c1_t", "x": 0.1, "y": 0.20, "w": 0.35, "h": 0.2}
    col1_bot = {"id": "c1_b", "x": 0.1, "y": 0.45, "w": 0.35, "h": 0.2}
    col2_top = {"id": "c2_t", "x": 0.55, "y": 0.20, "w": 0.35, "h": 0.2}
    col2_bot = {"id": "c2_b", "x": 0.55, "y": 0.45, "w": 0.35, "h": 0.2}
    footer = {"id": "footer", "x": 0.1, "y": 0.85, "w": 0.8, "h": 0.05}

    # Shuffled input order
    scrambled = [col2_bot, col1_bot, footer, col2_top, title, col1_top]

    ordered, meta = layout_aware_reading_order(scrambled)
    ordered_ids = [e["id"] for e in ordered]

    # Expected: Spanning title -> Column 1 top-to-bottom -> Column 2 top-to-bottom -> Spanning footer
    assert ordered_ids == ["title", "c1_t", "c1_b", "c2_t", "c2_b", "footer"]
    assert meta["detected_columns"] == 2
    assert meta["is_ambiguous"] is False
    assert meta["spanning_count"] == 2


def test_layout_ambiguity_flagging():
    """P2.1: Layout-aware ordering explicitly flags overlapping/conflicting bounding boxes."""
    block1 = {"id": "blk1", "x": 0.2, "y": 0.3, "w": 0.5, "h": 0.4}
    block2 = {"id": "blk2", "x": 0.22, "y": 0.32, "w": 0.48, "h": 0.38}  # Overlaps block1 substantially

    elements = [block1, block2]
    ordered, meta = layout_aware_reading_order(elements)

    assert len(ordered) == 2
    assert meta["is_ambiguous"] is True
    assert len(meta["ambiguities"]) >= 1
    assert "High spatial overlap" in meta["ambiguities"][0]


def test_table_structure_reconstruction():
    """P2.1: Table cells and headers can be reconstructed from normalized representation."""
    table_block = NormalizedBlock(
        block_id="table-fin-q3",
        type=BlockType.TABLE,
        text="Quarter | Revenue | EBITDA\nQ1 | $10M | $2.5M\nQ2 | $12M | $3.1M",
        bbox=BoundingBox(0.1, 0.2, 0.9, 0.5),
        page=3,
        metadata={
            "table_data": {
                "columns": ["Quarter", "Revenue", "EBITDA"],
                "records": [
                    {"Quarter": "Q1", "Revenue": "$10M", "EBITDA": "$2.5M"},
                    {"Quarter": "Q2", "Revenue": "$12M", "EBITDA": "$3.1M"},
                ],
            }
        },
    )

    el = table_block.to_normalized_element(document_id="doc-fin-1", source_format="xlsx")
    assert el.kind == "table"
    assert "table_data" in el.metadata
    records = el.metadata["table_data"]["records"]
    assert len(records) == 2
    assert records[0]["Revenue"] == "$10M"
    assert records[1]["EBITDA"] == "$3.1M"
