"""Version resolution: prefer VCS (hatch_vcs), fall back to static."""

from __future__ import annotations

try:
    from amdi._version import __version__  # produced by hatch-vcs at build time
except Exception:  # pragma: no cover — source checkout without build step
    __version__: str = "0.2.0.dev0"

__all__ = ["__version__"]
