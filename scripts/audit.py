#!/usr/bin/env python3
"""
scripts/audit.py
================
Convenience script wrapper for `python -m aegis.audit`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aegis.audit.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
