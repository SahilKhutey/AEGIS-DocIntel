"""Validate the sync client speaks the same wire format the server expects."""

from __future__ import annotations

from concurrent import futures
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
if root not in sys.path:
    sys.path.insert(0, root)
sdk_proto = str(Path(__file__).resolve().parents[2] / "sdks" / "python" / "src")
if sdk_proto not in sys.path:
    sys.path.insert(0, sdk_proto)

import grpc
import pytest

from amdi_sdk import AmdiClient
from amdi_sdk.proto import amdi_pb2, amdi_pb2_grpc


class _MiniServicer(amdi_pb2_grpc.DocumentIntelligenceServicer):
    def Health(self, request, context):
        return amdi_pb2.HealthResponse(
            serving_state=amdi_pb2.HealthResponse.SERVING, version="0.0.1",
        )


@pytest.fixture(scope="module")
def fake_target():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    amdi_pb2_grpc.add_DocumentIntelligenceServicer_to_server(_MiniServicer(), server)
    port = server.add_insecure_port("localhost:0")
    server.start()
    try:
        yield f"localhost:{port}"
    finally:
        server.stop(0)


def test_round_trip_health(fake_target) -> None:
    c = AmdiClient(target=fake_target)
    out = c.health()
    assert out.serving_state == amdi_pb2.HealthResponse.SERVING
    c.close()
