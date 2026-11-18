"""
AEGIS-DocIntel Compliance Repositories Module
"""

from src.repositories.compliance.control_repository import ControlRepository, control_repository
from src.repositories.compliance.evidence_repository import EvidenceRepository, evidence_repository
from src.repositories.compliance.supplier_repository import SupplierRepository, supplier_repository
from src.repositories.compliance.privacy_request_repository import (
    PrivacyRequestRepository,
    privacy_request_repository,
)

__all__ = [
    "ControlRepository",
    "control_repository",
    "EvidenceRepository",
    "evidence_repository",
    "SupplierRepository",
    "supplier_repository",
    "PrivacyRequestRepository",
    "privacy_request_repository",
]
