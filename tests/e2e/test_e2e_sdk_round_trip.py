"""The Python SDK wraps the same wire format the server emits."""

from __future__ import annotations

import threading
from concurrent import futures

import grpc
import pytest

# Generated stub is required in CI; if missing, skip with a clear reason.
gr = pytest.importorskip("amdi_proto", reason="run `make protos` first")


@pytest.fixture(scope="module")
def server():
    from amdi_proto import amdi_pb2, amdi_pb2_grpc

    class _Stub(amdi_pb2_grpc.DocumentIntelligenceServicer):
        def Health(self, request, context):
            return amdi_pb2.HealthResponse(
                serving_state=amdi_pb2.HealthResponse.SERVING,
                version="test",
            )

    s = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    amdi_pb2_grpc.add_DocumentIntelligenceServicer_to_server(_Stub(), s)
    port = s.add_insecure_port("localhost:0")
    s.start()
    try:
        yield f"localhost:{port}"
    finally:
        s.stop(0)


def test_sdk_health(server):
    from amdi_sdk import AmdiClient   # type: ignore[import-not-found]
    c = AmdiClient(target=server)
    h = c.health()
    assert h.version == "test"
    c.close()
