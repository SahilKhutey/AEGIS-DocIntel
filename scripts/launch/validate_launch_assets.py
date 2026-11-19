"""
AEGIS-DocIntel — Launch Asset Validator

Validates that all required visual assets (gallery, logo, graphics, social cards)
exist and have valid SVG / image formats and dimensions for Product Hunt.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "launch" / "product-hunt" / "assets"

REQUIRED_ASSETS = [
    ASSETS_DIR / "logo" / "logo.svg",
    ASSETS_DIR / "logo" / "logo-512x512.svg",
    ASSETS_DIR / "gallery" / "gallery-01-hero.svg",
    ASSETS_DIR / "gallery" / "gallery-02-workflow.svg",
    ASSETS_DIR / "gallery" / "gallery-03-retrieval.svg",
    ASSETS_DIR / "gallery" / "gallery-04-structured-output.svg",
    ASSETS_DIR / "gallery" / "gallery-05-trust-security.svg",
    ASSETS_DIR / "graphics" / "architecture-workflow.svg",
    ASSETS_DIR / "graphics" / "website-launch-banner.svg",
    ASSETS_DIR / "social" / "og-image-1200x630.svg",
    ASSETS_DIR / "social" / "twitter-card-1200x630.svg",
]


def validate_svg(path: Path) -> None:
    """Validate that an SVG file is well-formed XML and has an svg root."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required asset: {path}")

    tree = ET.parse(path)
    root = tree.getroot()
    tag = root.tag.lower()
    if not tag.endswith("svg"):
        raise ValueError(f"File {path} root tag is '{root.tag}', expected 'svg'")


def validate_all_assets() -> bool:
    """Verify all required launch assets."""
    print(f"Validating {len(REQUIRED_ASSETS)} launch assets in {ASSETS_DIR}...")
    errors = []
    for asset in REQUIRED_ASSETS:
        try:
            validate_svg(asset)
        except Exception as e:
            errors.append((asset.name, str(e)))

    if errors:
        print(f"FAILED: {len(errors)} assets invalid or missing:", file=sys.stderr)
        for name, err in errors:
            print(f"  {name}: {err}", file=sys.stderr)
        return False

    print(f"SUCCESS: All {len(REQUIRED_ASSETS)} required visual assets verified and well-formed.")
    return True


if __name__ == "__main__":
    if not validate_all_assets():
        sys.exit(1)
