#!/usr/bin/env python3
"""Print every HTTP operation of the live app: METHOD PATH -> handler. Flags (method,path) collisions."""
from __future__ import annotations

import logging
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.CRITICAL)

from src.api.route_inspect import iter_operations  # noqa: E402
from src.main import app  # noqa: E402

seen: dict[tuple[str, str], list[str]] = defaultdict(list)
for method, path, handler in iter_operations(app.routes):
    seen[(method, path)].append(handler)

for (method, path), handlers in sorted(seen.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    flag = "  <-- COLLISION (first wins)" if len(handlers) > 1 else ""
    print(f"{method:<7}{path:<52}{' | '.join(handlers)}{flag}")
dups = sum(1 for h in seen.values() if len(h) > 1)
print(f"\n{sum(len(h) for h in seen.values())} operations, {len(seen)} unique (method,path), {dups} collision(s)")
sys.exit(0)
