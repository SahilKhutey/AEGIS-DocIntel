"""gRPC transport for AEGIS-DocIntel.

One canonical contract in `proto/amdi.proto` is compiled into four SDKs.
This package wires that contract to:

* A standalone gRPC server (`grpc_server.py`)
* Auth + logging interceptors (`grpc_interceptors.py`)
* Async + sync clients (`client.py`)
* A REST ↔ gRPC adapter that lets the FastAPI HTTP surface keep working
  unchanged (`http_bridge.py`)
"""
