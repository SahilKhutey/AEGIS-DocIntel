"""
aegis.processing.tables.detector
================================
Table extraction and structural grid reconstruction from document pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import fitz

from aegis.processing.models import TableCellModel, TableReconstruction


class TableExtractor:
    """Extracts and reconstructs tabular structures from PDF pages and raw matrices."""

    @classmethod
    def extract_from_fitz_page(
        cls,
        page: fitz.Page,
        document_id: str,
        page_number: int = 1
    ) -> List[TableReconstruction]:
        """Extract tables from PyMuPDF page using native table finder."""
        reconstructions: List[TableReconstruction] = []
        try:
            tabs = page.find_tables()
            for idx, tab in enumerate(tabs.tables):
                t_bbox = [float(c) for c in tab.bbox]
                extracted_data = tab.extract()
                row_cnt = len(extracted_data)
                col_cnt = len(extracted_data[0]) if row_cnt > 0 else 0

                cells: List[TableCellModel] = []
                for r_idx, row in enumerate(extracted_data):
                    for c_idx, val in enumerate(row):
                        cell_text = str(val or "").strip()
                        # Approximate cell bounding box within table bbox
                        cell_w = (t_bbox[2] - t_bbox[0]) / max(1, col_cnt)
                        cell_h = (t_bbox[3] - t_bbox[1]) / max(1, row_cnt)
                        c_x0 = t_bbox[0] + c_idx * cell_w
                        c_y0 = t_bbox[1] + r_idx * cell_h
                        c_x1 = c_x0 + cell_w
                        c_y1 = c_y0 + cell_h

                        role = "column_header" if r_idx == 0 else ("empty" if not cell_text else "data")

                        cells.append(
                            TableCellModel(
                                cell_id=f"CELL-{page_number:02d}-{idx:02d}-{r_idx:02d}-{c_idx:02d}",
                                row_index=r_idx,
                                column_index=c_idx,
                                row_span=1,
                                column_span=1,
                                text=cell_text,
                                role=role,
                                bbox=[round(c_x0, 2), round(c_y0, 2), round(c_x1, 2), round(c_y1, 2)],
                            )
                        )

                reconstructions.append(
                    TableReconstruction(
                        table_id=f"TABLE-{page_number:03d}-{idx:03d}",
                        document_id=document_id,
                        page_number=page_number,
                        bbox=t_bbox,
                        row_count=row_cnt,
                        column_count=col_cnt,
                        cells=cells,
                        header_rows=[0] if row_cnt > 0 else [],
                        source_reference=f"{document_id}:PAGE-{page_number}:TABLE-{idx}",
                    )
                )
        except Exception:
            pass

        return reconstructions

    @classmethod
    def from_grid_data(
        cls,
        table_id: str,
        document_id: str,
        page_number: int,
        headers: List[str],
        data_rows: List[List[str]],
        bbox: Optional[List[float]] = None
    ) -> TableReconstruction:
        """Construct canonical TableReconstruction from raw row/col matrices."""
        all_rows = [headers] + data_rows
        row_cnt = len(all_rows)
        col_cnt = len(headers) if headers else (len(data_rows[0]) if data_rows else 0)
        t_bbox = bbox or [50.0, 100.0, 550.0, 100.0 + row_cnt * 25.0]

        cells: List[TableCellModel] = []
        cell_w = (t_bbox[2] - t_bbox[0]) / max(1, col_cnt)
        cell_h = (t_bbox[3] - t_bbox[1]) / max(1, row_cnt)

        for r_idx, row in enumerate(all_rows):
            for c_idx in range(col_cnt):
                val = row[c_idx] if c_idx < len(row) else ""
                c_x0 = t_bbox[0] + c_idx * cell_w
                c_y0 = t_bbox[1] + r_idx * cell_h
                role = "column_header" if r_idx == 0 else ("empty" if not val.strip() else "data")

                cells.append(
                    TableCellModel(
                        cell_id=f"CELL-{page_number:02d}-{r_idx:02d}-{c_idx:02d}",
                        row_index=r_idx,
                        column_index=c_idx,
                        row_span=1,
                        column_span=1,
                        text=str(val).strip(),
                        role=role,
                        bbox=[round(c_x0, 2), round(c_y0, 2), round(c_x0 + cell_w, 2), round(c_y0 + cell_h, 2)],
                    )
                )

        return TableReconstruction(
            table_id=table_id,
            document_id=document_id,
            page_number=page_number,
            bbox=t_bbox,
            row_count=row_cnt,
            column_count=col_cnt,
            cells=cells,
            header_rows=[0],
            source_reference=f"{document_id}:PAGE-{page_number}:{table_id}",
        )
