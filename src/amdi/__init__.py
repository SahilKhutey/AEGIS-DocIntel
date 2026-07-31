# ─────────────────────────────────────────────────────────────────────────────
# AEGIS-DocIntel / AMDI-OS
# Adaptive Mathematical Document Intelligence Operating System
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from amdi.core import __doc__ as _pkg_doc  # noqa: F401
from amdi.version import __version__

__all__ = ["__version__", "__doc__"]

# Top-level package docstring is set in amdi.core to avoid cycle on cold import.
try:
    from amdi import core as _core  # noqa: F401
    __doc__ = getattr(_core, "__doc__", __doc__) or __doc__
except Exception:  # pragma: no cover — partial install tolerance
    pass

VERSION_INFO = tuple(int(p) for p in __version__.split(".") if p.isdigit())
