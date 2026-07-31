"""Drive the gRPC server in-process; verify every method round-trips."""

from __future__ import annotations

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

from amdi.config import get_settings
from amdi.transport.grpc_server import make_server
from amdi_sdk.proto import amdi_pb2, amdi_pb2_grpc


@pytest.fixture(scope="module")
def target():
    get_settings.cache_clear()
    server = make_server(port=50061)
    server.start()
    target_addr = "localhost:50061"
    try:
        yield target_addr
    finally:
        server.stop(grace=0)


def test_health_call(target) -> None:
    channel = grpc.insecure_channel(target)
    stub = amdi_pb2_grpc.DocumentIntelligenceStub(channel)
    resp = stub.Health(amdi_pb2.HealthRequest())
    assert resp.serving_state == amdi_pb2.HealthResponse.SERVING
    channel.close()
