"""
AMDI-OS — Normalized Document
==============================
Output of Layer 2 (Document Normalization).
Feeds all representation engines.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class BlockType(str, Enum):
    TEXT     = "text"
    TABLE    = "table"
    FIGURE   = "figure"
    EQUATION = "equation"
    HEADER   = "header"
    FOOTER   = "footer"
    CAPTION  = "caption"
    LIST     = "list"
    TITLE    = "title"
    SUBTITLE = "subtitle"
    CODE     = "code"


@dataclass(frozen=True)
class BoundingBox:
    x0: float; y0: float; x1: float; y1: float
    rotation: float = 0.0

    @property
    def width(self) -> float: return self.x1 - self.x0
    @property
    def height(self) -> float: return self.y1 - self.y0
    @property
    def area(self) -> float: return max(0., self.width) * max(0., self.height)
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)


@dataclass(init=False)
class NormalizedBlock:
    block_id:   str
    type:       BlockType
    text:       str
    bbox:       Optional[Any]
    page:       int
    confidence: float
    language:   str
    section:    Optional[str]
    level:      int
    metadata:   dict[str, Any]
    image_data: Optional[bytes]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        names = ["block_id", "type", "text", "bbox", "page", "confidence", "language", "section", "level", "metadata", "image_data"]
        for i, val in enumerate(args):
            kwargs[names[i]] = val
            
        self.block_id = kwargs.get("block_id", str(uuid.uuid4()))
        self.type = kwargs.get("type", kwargs.get("block_type", BlockType.TEXT))
        self.text = kwargs.get("text", "")
        self.bbox = kwargs.get("bbox", None)
        self.page = kwargs.get("page", kwargs.get("page_index", 0))
        self.confidence = kwargs.get("confidence", 1.0)
        self.language = kwargs.get("language", "en")
        self.section = kwargs.get("section", None)
        self.level = kwargs.get("level", 0)
        self.metadata = kwargs.get("metadata", {})
        self.image_data = kwargs.get("image_data", None)

    @property
    def token_count(self) -> int:
        return max(1, int(len(self.text.split()) * 1.33))

    @property
    def block_type(self) -> BlockType:
        return self.type


@dataclass(init=False)
class NormalizedPage:
    page_number: int
    width:       float
    height:      float
    blocks:      list[NormalizedBlock]
    is_scanned:  bool
    language:    str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        names = ["page_number", "width", "height", "blocks", "is_scanned", "language"]
        for i, val in enumerate(args):
            kwargs[names[i]] = val
            
        self.page_number = kwargs.get("page_number", kwargs.get("page_index", 0))
        self.width = kwargs.get("width", 612.0)
        self.height = kwargs.get("height", 792.0)
        self.blocks = kwargs.get("blocks", [])
        self.is_scanned = kwargs.get("is_scanned", False)
        self.language = kwargs.get("language", "en")

    @property
    def page_index(self) -> int:
        return self.page_number

    @page_index.setter
    def page_index(self, val: int) -> None:
        self.page_number = val

    @property
    def text(self) -> str:
        return "\n\n".join(b.text for b in self.blocks if b.text)

    @property
    def table_blocks(self) -> list[NormalizedBlock]:
        return [b for b in self.blocks if b.type == BlockType.TABLE]


@dataclass(init=False)
class NormalizedDocument:
    """
    Standard intermediate representation — format-agnostic.
    Input to the Multi-Representation Engine.
    """
    doc_id:   str
    filename: str
    pages:    list[NormalizedPage]
    language: str
    metadata: dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        names = ["doc_id", "filename", "pages", "language", "metadata"]
        for i, val in enumerate(args):
            kwargs[names[i]] = val
            
        self.doc_id = kwargs.get("doc_id", kwargs.get("source_id", str(uuid.uuid4())))
        self.filename = kwargs.get("filename", kwargs.get("source_path", ""))
        self.pages = kwargs.get("pages", [])
        self.language = kwargs.get("language", "en")
        self.metadata = kwargs.get("metadata", {})

    @property
    def total_pages(self) -> int: return len(self.pages)
    @property
    def total_blocks(self) -> int: return sum(len(p.blocks) for p in self.pages)
    @property
    def full_text(self) -> str: return "\n\n".join(p.text for p in self.pages)

    def all_blocks(self) -> list[NormalizedBlock]:
        return [b for p in self.pages for b in p.blocks]

    @property
    def blocks(self) -> list[NormalizedBlock]:
        return self.all_blocks()

    def tables(self) -> list[NormalizedBlock]:
        return [b for p in self.pages for b in p.blocks if b.type == BlockType.TABLE]

    def figures(self) -> list[NormalizedBlock]:
        return [b for p in self.pages for b in p.blocks if b.type == BlockType.FIGURE]
