"""Helper so generated protobuf modules are importable as amdi_proto.*."""

from __future__ import annotations

import sys
import types

try:
    from amdi_proto import amdi_pb2, amdi_pb2_grpc  # type: ignore
except ImportError:
    # Fallback to generated stubs under sdks/python if present
    try:
        from amdi_sdk.proto import amdi_pb2, amdi_pb2_grpc  # type: ignore
    except ImportError:  # pragma: no cover — in-flight dev fallback
        shim = types.ModuleType("amdi_proto")
        sys.modules.setdefault("amdi_proto", shim)
        amdi_pb2 = shim.amdi_pb2 = types.SimpleNamespace()          # type: ignore
        amdi_pb2_grpc = shim.amdi_pb2_grpc = types.SimpleNamespace()  # type: ignore

__all__ = ["amdi_pb2", "amdi_pb2_grpc"]
