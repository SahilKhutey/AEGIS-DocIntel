"""
aegis.processing
================
AEGIS Document Processing Pipeline: extraction, layout analysis,
reading order resolution, table reconstruction, and field-level provenance.
"""

from aegis.processing.models import (
    CoordinateSystem,
    DocumentProcessingResult,
    ExtractionBlock,
    ExtractionMethod,
    FieldProvenance,
    LayoutRegion,
    PageTextExtraction,
    ProcessingError,
    ProcessingStatus,
    ReadingOrderResult,
    RegionType,
    ResourceUsage,
    TableCellModel,
    TableReconstruction,
)
from aegis.processing.pipeline import DocumentProcessingPipeline

__all__ = [
    "DocumentProcessingPipeline",
    "DocumentProcessingResult",
    "ProcessingStatus",
    "ProcessingError",
    "PageTextExtraction",
    "ExtractionMethod",
    "ExtractionBlock",
    "LayoutRegion",
    "RegionType",
    "CoordinateSystem",
    "ReadingOrderResult",
    "TableReconstruction",
    "TableCellModel",
    "FieldProvenance",
    "ResourceUsage",
]
