"""
AEGIS-DocIntel Evaluation API Routers Module (PROT-FINAL-02)
Aggregates all evaluation endpoints into a unified router.
"""

from fastapi import APIRouter

from .activation import router as activation_router
from .licenses import router as licenses_router
from .sessions import router as sessions_router
from .devices import router as devices_router
from .entitlements import router as entitlements_router
from .usage import router as usage_router

evaluation_router = APIRouter()
evaluation_router.include_router(activation_router)
evaluation_router.include_router(licenses_router)
evaluation_router.include_router(sessions_router)
evaluation_router.include_router(devices_router)
evaluation_router.include_router(entitlements_router)
evaluation_router.include_router(usage_router)

__all__ = [
    "evaluation_router",
    "activation_router",
    "licenses_router",
    "sessions_router",
    "devices_router",
    "entitlements_router",
    "usage_router",
]
