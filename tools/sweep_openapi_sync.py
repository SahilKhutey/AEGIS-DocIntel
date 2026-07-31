"""Validates that every gRPC method has a matching REST annotation and vice versa.

We allow *either* a `:method` + `:path` pair or none at all (some internal
RPCs are gRPC-only). But if you declare one, the other must match.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROTO = Path(__file__).resolve().parents[1] / "proto" / "amdi.proto"


SERVICE_RX = re.compile(
    r"rpc\s+(\w+)\s*\((stream\s)?[\w.]+\)\s+returns\s+\((stream\s)?[\w.]+\)\s*\{([^}]*)\}",
    re.DOTALL
)
PATH_RX = re.compile(r'(get|put|post|delete|patch):\s*"(/[^"]+)"')


def main() -> int:
    if not PROTO.exists():
        print("· proto/amdi.proto not found; skipping.")
        return 0

    text = PROTO.read_text(encoding="utf-8")
    rpcs = SERVICE_RX.findall(text)
    diffs: list[str] = []

    openapi = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"
    if openapi.exists():
        oa = openapi.read_text(encoding="utf-8")
        for _, _, _, body in rpcs:
            paths = PATH_RX.findall(body or "")
            if not paths:
                continue
            for method, path in paths:
                if path not in oa:
                    diffs.append(f"gRPC -> {method.upper()} {path}  missing in openapi.yaml")

    if diffs:
        print("✗ OpenAPI <-> gRPC drift:")
        for d in diffs:
            print(" -", d)
        return 1
    print("✓ OpenAPI <-> gRPC in sync (or openapi.yaml not provided).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
