"""
AEGIS-DocIntel Compliance Services Module
"""

from src.services.compliance.control_register_service import (
    ControlRegisterService,
    control_register_service,
)
from src.services.compliance.evidence_service import (
    EvidenceService,
    evidence_service,
)
from src.services.compliance.supplier_assessment_service import (
    SupplierAssessmentService,
    supplier_assessment_service,
)
from src.services.compliance.privacy_request_service import (
    PrivacyRequestService,
    PrivacyAccessDenied,
    privacy_request_service,
)
from src.services.compliance.policy_version_service import (
    PolicyVersionService,
    policy_version_service,
)
from src.services.compliance.compliance_reporting_service import (
    ComplianceReportingService,
    compliance_reporting_service,
)

__all__ = [
    "ControlRegisterService",
    "control_register_service",
    "EvidenceService",
    "evidence_service",
    "SupplierAssessmentService",
    "supplier_assessment_service",
    "PrivacyRequestService",
    "PrivacyAccessDenied",
    "privacy_request_service",
    "PolicyVersionService",
    "policy_version_service",
    "ComplianceReportingService",
    "compliance_reporting_service",
]
