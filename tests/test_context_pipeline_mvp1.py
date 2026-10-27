"""MVP 1 regression tests for deterministic context chunking."""
from __future__ import annotations

import pytest

from src.core.context_pipeline import (
    ContextChunk,
    ContextResult,
    build_context_for_normalized_text,
    build_context_from_normalized_document,
    chunk_text,
    normalize_text,
)
from src.core.normalized_document import (
    BlockType,
    NormalizedBlock,
    NormalizedDocument,
    NormalizedPage,
)


def test_normalization_preserves_paragraph_boundaries() -> None:
    result = normalize_text(" First line\r\n\r\nSecond line ")
    assert result == "First line\n\nSecond line"


def test_empty_text_returns_no_chunks() -> None:
    result = chunk_text(document_id="doc-empty", text=" \n\t ")
    assert result.chunk_count == 0
    assert result.chunks == ()
    assert result.text_length == 0


def test_chunk_offsets_reconstruct_source_slices() -> None:
    source = ("AEGIS document intelligence. " * 150).strip()
    result = chunk_text(
        document_id="doc-offsets",
        text=source,
        max_chars=240,
        overlap_chars=40,
    )
    assert result.chunk_count > 1
    for chunk in result.chunks:
        assert source[chunk.char_start:chunk.char_end] == chunk.text
        assert len(chunk.text) <= 240


def test_chunks_cover_source_without_gaps() -> None:
    source = ("0123456789 " * 100).strip()
    result = chunk_text(
        document_id="doc-coverage",
        text=source,
        max_chars=120,
        overlap_chars=30,
    )
    assert result.chunk_count > 1
    assert result.chunks[0].char_start == 0
    assert result.chunks[-1].char_end == len(source)

    for i in range(len(result.chunks) - 1):
        c1 = result.chunks[i]
        c2 = result.chunks[i + 1]
        # Next chunk starts at or before the previous chunk ends (no gaps)
        assert c2.char_start <= c1.char_end
        # Overlap does not exceed configured maximum
        assert (c1.char_end - c2.char_start) <= 30

    # Contiguous 0-based indices
    assert [c.index for c in result.chunks] == list(range(len(result.chunks)))


def test_deterministic_chunking_identical_output() -> None:
    source = "Deterministic chunking verification text.\n\nSection 1:\nKey details here."
    r1 = chunk_text(document_id="doc-det", text=source, max_chars=40, overlap_chars=10)
    r2 = chunk_text(document_id="doc-det", text=source, max_chars=40, overlap_chars=10)

    assert r1.chunk_count == r2.chunk_count
    assert r1.text_length == r2.text_length
    for c1, c2 in zip(r1.chunks, r2.chunks):
        assert c1.chunk_id == c2.chunk_id
        assert c1.char_start == c2.char_start
        assert c1.char_end == c2.char_end
        assert c1.text == c2.text


def test_invalid_parameters_raise_value_error() -> None:
    with pytest.raises(ValueError, match="max_chars must be positive"):
        chunk_text(document_id="doc-err", text="hello", max_chars=0)

    with pytest.raises(ValueError, match="overlap_chars must be non-negative"):
        chunk_text(document_id="doc-err", text="hello", max_chars=100, overlap_chars=-5)

    with pytest.raises(ValueError, match="overlap_chars must be strictly less than max_chars"):
        chunk_text(document_id="doc-err", text="hello", max_chars=100, overlap_chars=100)


def test_build_context_for_normalized_text_adapter() -> None:
    source = "Normalized text through adapter interface."
    res = build_context_for_normalized_text(
        document_id="doc-adapter",
        normalized_text=source,
        max_chars=25,
        overlap_chars=5,
    )
    assert res.chunk_count > 1
    assert res.document_id == "doc-adapter"
    assert res.chunks[0].text == source[:25]


def test_page_provenance_mapping_with_normalized_document() -> None:
    p1_block = NormalizedBlock(
        block_id="b-p1",
        type=BlockType.TEXT,
        text="Alpha header on page one with sufficient length for testing.",
        page=1,
    )
    p2_block = NormalizedBlock(
        block_id="b-p2",
        type=BlockType.TEXT,
        text="Beta content on page two with sufficient length for testing.",
        page=2,
    )
    norm_doc = NormalizedDocument(
        doc_id="doc-provenance",
        filename="report.pdf",
        pages=[
            NormalizedPage(page_number=1, blocks=[p1_block]),
            NormalizedPage(page_number=2, blocks=[p2_block]),
        ],
    )

    # Chunk with max_chars=35 so chunks fall within page 1, cross the boundary, and reach page 2
    res = build_context_from_normalized_document(
        doc=norm_doc,
        max_chars=35,
        overlap_chars=5,
    )
    assert res.chunk_count >= 3
    # First chunk belongs strictly to page 1
    assert res.chunks[0].page_start == 1
    assert res.chunks[0].page_end == 1
    # Last chunk belongs strictly to page 2
    assert res.chunks[-1].page_start == 2
    assert res.chunks[-1].page_end == 2


def test_large_document_scaling() -> None:
    # 50,000 character synthetic document
    source = ("The quick brown fox jumps over the lazy dog. " * 1100).strip()
    res = chunk_text(document_id="doc-large", text=source, max_chars=1000, overlap_chars=100)
    assert res.chunk_count > 50
    assert res.text_length == len(source)
    assert res.chunks[0].char_start == 0
    assert res.chunks[-1].char_end == len(source)
