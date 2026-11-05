"""
aegis.corpus.adapters
=====================
Package providing adapters to normalize external document datasets into
canonical AEGIS schemas (document, annotation, evaluation item).
"""

from aegis.corpus.adapters.base import DatasetAdapter
from aegis.corpus.adapters.cord import CORDAdapter
from aegis.corpus.adapters.custom_json import CustomJSONAdapter
from aegis.corpus.adapters.docvqa import DocVQAAdapter
from aegis.corpus.adapters.funsd import FUNSDAdapter
from aegis.corpus.adapters.generic_pdf import GenericPDFAdapter
from aegis.corpus.adapters.models import (
    BoundingBoxItem,
    CanonicalAnnotation,
    CanonicalDocument,
    CanonicalEvaluationItem,
    ContentInfo,
    ConversionReport,
    EvidenceSpan,
    MetadataInfo,
    RightsInfo,
)
from aegis.corpus.adapters.publaynet import PubLayNetAdapter
from aegis.corpus.adapters.registry import AdapterRegistry

__all__ = [
    "DatasetAdapter",
    "CanonicalDocument",
    "CanonicalAnnotation",
    "CanonicalEvaluationItem",
    "ConversionReport",
    "ContentInfo",
    "MetadataInfo",
    "RightsInfo",
    "BoundingBoxItem",
    "EvidenceSpan",
    "DocVQAAdapter",
    "FUNSDAdapter",
    "CORDAdapter",
    "PubLayNetAdapter",
    "GenericPDFAdapter",
    "CustomJSONAdapter",
    "AdapterRegistry",
]
