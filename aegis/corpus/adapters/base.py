"""
aegis.corpus.adapters.base
==========================
Base class and interface definition for all AEGIS dataset adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from aegis.corpus.adapters.models import (
    CanonicalAnnotation,
    CanonicalDocument,
    CanonicalEvaluationItem,
    ConversionReport,
)


class DatasetAdapter(ABC):
    """Abstract base class for dataset adapters converting external formats to AEGIS canonical schema."""

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Unique identifier of the adapter."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """List of format extensions or identifier strings supported by this adapter."""
        pass

    @abstractmethod
    def validate_source(self, path: Union[str, Path]) -> bool:
        """Check whether the provided path contains valid data structure for this adapter."""
        pass

    @abstractmethod
    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        """Yield canonical documents from the source."""
        pass

    @abstractmethod
    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        """Yield canonical annotations from the source."""
        pass

    @abstractmethod
    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        """Yield canonical evaluation items from the source."""
        pass

    def convert(
        self,
        path: Union[str, Path],
        dataset_id: Optional[str] = None,
        **kwargs
    ) -> Tuple[List[CanonicalDocument], List[CanonicalAnnotation], List[CanonicalEvaluationItem], ConversionReport]:
        """Run complete extraction and return all canonical records alongside conversion metrics."""
        path = Path(path)
        ds_id = dataset_id or self.adapter_name.lower()
        report = ConversionReport(dataset_id=ds_id, adapter_name=self.adapter_name)

        docs: List[CanonicalDocument] = []
        annos: List[CanonicalAnnotation] = []
        evals: List[CanonicalEvaluationItem] = []

        try:
            if not self.validate_source(path):
                report.errors.append(f"Source validation failed for path: {path}")
                report.success = False
                return docs, annos, evals, report

            for doc in self.load_documents(path, dataset_id=ds_id, **kwargs):
                docs.append(doc)
            report.documents_converted = len(docs)

            for anno in self.load_annotations(path, dataset_id=ds_id, **kwargs):
                annos.append(anno)
            report.annotations_converted = len(annos)

            for item in self.load_evaluation_items(path, dataset_id=ds_id, **kwargs):
                evals.append(item)
            report.evaluation_items_converted = len(evals)

        except Exception as exc:
            report.errors.append(f"Extraction error: {str(exc)}")
            report.success = False

        return docs, annos, evals, report

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata regarding the adapter capabilities."""
        return {
            "adapter_name": self.adapter_name,
            "supported_formats": self.supported_formats,
            "version": "1.0.0",
        }
