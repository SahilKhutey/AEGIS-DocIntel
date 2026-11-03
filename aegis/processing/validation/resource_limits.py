"""
aegis.processing.validation.resource_limits
===========================================
Resource limits configuration and enforcement guards for safe document processing.
"""

from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class ResourceLimitsConfig(BaseModel):
    max_file_size_bytes: int = 52428800  # 50 MB
    max_pages: int = 500
    max_page_dimension_points: float = 10000.0
    max_image_pixels: int = 50000000  # 50 Megapixels
    timeout_seconds: float = 45.0
    max_memory_mb: int = 1024
    allowed_mime_types: List[str] = Field(
        default_factory=lambda: ["application/pdf", "image/png", "image/jpeg", "image/tiff"]
    )
    allow_encrypted: bool = False
