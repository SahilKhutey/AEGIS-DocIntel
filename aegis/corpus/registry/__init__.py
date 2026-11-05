"""
aegis.corpus.registry
=====================
Source, licence, and acquisition registries for corpus governance.
"""
from .source_registry import SourceRegistry
from .licence_registry import LicenceRegistry
from .acquisition_registry import AcquisitionRegistry

__all__ = ["SourceRegistry", "LicenceRegistry", "AcquisitionRegistry"]
