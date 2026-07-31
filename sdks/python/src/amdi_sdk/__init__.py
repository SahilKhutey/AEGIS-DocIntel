"""AEGIS-DocIntel Python SDK.

Two clients:

    from amdi_sdk import AmdiClient            # sync, thread-safe
    from amdi_sdk.aio import AsyncAmdiClient   # async

Both share the same proto contract (`proto/amdi.proto`).
"""

from amdi_sdk.client import AmdiClient

__all__ = ["AmdiClient"]
