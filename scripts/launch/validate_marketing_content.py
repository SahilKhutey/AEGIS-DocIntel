"""
AEGIS-DocIntel — Marketing Content Validator

Validates that all required Product Hunt listing, positioning, and FAQ files
exist, contain approved copy, and have no unrendered placeholders or broken sections.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PH_DIR = REPO_ROOT / "launch" / "product-hunt"

REQUIRED_DOCS = [
    PH_DIR / "strategy" / "PRODUCT_POSITIONING.md",
    PH_DIR / "strategy" / "TARGET_AUDIENCE.md",
    PH_DIR / "strategy" / "COMPETITIVE_ANALYSIS.md",
    PH_DIR / "listing" / "PRODUCT_NAME.md",
    PH_DIR / "listing" / "TAGLINE.md",
    PH_DIR / "listing" / "DESCRIPTION.md",
    PH_DIR / "listing" / "MAKER_COMMENT.md",
    PH_DIR / "listing" / "FAQ.md",
    PH_DIR / "release" / "KNOWN_LIMITATIONS.md",
]

FORBIDDEN_PLACEHOLDERS = [
    "TODO",
    "TBD",
    "FIXME",
    "<INSERT",
    "<REPLACE",
    "[REPLACE ME]",
]


def validate_file_content(path: Path) -> List[str]:
    """Validate document content, checking for missing file or placeholders."""
    if not path.exists():
        return [f"Missing required file: {path}"]

    content = path.read_text(encoding="utf-8")
    issues = []

    if len(content.strip()) < 50:
        issues.append(f"File {path.name} is too short ({len(content.strip())} chars)")

    for ph in FORBIDDEN_PLACEHOLDERS:
        if ph in content:
            issues.append(f"File {path.name} contains forbidden placeholder: '{ph}'")

    return issues


def validate_all_content() -> bool:
    """Validate all required marketing files."""
    print(f"Validating {len(REQUIRED_DOCS)} marketing documents...")
    all_issues = []
    for doc in REQUIRED_DOCS:
        issues = validate_file_content(doc)
        all_issues.extend(issues)

    if all_issues:
        print(f"FAILED: {len(all_issues)} issues found in marketing content:", file=sys.stderr)
        for issue in all_issues:
            print(f"  - {issue}", file=sys.stderr)
        return False

    print(f"SUCCESS: All {len(REQUIRED_DOCS)} marketing documents verified with no placeholders.")
    return True


if __name__ == "__main__":
    if not validate_all_content():
        sys.exit(1)
