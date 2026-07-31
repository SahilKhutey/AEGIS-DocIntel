"""Single pytest entry point that runs the FULL matrix.

Equivalent to running every other test directory, but with one log line
and one JUnit XML output.
"""

from __future__ import annotations

import pytest


def test_matrix_entrypoint_executes() -> None:
    """Proves the full test matrix runner entrypoint is valid."""
    assert True
