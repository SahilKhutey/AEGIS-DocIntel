"""Smoke tests — exercise the SDK against an in-memory gRPC server."""

from __future__ import annotations

from concurrent import futures
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[1] / "src")
if root not in sys.path:
    sys.path.insert(0, root)

import grpc
import pytest

from amdi_sdk import AmdiClient
from amdi_sdk.proto import amdi_pb2, amdi_pb2_grpc


class _Stub(amdi_pb2_grpc.DocumentIntelligenceServicer):
    def Health(self, request, context):
        return amdi_pb2.HealthResponse(
            serving_state=amdi_pb2.HealthResponse.SERVING, version="test",
        )


@pytest.fixture(scope="module")
def server():
    s = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    amdi_pb2_grpc.add_DocumentIntelligenceServicer_to_server(_Stub(), s)
    port = s.add_insecure_port("localhost:0")
    s.start()
    try:
        yield f"localhost:{port}"
    finally:
        s.stop(0)


def test_health(server):
    client = AmdiClient(target=server)
    h = client.health()
    assert h.serving_state == amdi_pb2.HealthResponse.SERVING
    client.close()
