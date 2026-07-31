"""Schema guard for the demo reel manifest.

If the trace shape changes (renamed key, new mandatory field), this
script fails CI early instead of letting the golden-trace test fail
with a confusing diff.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = {
    "task_id", "backend", "started_at", "finished_at",
    "total_ms", "seed_corpus", "ingest", "retrieval",
    "export", "agents", "assertions",
}


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 \
        else Path("benchmarks/results/reel.manifest.json")
    if not target.exists():
        print(f"· no manifest at {target}; skipping.")
        return 0
    data = json.loads(target.read_text(encoding="utf-8"))
    missing = REQUIRED - data.keys()
    if missing:
        print(f"✗ manifest missing keys: {missing}")
        return 1
    print("✓ manifest shape OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
