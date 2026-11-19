"""
Tests for Work Packages PH-06 and PH-07:
Visual Identity, Image Dimensions, Vector Standards, and Demo Storyboard.
"""

from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ASSETS_DIR = REPO_ROOT / "launch" / "product-hunt" / "assets"


def _extract_svg_dimensions(svg_path: Path):
    """Helper to extract viewBox or width/height attributes from an SVG file."""
    assert svg_path.exists(), f"SVG asset {svg_path.name} must exist"
    content = svg_path.read_text(encoding="utf-8")

    width_match = re.search(r'width="(\d+)"', content)
    height_match = re.search(r'height="(\d+)"', content)
    viewbox_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', content)

    if width_match and height_match:
        return int(width_match.group(1)), int(height_match.group(1))
    elif viewbox_match:
        return int(viewbox_match.group(1)), int(viewbox_match.group(2))
    pytest.fail(f"Could not determine dimensions for SVG {svg_path.name}")


def test_logo_dimensions():
    """Verify product logo meets Product Hunt 512x512 standard."""
    logo_file = ASSETS_DIR / "logo" / "logo-512x512.svg"
    w, h = _extract_svg_dimensions(logo_file)
    assert (w, h) == (512, 512), f"Expected 512x512 logo, got {w}x{h}"


def test_gallery_slides_dimensions():
    """Verify all 5 Product Hunt gallery images are 1270x760 px."""
    gallery_dir = ASSETS_DIR / "gallery"
    slides = [f"gallery-0{i}-{name}.svg" for i, name in [
        (1, "hero"), (2, "workflow"), (3, "retrieval"),
        (4, "structured-output"), (5, "trust-security")
    ]]

    for slide in slides:
        slide_path = gallery_dir / slide
        assert slide_path.exists(), f"Gallery slide {slide} must exist"
        w, h = _extract_svg_dimensions(slide_path)
        assert (w, h) == (1270, 760), f"Slide {slide} dimensions {w}x{h} do not match 1270x760"


def test_architecture_and_banner_graphics():
    """Verify architecture graphic and website banner dimensions."""
    arch_path = ASSETS_DIR / "graphics" / "architecture-workflow.svg"
    banner_path = ASSETS_DIR / "graphics" / "website-launch-banner.svg"

    w_arch, h_arch = _extract_svg_dimensions(arch_path)
    assert (w_arch, h_arch) == (1270, 760), f"Architecture SVG expected 1270x760, got {w_arch}x{h_arch}"

    w_banner, h_banner = _extract_svg_dimensions(banner_path)
    assert (w_banner, h_banner) == (1200, 400), f"Banner SVG expected 1200x400, got {w_banner}x{h_banner}"


def test_social_cards_dimensions():
    """Verify OpenGraph and Twitter card assets are 1200x630 px."""
    og_path = ASSETS_DIR / "social" / "og-image-1200x630.svg"
    tw_path = ASSETS_DIR / "social" / "twitter-card-1200x630.svg"

    w_og, h_og = _extract_svg_dimensions(og_path)
    assert (w_og, h_og) == (1200, 630), f"OG image expected 1200x630, got {w_og}x{h_og}"

    w_tw, h_tw = _extract_svg_dimensions(tw_path)
    assert (w_tw, h_tw) == (1200, 630), f"Twitter card expected 1200x630, got {w_tw}x{h_tw}"


def test_demo_storyboard_exact_duration_math():
    """Verify demo storyboard duration sums to exactly 75 seconds across 6 scenes."""
    storyboard_file = ASSETS_DIR / "video" / "DEMO_STORYBOARD.md"
    assert storyboard_file.exists()
    content = storyboard_file.read_text(encoding="utf-8")

    # Match scene duration items e.g., Scene 1: The Problem (8s)
    durations = [int(m) for m in re.findall(r"Scene \d+:[^\n]+\((\d+)s\)", content)]
    assert len(durations) == 6, f"Expected 6 scene durations, found {len(durations)}: {durations}"

    total_seconds = sum(durations)
    assert total_seconds == 75, f"Storyboard total duration must be exactly 75s, got {total_seconds}s"


def test_walkthrough_script_content():
    """Verify walkthrough recording script includes audio and screen action directions."""
    script_file = ASSETS_DIR / "video" / "WALKTHROUGH_SCRIPT.md"
    assert script_file.exists()
    content = script_file.read_text(encoding="utf-8")

    assert "OBS Studio" in content
    assert "Voice:" in content
    assert "Screen:" in content
    assert "aegis_neural_hardware_spec_v2" in content
