"""FastAPI dependencies that surface container services."""

from __future__ import annotations

from typing import TYPE_CHECKING
from fastapi import Request

from amdi.jobs.ledger import JobLedger
from amdi.jobs.progress import ProgressBus
from amdi.services.queue import QueueClient

if TYPE_CHECKING:
    from amdi.services.container import ServiceContainer
    from amdi.retrieval.hybrid import HybridRetriever
    from amdi.retrieval.index_store import IndexStore

_container_singleton: "ServiceContainer | None" = None


def set_container(container: "ServiceContainer") -> None:
    global _container_singleton
    _container_singleton = container


def get_container(request: Request | None = None) -> "ServiceContainer":
    global _container_singleton
    if request is not None and hasattr(request.app.state, "container"):
        return request.app.state.container
    if _container_singleton is not None:
        return _container_singleton
    from amdi.config import get_settings
    from amdi.services.container import ServiceContainer
    _container_singleton = ServiceContainer(settings=get_settings())
    return _container_singleton



def get_queue(request: Request) -> QueueClient:
    return request.app.state.queue


def get_ledger(request: Request) -> JobLedger:
    return request.app.state.ledger


def get_bus(request: Request) -> ProgressBus:
    return request.app.state.bus


def get_retriever(request: Request) -> "HybridRetriever":
    return get_container(request).retriever()


def get_index_store(request: Request) -> "IndexStore":
    return get_container(request).index_store()


__all__ = [
    "get_queue", "get_ledger", "get_bus",
    "get_container", "set_container", "_container_singleton",
    "get_retriever", "get_index_store",
]
