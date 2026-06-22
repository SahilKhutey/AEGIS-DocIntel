"""Alias for easy importing."""
from src.engines.template.template_engine import (
    TemplateEngine, PageTemplate, PageFingerprint,
    DuplicateGroup, TemplateStats,
)

__all__ = [
    "TemplateEngine", "PageTemplate", "PageFingerprint",
    "DuplicateGroup", "TemplateStats",
]
