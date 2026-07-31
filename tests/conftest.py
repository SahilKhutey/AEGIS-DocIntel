"""Root conftest for pytest: adds project root to sys.path."""

from __future__ import annotations

import sys
from pathlib import Path

root = str(Path(__file__).parents[1])
if root not in sys.path:
    sys.path.insert(0, root)

gen = Path(root) / "sdks" / "python" / "src" / "amdi_sdk" / "proto"
if gen.exists() and str(gen) not in sys.path:
    sys.path.insert(0, str(gen))

sdk_src = Path(root) / "sdks" / "python" / "src"
if sdk_src.exists() and str(sdk_src) not in sys.path:
    sys.path.insert(0, str(sdk_src))

