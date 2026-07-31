"""FastAPI routers, organized by dashboard surface."""
from amdi.api.routers import advanced, documents, health, jobs, query  # noqa: F401

__all__ = ["health", "documents", "jobs", "query", "advanced"]
