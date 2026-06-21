"""
layout_detector.py
==================
AEGIS-AMDI-OS  |  Engine Layer  |  Layout Analysis

Provides :class:`LayoutDetector`, which enriches a
:class:`~src.core.normalized_document.NormalizedDocument` with structural
annotations:

* **Reading order** – blocks are sorted by (y₀, x₀), taking multi-column
  layouts into account.
* **Section assignment** – each block's ``.section`` attribute is set to the
  text of the most recently seen TITLE or SUBTITLE heading.
* **Heading level** – TITLE / SUBTITLE blocks are assigned ``.level``
  1 / 2 / 3 based on their bounding-box height as a font-size proxy.
* **Column count** – a per-page column estimate is stored in
  ``page.metadata["column_count"]``.

All operations are purely structural (no ML inference).  The class is
designed to run *after* the parser and OCR engines in the AMDI-OS pipeline.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
from src.core.normalized_document import (
    BlockType,
    NormalizedBlock,
    NormalizedDocument,
    NormalizedPage,
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
_COLUMN_CLUSTER_GAP: float = 0.15
"""
Fraction of page width used as minimum gap to consider two x-positions
as belonging to separate columns.  E.g. 0.15 → 15 % of page width.
"""

_HEADING_LEVEL_THRESHOLDS: Tuple[float, float] = (20.0, 14.0)
"""
BBox-height breakpoints (in points) for heading level assignment:
* height ≥ thresholds[0]  → level 1  (largest heading)
* height ≥ thresholds[1]  → level 2
* height <  thresholds[1] → level 3
"""

_HEADING_BLOCK_TYPES = frozenset({BlockType.TITLE, BlockType.SUBTITLE})


# ===========================================================================
# LayoutDetector
# ===========================================================================
class LayoutDetector:
    """
    Structural layout analyser for parsed documents.

    Parameters
    ----------
    column_gap_fraction : float
        Override for :data:`_COLUMN_CLUSTER_GAP`.
    heading_level_thresholds : tuple[float, float]
        Override for :data:`_HEADING_LEVEL_THRESHOLDS`.

    Examples
    --------
    >>> detector = LayoutDetector()
    >>> enriched_doc = await detector.analyze(normalized_doc)
    """

    def __init__(
        self,
        column_gap_fraction: float = _COLUMN_CLUSTER_GAP,
        heading_level_thresholds: Tuple[float, float] = _HEADING_LEVEL_THRESHOLDS,
    ) -> None:
        self.column_gap_fraction = column_gap_fraction
        self.heading_level_thresholds = heading_level_thresholds
        log.debug(
            "LayoutDetector initialised (col_gap=%.2f, h_thresh=%s)",
            column_gap_fraction,
            heading_level_thresholds,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(self, doc: NormalizedDocument) -> NormalizedDocument:
        """
        Enrich *doc* with layout annotations and return the result.

        Processing pipeline per page
        ----------------------------
        1. :meth:`_sort_reading_order`  – spatially order blocks
        2. :meth:`_detect_columns`      – estimate column count
        3. :meth:`_assign_levels`       – level 1/2/3 for headings
        4. :meth:`_infer_sections`      – propagate section labels

        Parameters
        ----------
        doc : NormalizedDocument

        Returns
        -------
        NormalizedDocument
            New document object with annotated pages.  The original *doc*
            is not mutated.
        """
        annotated_pages: List[NormalizedPage] = []

        for page in doc.pages:
            log.debug("Analysing layout for page %d.", page.page_index)

            # 1. Sort blocks into reading order
            ordered_page = self._sort_reading_order(page)

            # 2. Detect column count
            col_count = self._detect_columns(ordered_page)
            log.debug("Page %d: estimated %d column(s).", page.page_index, col_count)

            # 3. Assign heading levels
            levelled_page = self._assign_levels(ordered_page)

            # 4. Infer and propagate sections
            sectioned_page = self._infer_sections(levelled_page)

            # Store column count in page metadata
            meta = dict(sectioned_page.metadata or {})
            meta["column_count"] = col_count
            annotated_pages.append(
                NormalizedPage(
                    page_index=sectioned_page.page_index,
                    width=sectioned_page.width,
                    height=sectioned_page.height,
                    blocks=sectioned_page.blocks,
                    metadata=meta,
                )
            )

        return NormalizedDocument(
            source_id=doc.source_id,
            source_path=doc.source_path,
            format=doc.format,
            pages=annotated_pages,
            metadata=doc.metadata,
        )

    # ------------------------------------------------------------------
    # Reading-order sort
    # ------------------------------------------------------------------

    def _sort_reading_order(self, page: NormalizedPage) -> NormalizedPage:
        """
        Sort *page* blocks into natural reading order.

        Algorithm
        ---------
        Blocks are sorted primarily by their top-edge y₀, secondarily by
        their left-edge x₀.  This handles the common case of left-to-right,
        top-to-bottom Western text and most two-column layouts where both
        columns start at different x-positions.

        For more complex column structures, callers should further rely on
        :meth:`_detect_columns` to segment the page before re-sorting each
        column strip independently (not done here to keep complexity low).

        Parameters
        ----------
        page : NormalizedPage

        Returns
        -------
        NormalizedPage
            New page with blocks in reading order.

        Notes
        -----
        Blocks without valid bounding boxes (``None`` or zero-length tuples)
        are appended at the end, preserving their relative order.
        """
        def _sort_key(block: NormalizedBlock) -> Tuple[float, float]:
            bbox = block.bbox
            if not bbox or len(bbox) < 4:
                return (float("inf"), float("inf"))
            _x0, y0, _x1, _y1 = bbox
            return (round(y0, 1), _x0)  # round y0 to 1 dp to group near-same rows

        sorted_blocks = sorted(page.blocks, key=_sort_key)

        return NormalizedPage(
            page_index=page.page_index,
            width=page.width,
            height=page.height,
            blocks=sorted_blocks,
            metadata=page.metadata,
        )

    # ------------------------------------------------------------------
    # Column detection
    # ------------------------------------------------------------------

    def _detect_columns(self, page: NormalizedPage) -> int:
        """
        Estimate the number of text columns on a page.

        Algorithm
        ---------
        1. Collect the left-edge x₀ coordinate of every text/content block.
        2. Sort these x-values and apply 1-D single-linkage clustering using
           a gap threshold of ``column_gap_fraction × page_width``.
        3. The number of resulting clusters is the column estimate.

        Parameters
        ----------
        page : NormalizedPage

        Returns
        -------
        int
            Estimated column count (minimum 1).

        Examples
        --------
        A page with all blocks starting near x=0 → 1 column.
        A page with blocks starting near x=0 and x=300 (for a 600 pt wide
        page) → 2 columns.
        """
        if not page.blocks:
            return 1

        page_w = page.width or 600.0
        gap = self.column_gap_fraction * page_w

        x_starts: List[float] = []
        for block in page.blocks:
            bbox = block.bbox
            if not bbox or len(bbox) < 2:
                continue
            # Skip headers / footers / figures from column analysis
            if block.block_type in (BlockType.HEADER, BlockType.FOOTER, BlockType.FIGURE):
                continue
            x_starts.append(bbox[0])

        if not x_starts:
            return 1

        x_starts.sort()
        clusters = 1
        for i in range(1, len(x_starts)):
            if x_starts[i] - x_starts[i - 1] > gap:
                clusters += 1

        return clusters

    # ------------------------------------------------------------------
    # Heading level assignment
    # ------------------------------------------------------------------

    def _assign_levels(self, page: NormalizedPage) -> NormalizedPage:
        """
        Assign a hierarchical level (1, 2, or 3) to heading blocks.

        The bounding-box height (``y1 - y0``) is used as a proxy for font
        size since actual font metrics may not be available after OCR.

        Level mapping
        -------------
        * ``height >= thresholds[0]`` → **level 1** (document title)
        * ``height >= thresholds[1]`` → **level 2** (section heading)
        * ``height <  thresholds[1]`` → **level 3** (sub-section heading)

        Non-heading blocks are left unchanged (level remains ``None`` or 0).

        Parameters
        ----------
        page : NormalizedPage

        Returns
        -------
        NormalizedPage
            New page with updated block ``.level`` values.

        Notes
        -----
        When ``font_size`` is explicitly set on a block (by the PDF parser),
        it is preferred over the bbox-height heuristic.
        """
        t_large, t_medium = self.heading_level_thresholds
        updated_blocks: List[NormalizedBlock] = []

        for block in page.blocks:
            if block.block_type not in _HEADING_BLOCK_TYPES:
                updated_blocks.append(block)
                continue

            # Prefer explicit font_size if available
            size_proxy: float
            explicit_fs = getattr(block, "font_size", None)
            if explicit_fs and explicit_fs > 0:
                size_proxy = float(explicit_fs)
            else:
                bbox = block.bbox or (0, 0, 0, 0)
                size_proxy = abs(bbox[3] - bbox[1]) if len(bbox) >= 4 else 0.0

            if size_proxy >= t_large:
                level = 1
            elif size_proxy >= t_medium:
                level = 2
            else:
                level = 3

            updated_blocks.append(_clone_block_with(block, level=level))

        return NormalizedPage(
            page_index=page.page_index,
            width=page.width,
            height=page.height,
            blocks=updated_blocks,
            metadata=page.metadata,
        )

    # ------------------------------------------------------------------
    # Section inference
    # ------------------------------------------------------------------

    def _infer_sections(self, page: NormalizedPage) -> NormalizedPage:
        """
        Walk blocks top-to-bottom and propagate section labels.

        When a :attr:`BlockType.TITLE` or :attr:`BlockType.SUBTITLE` block is
        encountered its text becomes the *current section*.  All subsequent
        non-heading blocks have their ``.section`` attribute set to that
        value, until the next heading resets it.

        Parameters
        ----------
        page : NormalizedPage

        Returns
        -------
        NormalizedPage
            New page with ``.section`` populated on content blocks.

        Notes
        -----
        * HEADER and FOOTER blocks are not assigned a section label (they
          lie outside the logical body of the document).
        * If no heading has been encountered yet, ``section`` is set to
          ``"(preamble)"``.
        """
        current_section: str = "(preamble)"
        updated_blocks: List[NormalizedBlock] = []

        for block in page.blocks:
            if block.block_type in _HEADING_BLOCK_TYPES:
                current_section = (block.text or "").strip() or current_section
                updated_blocks.append(
                    _clone_block_with(block, section=current_section)
                )
            elif block.block_type in (BlockType.HEADER, BlockType.FOOTER):
                # Preserve these blocks unchanged
                updated_blocks.append(block)
            else:
                updated_blocks.append(
                    _clone_block_with(block, section=current_section)
                )

        return NormalizedPage(
            page_index=page.page_index,
            width=page.width,
            height=page.height,
            blocks=updated_blocks,
            metadata=page.metadata,
        )


# ---------------------------------------------------------------------------
# Internal utility
# ---------------------------------------------------------------------------

def _clone_block_with(block: NormalizedBlock, **overrides) -> NormalizedBlock:
    """
    Return a shallow copy of *block* with selected fields overridden.

    Parameters
    ----------
    block : NormalizedBlock
        Source block to clone.
    **overrides
        Field name → new value pairs applied on top of the clone.

    Returns
    -------
    NormalizedBlock

    Notes
    -----
    Uses ``dataclasses.replace`` when available; falls back to manual
    ``__init__`` to remain compatible with non-dataclass implementations.
    """
    try:
        import dataclasses
        if dataclasses.is_dataclass(block):
            return dataclasses.replace(block, **overrides)
    except Exception:
        pass

    # Manual copy path
    init_fields = {
        "block_type": block.block_type,
        "text": block.text,
        "bbox": block.bbox,
        "page_index": block.page_index,
        "section": getattr(block, "section", None),
        "level": getattr(block, "level", None),
        "font_size": getattr(block, "font_size", None),
        "metadata": dict(block.metadata) if getattr(block, "metadata", None) else {},
    }
    init_fields.update(overrides)
    return NormalizedBlock(**init_fields)
