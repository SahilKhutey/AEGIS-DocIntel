'''
AEGIS-MIOS — Shared Element Model
==================================
Re-exports the universal document element model.
'''

from __future__ import annotations

from typing import Any
from src.engines.geometry.element import ElementType, GeometricElement


def make_element(
    content: str,
    page: int,
    etype: ElementType,
    bbox: Any = None,
    section: str | None = None,
    doc_id: str = '',
) -> GeometricElement:
    '''Create a GeometricElement instance.'''
    return GeometricElement(
        content=content,
        page=page,
        type=etype,
        bbox=bbox,
        section=section,
        doc_id=doc_id,
    )
