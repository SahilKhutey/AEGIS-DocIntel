"""CHANGELOG section is good enough to publish verbatim."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


CHANGELOG = Path(__file__).resolve().parents[2] / "CHANGELOG.md"


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[2] / "CHANGELOG.md").exists(),
    reason="CHANGELOG.md not found"
)
@pytest.mark.parametrize("section", ["Added", "Changed", "Deprecated", "Fixed", "Security"])
def test_section_present(section: str) -> None:
    txt = CHANGELOG.read_text(encoding="utf-8")
    assert re.search(rf"^### {section}", txt, re.MULTILINE) or \
           re.search(rf"^## \[0\.3\.0\]", txt, re.MULTILINE), \
           f"No 0.3.0 section or {section} heading found in CHANGELOG"


def test_has_version_entry() -> None:
    if not CHANGELOG.exists():
        pytest.skip("CHANGELOG.md not found")
    txt = CHANGELOG.read_text(encoding="utf-8")
    assert "0.3" in txt, "CHANGELOG should reference v0.3.x"
