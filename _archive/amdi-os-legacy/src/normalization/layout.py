'''
AEGIS-MIOS — Layout Analysis Adapter
====================================
Adapts the BaseLayoutDetector to run on single NormalizedPage objects.
'''

from __future__ import annotations

from src.core.normalized_document import NormalizedPage, BlockType, NormalizedBlock
from src.engines.layout.layout_detector import LayoutDetector as BaseLayoutDetector


class LayoutDetector:
    '''Enriches a NormalizedPage with reading order, heading levels, and section labels.'''

    def __init__(self):
        self._detector = BaseLayoutDetector()

    def analyze(self, page: NormalizedPage) -> NormalizedPage:
        '''Enrich page with layout analysis.'''
        # 1. Sort reading order
        ordered_page = self._detector._sort_reading_order(page)
        # 2. Column count
        col_count = self._detector._detect_columns(ordered_page)
        # 3. Heading levels
        levelled_page = self._detector._assign_levels(ordered_page)
        # 4. Infer sections
        sectioned_page = self._detector._infer_sections(levelled_page)

        # Add column count to metadata
        meta = dict(sectioned_page.metadata or {})
        meta['column_count'] = col_count

        return NormalizedPage(
            page_number=sectioned_page.page_number,
            width=sectioned_page.width,
            height=sectioned_page.height,
            blocks=sectioned_page.blocks,
            is_scanned=sectioned_page.is_scanned,
            language=sectioned_page.language,
            metadata=meta,
        )
