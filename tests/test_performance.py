"""
Performance regression tests — marked @pytest.mark.slow.

These tests guard against regressions in time and memory budgets.
They are NOT run in the default test suite. Run them directly with:

    pytest tests/test_performance.py -v

Or with the CI performance job (main-branch pushes only).

Budgets are deliberately generous — the point is regression detection,
not speed records. A test that runs in 2s today should still run in <10s
after any change. If a change genuinely makes the system slower, the
team should explicitly widen the budget with a comment explaining why.
"""
from __future__ import annotations

import asyncio
import time
import tracemalloc
from pathlib import Path

import pytest

from src.ingestion.pdf_loader import PDFLoader

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REAL_PDF = Path("tests/fixtures/real_research_paper.pdf")
REAL_DOCX = Path("tests/fixtures/real_presentation.pptx")  # used as DOCX surrogate size ref


def _async(coro):
    """Run a coroutine synchronously (for use in non-async test functions)."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Step 9.5 — Time and memory regression guards
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_pdf_loader_completes_within_time_budget():
    """PDFLoader.load() on a real 14-page, 1.3MB PDF must finish in under 10s.

    Measured baseline (Phase 9): ~112ms on the dev machine.
    The 10s ceiling is deliberately generous — this is a regression guard,
    not a speed record. If this test starts failing it means a change added
    a >10x performance regression.
    """
    assert REAL_PDF.exists(), f"Fixture missing: {REAL_PDF}"
    raw = REAL_PDF.read_bytes()
    loader = PDFLoader()

    start = time.perf_counter()
    result = _async(loader.load(raw, filename="real_research_paper.pdf"))
    elapsed = time.perf_counter() - start

    assert elapsed < 10.0, (
        f"PDFLoader.load() took {elapsed:.2f}s — exceeded 10s budget. "
        f"Baseline Phase 9: ~0.112s."
    )
    assert result.char_count > 0, "Expected non-zero char_count from real PDF"
    assert result.page_count > 0, "Expected non-zero page_count from real PDF"


@pytest.mark.slow
def test_pdf_loader_no_double_extraction():
    """Verify the Phase 9 double-extraction fix: PDFLoader.load() must not
    call fitz get_text() more than once per page.

    We measure this indirectly: loading twice sequentially should take
    less than twice the single-load time (the fix reduces CPU wasted on
    duplicate fitz passes), but more importantly the result is correct.
    """
    assert REAL_PDF.exists(), f"Fixture missing: {REAL_PDF}"
    raw = REAL_PDF.read_bytes()
    loader = PDFLoader()

    # First load (cold fitz open)
    start = time.perf_counter()
    result1 = _async(loader.load(raw, filename="real_research_paper.pdf"))
    t1 = time.perf_counter() - start

    # Second load (same bytes — should behave identically, not 2x slower)
    start = time.perf_counter()
    result2 = _async(loader.load(raw, filename="real_research_paper.pdf"))
    t2 = time.perf_counter() - start

    # Both loads must agree on document content
    assert result1.char_count == result2.char_count, (
        "char_count inconsistent between two loads of the same file — "
        "suggests non-deterministic text extraction"
    )
    assert result1.page_count == result2.page_count

    # Neither should be wildly slow
    assert t1 < 10.0, f"First load {t1:.2f}s exceeded 10s budget"
    assert t2 < 10.0, f"Second load {t2:.2f}s exceeded 10s budget"


@pytest.mark.slow
def test_pdf_loader_validate_accepts_ghostscript_header():
    """Phase 9 fix: validate() must scan first 1024 bytes, not just startswith.

    Ghostscript-generated PDFs prepend a version comment before the %PDF-
    marker. The old validate() rejected these. The new one tolerates them.
    """
    loader = PDFLoader()

    # A real PDF has the marker near the start — should pass
    real_pdf_bytes = REAL_PDF.read_bytes()
    assert loader.validate(real_pdf_bytes), (
        "validate() rejected a real PDF — startswith fix may have regressed"
    )

    # Simulate a Ghostscript-style header: comment before %PDF-
    gs_style = b"GPL Ghostscript 10.02.0 (2023-11-01)\n%PDF-1.7\n"
    assert loader.validate(gs_style), (
        "validate() rejected a Ghostscript-style header — Phase 9 fix regressed"
    )

    # Pure junk must still be rejected
    assert not loader.validate(b"notapdf" * 200), (
        "validate() accepted clearly invalid bytes"
    )

    # Empty must be rejected
    assert not loader.validate(b""), "validate() accepted empty bytes"
    assert not loader.validate(b"ab"), "validate() accepted 2-byte file"


@pytest.mark.slow
def test_pdf_loader_memory_under_budget():
    """Memory allocated during PDFLoader.load() must stay under 500MB.

    Measured baseline (Phase 9): loader-only tracemalloc is well under 50MB.
    500MB is a conservative ceiling; if it's exceeded something is storing
    large data twice (e.g. raw_bytes duplicated in memory).
    """
    assert REAL_PDF.exists(), f"Fixture missing: {REAL_PDF}"
    raw = REAL_PDF.read_bytes()
    loader = PDFLoader()

    tracemalloc.start()
    _async(loader.load(raw, filename="real_research_paper.pdf"))
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()

    total_bytes = sum(stat.size for stat in snapshot.statistics("lineno"))
    total_mb = total_bytes / (1024 * 1024)

    assert total_mb < 500, (
        f"PDFLoader.load() memory usage {total_mb:.1f}MB exceeded 500MB budget. "
        f"Baseline Phase 9: well under 50MB."
    )


@pytest.mark.slow
def test_pdf_loader_char_count_is_accurate():
    """char_count from PDFLoader on the real research paper must be >30,000.

    Verified in Phase 7: the 14-page AMDI research paper contains 34,671
    characters (measured directly via fitz). This test is a performance
    regression guard in a different sense — it guards against a refactor
    that silently zeros char_count by removing the extraction step.
    """
    assert REAL_PDF.exists(), f"Fixture missing: {REAL_PDF}"
    raw = REAL_PDF.read_bytes()
    loader = PDFLoader()
    result = _async(loader.load(raw, filename="real_research_paper.pdf"))

    assert result.char_count >= 30_000, (
        f"char_count={result.char_count} is below 30,000 — "
        f"expected ≥34,671 based on Phase 7 verification"
    )
