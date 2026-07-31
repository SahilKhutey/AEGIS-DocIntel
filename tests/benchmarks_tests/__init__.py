"""Benchmark metric tests."""

import sys
from pathlib import Path

root = str(Path(__file__).parents[2])
if root not in sys.path:
    sys.path.insert(0, root)
