"""
Tests for Work Packages PH-01, PH-02, and PH-05:
Positioning, Competitive Differentiation, and Product Hunt Listing Limits.
"""

from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LISTING_DIR = REPO_ROOT / "launch" / "product-hunt" / "listing"
STRATEGY_DIR = REPO_ROOT / "launch" / "product-hunt" / "strategy"


def test_product_name_limits():
    """Verify product name is <= 40 characters and matches canonical naming."""
    name_file = LISTING_DIR / "PRODUCT_NAME.md"
    assert name_file.exists(), "PRODUCT_NAME.md must exist"
    content = name_file.read_text(encoding="utf-8")

    match = re.search(r"Chosen Name:\*{0,2}\s*`([^`]+)`", content)
    assert match, "Chosen Name must be defined in backticks"
    product_name = match.group(1).strip()

    assert product_name == "AEGIS-DocIntel"
    assert len(product_name) <= 40, f"Product name length {len(product_name)} exceeds 40 chars"


def test_tagline_limits():
    """Verify primary and secondary taglines are <= 60 characters."""
    tagline_file = LISTING_DIR / "TAGLINE.md"
    assert tagline_file.exists(), "TAGLINE.md must exist"
    content = tagline_file.read_text(encoding="utf-8")

    # Primary tagline in bold backticks: `**`AI-powered intelligence for complex documents`**` or `**`...`**`
    match = re.search(r"\*\*`([^`]+)`\*\*", content)
    assert match, "Primary approved tagline must be highlighted"
    primary_tagline = match.group(1).strip()

    assert len(primary_tagline) <= 60, f"Tagline length {len(primary_tagline)} exceeds 60 chars"
    assert "intelligence" in primary_tagline.lower()
    assert "documents" in primary_tagline.lower()


def test_description_limits_and_capabilities():
    """Verify description is <= 500 characters and contains core capability verbs."""
    desc_file = LISTING_DIR / "DESCRIPTION.md"
    assert desc_file.exists(), "DESCRIPTION.md must exist"
    content = desc_file.read_text(encoding="utf-8")

    # Match blockquote description
    match = re.search(r"> \*\*([^\*]+)\*\*", content)
    assert match, "Primary description blockquote must exist"
    description = match.group(1).strip()

    assert len(description) <= 500, f"Description length {len(description)} exceeds 500 chars"
    assert len(description) >= 100, f"Description length {len(description)} is too brief"

    # Core capability assertions
    assert "document processing" in description.lower()
    assert "intelligent retrieval" in description.lower()
    assert "context optimization" in description.lower()
    assert "analysis" in description.lower()


def test_maker_comment_structure_and_limits():
    """Verify first Maker comment is <= 5000 characters and contains key sections."""
    comment_file = LISTING_DIR / "MAKER_COMMENT.md"
    assert comment_file.exists(), "MAKER_COMMENT.md must exist"
    content = comment_file.read_text(encoding="utf-8")

    # Check length
    assert len(content) <= 5000, f"Maker comment length {len(content)} exceeds 5000 chars"
    assert len(content) >= 800, f"Maker comment length {len(content)} is unexpectedly short"

    # Check structural elements
    assert "Hi Product Hunt" in content
    assert "Why I Built AEGIS-DocIntel" in content
    assert "Controlled Evaluation Release" in content
    assert "What I'd Love Feedback On" in content
    assert "Sahil Khutey" in content


def test_faq_comprehensiveness():
    """Verify FAQ covers privacy, licensing, quotas, and supported file formats."""
    faq_file = LISTING_DIR / "FAQ.md"
    assert faq_file.exists(), "FAQ.md must exist"
    content = faq_file.read_text(encoding="utf-8")

    questions = re.findall(r"### Q\d+:", content)
    assert len(questions) >= 8, f"Expected at least 8 FAQs, found {len(questions)}"

    # Topic coverage
    assert "training" in content.lower()
    assert "quota" in content.lower()
    assert "pdf" in content.lower()
    assert "ed25519" in content.lower()
    assert "comparison" in content.lower()


def test_product_positioning_and_target_audience():
    """Verify product positioning and ICP target audience specifications."""
    pos_file = STRATEGY_DIR / "PRODUCT_POSITIONING.md"
    aud_file = STRATEGY_DIR / "TARGET_AUDIENCE.md"
    comp_file = STRATEGY_DIR / "COMPETITIVE_ANALYSIS.md"

    assert pos_file.exists()
    assert aud_file.exists()
    assert comp_file.exists()

    pos_content = pos_file.read_text(encoding="utf-8")
    assert "Turn complex documents into structured intelligence" in pos_content
    assert "Kahn's DAG" in pos_content
    assert "Submodular knapsack" in pos_content

    aud_content = aud_file.read_text(encoding="utf-8")
    assert "Researchers & Academics" in aud_content
    assert "Analysts & Knowledge Workers" in aud_content
    assert "Developers & Technical Teams" in aud_content
