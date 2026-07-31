"""Optional adapter: lets clients that already speak REST (e.g., the FastAPI
UI) call into the same gRPC service without code duplication.
"""

from __future__ import annotations

from fastapi import FastAPI

from amdi.api.app import create_app as create_rest_app


def create_app() -> FastAPI:
    """A FastAPI app identical to the original HTTP surface."""
    return create_rest_app()


__all__ = ["create_app"]
