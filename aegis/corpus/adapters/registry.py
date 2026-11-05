"""
aegis.corpus.adapters.registry
==============================
Registry and auto-detection factory for dataset adapters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from aegis.corpus.adapters.base import DatasetAdapter
from aegis.corpus.adapters.cord import CORDAdapter
from aegis.corpus.adapters.custom_json import CustomJSONAdapter
from aegis.corpus.adapters.docvqa import DocVQAAdapter
from aegis.corpus.adapters.funsd import FUNSDAdapter
from aegis.corpus.adapters.generic_pdf import GenericPDFAdapter
from aegis.corpus.adapters.publaynet import PubLayNetAdapter


class AdapterRegistry:
    """Registry maintaining active dataset adapters and resolving them by name or file path."""

    _registry: Dict[str, Type[DatasetAdapter]] = {
        "docvqa": DocVQAAdapter,
        "funsd": FUNSDAdapter,
        "cord": CORDAdapter,
        "publaynet": PubLayNetAdapter,
        "generic_pdf": GenericPDFAdapter,
        "pdf": GenericPDFAdapter,
        "custom_json": CustomJSONAdapter,
        "json": CustomJSONAdapter,
    }

    @classmethod
    def register(cls, name: str, adapter_cls: Type[DatasetAdapter]) -> None:
        """Register a new adapter class."""
        cls._registry[name.lower()] = adapter_cls

    @classmethod
    def get_adapter(cls, name: str) -> Optional[DatasetAdapter]:
        """Get an instantiated adapter by registered name."""
        adapter_cls = cls._registry.get(name.lower())
        if adapter_cls:
            return adapter_cls()
        return None

    @classmethod
    def list_adapters(cls) -> List[str]:
        """List registered adapter names."""
        return sorted(list(cls._registry.keys()))

    @classmethod
    def detect_adapter(cls, path: Union[str, Path]) -> Optional[DatasetAdapter]:
        """Auto-detect the appropriate adapter for a given dataset file or directory."""
        path = Path(path)
        # Order of checks: specific formats first, then generic fallbacks
        priority_order = [
            PubLayNetAdapter,
            FUNSDAdapter,
            CORDAdapter,
            DocVQAAdapter,
            GenericPDFAdapter,
            CustomJSONAdapter,
        ]

        for adapter_cls in priority_order:
            adapter = adapter_cls()
            if adapter.validate_source(path):
                return adapter
        return None
