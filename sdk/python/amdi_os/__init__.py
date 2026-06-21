"""
AMDI-OS Python SDK
==================

Official Python client for AMDI-OS.

Usage:
    from amdi_os import AmdiClient

    client = AmdiClient(api_key="your-key", base_url="https://amdi.example.com")

    # Upload document
    doc = client.documents.upload("path/to/file.pdf")

    # Query
    result = client.retrieval.search(
        query="What is quantum entanglement?",
        top_k=10,
    )

    # Send to AI agent
    response = client.agents.claude.send_ueo(
        ueo=result.ueo,
        question="Summarize key findings.",
    )
"""

from .client import AmdiClient
from .async_client import AsyncAmdiClient
from .models import (
    Document,
    DocumentSummary,
    RetrievalResult,
    UniversalExportObject,
    ConnectorResponse,
    VerificationReport,
    EngineOutput,
)
from .exceptions import (
    AmdiError,
    AmdiAuthError,
    AmdiNotFoundError,
    AmdiRateLimitError,
    AmdiValidationError,
    AmdiServerError,
)

__version__ = "1.0.0"
__all__ = [
    "AmdiClient",
    "AsyncAmdiClient",
    "Document",
    "DocumentSummary",
    "RetrievalResult",
    "UniversalExportObject",
    "ConnectorResponse",
    "VerificationReport",
    "EngineOutput",
    "AmdiError",
    "AmdiAuthError",
    "AmdiNotFoundError",
    "AmdiRateLimitError",
    "AmdiValidationError",
    "AmdiServerError",
]
