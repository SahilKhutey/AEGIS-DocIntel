'''
AEGIS-AEL — Universal Export Object (UEO)
============================================
The universal language between AMDI-OS and any AI agent.
'''
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ExportFormat(str, Enum):
    JSON = 'json'
    MARKDOWN = 'markdown'
    YAML = 'yaml'
    XML = 'xml'
    HTML = 'html'
    AGENT_NATIVE = 'agent_native'


class PriorityLevel(str, Enum):
    CRITICAL = 'critical'   # Must include
    HIGH = 'high'           # Include if budget allows
    MEDIUM = 'medium'       # Include if efficient
    LOW = 'low'             # Optional


@dataclass
class Metadata:
    document_name: str
    pages: int
    language: str
    document_type: str
    doc_id: str
    total_elements: int
    total_tables: int
    total_templates: int
    export_timestamp: float = field(default_factory=time.time)
    amdi_version: str = '1.0.0'


@dataclass
class DocumentSummary:
    title: str
    abstract: str
    key_topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    entities: list[dict] = field(default_factory=list)  # [{text, type, page}]
    sections: list[dict] = field(default_factory=list)  # [{name, page, level}]


@dataclass
class SemanticLayer:
    topics: list[dict] = field(default_factory=list)        # [{name, relevance, pages}]
    keywords: list[dict] = field(default_factory=list)      # [{term, weight, frequency}]
    entities: list[dict] = field(default_factory=list)      # [{text, type, page}]
    sentiment: dict = field(default_factory=dict)            # {positive, neutral, negative}


@dataclass
class GeometryLayer:
    important_regions: list[dict] = field(default_factory=list)  # [{page, bbox, content, importance}]
    section_locations: list[dict] = field(default_factory=list)  # [{name, page, bbox}]


@dataclass
class MatrixLayer:
    '''Tables with pre-computed metrics — never raw text.'''
    tables: list[dict] = field(default_factory=list)  # see TableExport
    n_tables: int = 0


@dataclass
class TableExport:
    name: str
    page: int
    headers: list[str]
    data: list[list[Any]]
    shape: tuple[int, int]
    computed_metrics: dict = field(default_factory=dict)  # {sum, mean, growth, ...}
    element_id: str = ''

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'page': self.page,
            'headers': self.headers,
            'data': self.data,
            'shape': list(self.shape),
            'computed_metrics': self.computed_metrics,
            'element_id': self.element_id,
        }


@dataclass
class GraphLayer:
    nodes: list[dict] = field(default_factory=list)        # [{id, type, content, page}]
    edges: list[dict] = field(default_factory=list)        # [{src, dst, type, weight}]
    n_nodes: int = 0
    n_edges: int = 0
    key_relationships: list[dict] = field(default_factory=list)


@dataclass
class TemplateLayer:
    templates: list[dict] = field(default_factory=list)  # [{id, pages, composition}]
    n_templates: int = 0
    dominant_template_id: str = ''


from src.models.context_object import Citation


@dataclass
class KeyPoint:
    text: str
    page: int
    section: str | None
    importance: float
    citations: list[Citation] = field(default_factory=list)


@dataclass
class Confidence:
    overall: float
    semantic: float
    numerical: float
    structural: float
    retrieval: float
    calibration_method: str = 'bayesian'


from src.export.universal_exporter import UniversalExportObject
