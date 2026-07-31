"""Capture environment versions for the published benchmark report."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import importlib.metadata as md


def main() -> int:
    out = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {},
    }
    for name in ("amdi", "ragas", "deepeval", "sentence-transformers",
                 "faiss-cpu", "rank-bm25", "pymupdf", "fastapi"):
        try:
            out["packages"][name] = md.version(name)
        except md.PackageNotFoundError:
            out["packages"][name] = "not installed"
    out_file = Path("benchmarks/results/env.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
