"""
AEGIS-DocIntel Compliance API Routers Module
"""

from fastapi import APIRouter

from src.api.routers.compliance.privacy_requests import router as privacy_requests_router
from src.api.routers.compliance.compliance_status import router as compliance_status_router
from src.api.routers.compliance.admin_compliance import router as admin_compliance_router

compliance_router = APIRouter()
compliance_router.include_router(privacy_requests_router)
compliance_router.include_router(compliance_status_router)
compliance_router.include_router(admin_compliance_router)

__all__ = [
    "compliance_router",
    "privacy_requests_router",
    "compliance_status_router",
    "admin_compliance_router",
]
