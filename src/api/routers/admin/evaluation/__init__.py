"""
AEGIS-DocIntel Admin Evaluation Routers Module
Aggregates evaluators, licenses, and feedback routers for operators.
"""

from fastapi import APIRouter

from .evaluators import router as evaluators_router
from .licenses import router as licenses_router
from .feedback import router as feedback_router

admin_evaluation_router = APIRouter()
admin_evaluation_router.include_router(evaluators_router)
admin_evaluation_router.include_router(licenses_router)
admin_evaluation_router.include_router(feedback_router)

__all__ = [
    "admin_evaluation_router",
    "evaluators_router",
    "licenses_router",
    "feedback_router",
]
