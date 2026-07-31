"""Transport test suite."""

from __future__ import annotations

import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
if root not in sys.path:
    sys.path.insert(0, root)
sdk_proto = str(Path(__file__).resolve().parents[2] / "sdks" / "python" / "src")
if sdk_proto not in sys.path:
    sys.path.insert(0, sdk_proto)
