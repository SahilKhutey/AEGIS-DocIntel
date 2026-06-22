"""
AMDI-OS Multi-Modal Support
============================

Handles images, tables, charts, and figures alongside text.

Capabilities:
    - Image embeddings (CLIP)
    - Enhanced table extraction
    - Chart/diagram understanding
    - Figure caption generation
    - Cross-modal retrieval

Author : AMDI-OS Development Team
Version: 1.2.0
"""

from .multimodal_engine import MultiModalEngine, MultiModalOutput, Modality
from .image_embedder import ImageEmbedder, CLIPEmbedder
from .table_extractor import EnhancedTableExtractor, TableCell, TableStructure, CellType
from .chart_understander import ChartUnderstander, ChartType, ChartData
from .caption_generator import CaptionGenerator, CaptionStyle

__all__ = [
    "MultiModalEngine",
    "MultiModalOutput",
    "Modality",
    "ImageEmbedder",
    "CLIPEmbedder",
    "EnhancedTableExtractor",
    "TableCell",
    "TableStructure",
    "CellType",
    "ChartUnderstander",
    "ChartType",
    "ChartData",
    "CaptionGenerator",
    "CaptionStyle",
]

__version__ = "1.2.0"
