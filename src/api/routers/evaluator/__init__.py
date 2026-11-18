"""
AEGIS-DocIntel Evaluator Router Module
Aggregates profile, releases, feedback, and support routers for external evaluators.
"""

from fastapi import APIRouter

from .profile import router as profile_router
from .releases import router as releases_router
from .feedback import router as feedback_router
from .support import router as support_router

evaluator_router = APIRouter()
evaluator_router.include_router(profile_router)
evaluator_router.include_router(releases_router)
evaluator_router.include_router(feedback_router)
evaluator_router.include_router(support_router)

__all__ = [
    "evaluator_router",
    "profile_router",
    "releases_router",
    "feedback_router",
    "support_router",
]
