#!/usr/bin/env python3
"""
Build-time script: fetches the cl100k_base tiktoken BPE file once (requires
network access) and copies it into src/ael/_vendor/, so production containers
never need runtime network access for tokenization.

Run this during the Docker image build (or a one-time CI job), never at
application runtime. See docs/deployment/vendoring-tiktoken.md.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

DEST = os.path.join(
    os.path.dirname(__file__), "..", "src", "ael", "_vendor", "cl100k_base.tiktoken"
)


def main() -> int:
    try:
        import tiktoken
    except ImportError:
        print("tiktoken is not installed; run `pip install tiktoken` first.", file=sys.stderr)
        return 1

    cache_dir = tempfile.mkdtemp(prefix="tiktoken_vendor_")
    os.environ["TIKTOKEN_CACHE_DIR"] = cache_dir

    try:
        tiktoken.get_encoding("cl100k_base")
    except Exception as e:
        print(f"Failed to fetch cl100k_base (network required for this one-time step): {e}", file=sys.stderr)
        return 1

    cached_files = [
        os.path.join(cache_dir, f)
        for f in os.listdir(cache_dir)
        if os.path.isfile(os.path.join(cache_dir, f))
    ]
    if not cached_files:
        print("No cached file found after fetch; tiktoken's caching layout may have changed.", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    shutil.copy(cached_files[0], DEST)
    print(f"Vendored cl100k_base encoding to {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
