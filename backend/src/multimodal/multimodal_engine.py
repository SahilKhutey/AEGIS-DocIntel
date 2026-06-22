"""
Multi-Modal Engine
===================

Orchestrates image, table, chart, and figure processing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np

from .caption_generator import CaptionGenerator, CaptionStyle
from .chart_understander import ChartData, ChartType, ChartUnderstander
from .image_embedder import CLIPEmbedder, ImageEmbedder
from .table_extractor import EnhancedTableExtractor, TableStructure


class Modality(Enum):
    """Supported modalities."""

    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"
    FIGURE = "figure"


@dataclass
class MultiModalOutput:
    """Output from multi-modal processing."""

    document_id: str
    modality: Modality
    data: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    caption: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "modality": self.modality.value,
            "data": self.data,
            "caption": self.caption,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "latency_ms": self.latency_ms,
        }


class MultiModalEngine:
    """
    Multi-modal engine that processes text + images + tables + charts.
    """

    def __init__(
        self,
        image_embedder: Optional[ImageEmbedder] = None,
        table_extractor: Optional[EnhancedTableExtractor] = None,
        chart_understander: Optional[ChartUnderstander] = None,
        caption_generator: Optional[CaptionGenerator] = None,
    ) -> None:
        self.image_embedder = image_embedder or CLIPEmbedder()
        self.table_extractor = table_extractor or EnhancedTableExtractor()
        self.chart_understander = chart_understander or ChartUnderstander()
        self.caption_generator = caption_generator or CaptionGenerator()

    def process_image(
        self,
        document_id: str,
        image_data: bytes,
        image_format: str = "png",
        generate_caption: bool = True,
    ) -> MultiModalOutput:
        """Process an image: embed + caption."""
        t0 = time.time()
        # generate embedding
        embedding = self.image_embedder.embed(image_data)
        # generate caption
        caption = None
        if generate_caption:
            caption = self.caption_generator.generate(
                image_data, style=CaptionStyle.DESCRIPTIVE
            )
        return MultiModalOutput(
            document_id=document_id,
            modality=Modality.IMAGE,
            data={"format": image_format, "size_bytes": len(image_data)},
            embedding=embedding,
            caption=caption,
            confidence=0.9 if embedding is not None else 0.0,
            latency_ms=(time.time() - t0) * 1000,
        )

    def process_table(
        self,
        document_id: str,
        table_data: List[List[str]],
        page: int = 1,
    ) -> MultiModalOutput:
        """Process a table: structure + statistics + caption."""
        t0 = time.time()
        structure = self.table_extractor.extract(table_data)
        caption = self.caption_generator.generate_table_caption(structure)
        return MultiModalOutput(
            document_id=document_id,
            modality=Modality.TABLE,
            data={
                "structure": structure.to_dict(),
                "rows": structure.row_count,
                "cols": structure.col_count,
            },
            caption=caption,
            confidence=structure.completeness,
            metadata={"page": page},
            latency_ms=(time.time() - t0) * 1000,
        )

    def process_chart(
        self,
        document_id: str,
        chart_image: bytes,
    ) -> MultiModalOutput:
        """Process a chart: detect type + extract data."""
        t0 = time.time()
        chart_data = self.chart_understander.understand(chart_image)
        caption = self.caption_generator.generate_chart_caption(chart_data)
        return MultiModalOutput(
            document_id=document_id,
            modality=Modality.CHART,
            data=chart_data.to_dict(),
            caption=caption,
            confidence=chart_data.confidence,
            latency_ms=(time.time() - t0) * 1000,
        )

    def cross_modal_search(
        self,
        query: str,
        images: List[bytes],
        top_k: int = 5,
    ) -> List[MultiModalOutput]:
        """Search images using text query (CLIP zero-shot)."""
        # encode query as text embedding
        query_embedding = self.image_embedder.embed_text(query)
        results: List[MultiModalOutput] = []
        scored: List[tuple] = []
        for i, img in enumerate(images):
            img_emb = self.image_embedder.embed(img)
            if img_emb is not None and query_embedding is not None:
                score = float(
                    np.dot(query_embedding, img_emb)
                    / (np.linalg.norm(query_embedding) * np.linalg.norm(img_emb))
                )
                scored.append((score, i, img))
        scored.sort(reverse=True)
        for score, idx, img in scored[:top_k]:
            results.append(MultiModalOutput(
                document_id=f"img_{idx}",
                modality=Modality.IMAGE,
                data={"index": idx},
                confidence=score,
            ))
        return results
