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


@dataclass
class Citation:
    element_id: str
    page: int
    section: str | None
    snippet: str
    confidence: float
    bbox: list | None = None


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


@dataclass
class UniversalExportObject:
    '''
    The UEO. Universal contract between AMDI-OS and any AI agent.
    Every agent receives this; each connector formats for its native API.
    '''
    metadata: Metadata
    query: str
    document_summary: DocumentSummary
    semantic: SemanticLayer = field(default_factory=SemanticLayer)
    geometry: GeometryLayer = field(default_factory=GeometryLayer)
    matrix: MatrixLayer = field(default_factory=MatrixLayer)
    graph: GraphLayer = field(default_factory=GraphLayer)
    template: TemplateLayer = field(default_factory=TemplateLayer)
    key_points: list[KeyPoint] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    confidence: Confidence = field(default_factory=lambda: Confidence(0.0, 0.0, 0.0, 0.0, 0.0))
    ueo_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    export_format: ExportFormat = ExportFormat.JSON
    tokens_used: int = 0
    priority_log: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'ueo_id': self.ueo_id,
            'metadata': {
                'document_name': self.metadata.document_name,
                'pages': self.metadata.pages,
                'language': self.metadata.language,
                'document_type': self.metadata.document_type,
                'doc_id': self.metadata.doc_id,
                'total_elements': self.metadata.total_elements,
                'total_tables': self.metadata.total_tables,
                'total_templates': self.metadata.total_templates,
                'export_timestamp': self.metadata.export_timestamp,
                'amdi_version': self.metadata.amdi_version,
            },
            'query': self.query,
            'document_summary': {
                'title': self.document_summary.title,
                'abstract': self.document_summary.abstract,
                'key_topics': self.document_summary.key_topics,
                'keywords': self.document_summary.keywords,
                'entities': self.document_summary.entities,
                'sections': self.document_summary.sections,
            },
            'semantic': {
                'topics': self.semantic.topics,
                'keywords': self.semantic.keywords,
                'entities': self.semantic.entities,
                'sentiment': self.semantic.sentiment,
            },
            'geometry': {
                'important_regions': self.geometry.important_regions,
                'section_locations': self.geometry.section_locations,
            },
            'matrix': {
                'tables': [t if isinstance(t, dict) else t.to_dict() for t in self.matrix.tables],
                'n_tables': self.matrix.n_tables,
            },
            'graph': {
                'nodes': self.graph.nodes[:50],  # Cap for export
                'edges': self.graph.edges[:100],
                'n_nodes': self.graph.n_nodes,
                'n_edges': self.graph.n_edges,
                'key_relationships': self.graph.key_relationships,
            },
            'template': {
                'templates': self.template.templates,
                'n_templates': self.template.n_templates,
                'dominant_template_id': self.template.dominant_template_id,
            },
            'key_points': [
                {
                    'text': kp.text, 'page': kp.page, 'section': kp.section,
                    'importance': kp.importance,
                    'citations': [{'element_id': c.element_id, 'page': c.page, 'section': c.section} for c in kp.citations],
                }
                for kp in self.key_points
            ],
            'citations': [
                {
                    'element_id': c.element_id, 'page': c.page, 'section': c.section,
                    'snippet': c.snippet[:200], 'confidence': c.confidence,
                }
                for c in self.citations
            ],
            'confidence': {
                'overall': self.confidence.overall,
                'semantic': self.confidence.semantic,
                'numerical': self.confidence.numerical,
                'structural': self.confidence.structural,
                'retrieval': self.confidence.retrieval,
                'calibration_method': self.confidence.calibration_method,
            },
            'tokens_used': self.tokens_used,
        }
