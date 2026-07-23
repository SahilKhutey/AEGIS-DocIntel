"""Examples of using the recurrence engine."""
import sys
from pathlib import Path
# Repository Audit follow-up: this previously pointed at the now-archived
# amdi-os/ directory, which no import in this file actually used (every
# import below is from src.*) -- the repo root is what these standalone
# scripts actually need on sys.path to resolve src.* imports when run
# directly (e.g. `python examples/matrix_usage.py`) from any working dir.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engines.recurrence import RecurrenceEngine
from src.core.geometric_element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox


def main():
    engine = RecurrenceEngine()

    # ===== Sample document =====
    elements = []
    for page in range(1, 21):
        # Header at top of every page
        elements.append(GeometricElement(
            content="ANNUAL REPORT 2024",
            page=page, type=ElementType.HEADER,
            bbox=BoundingBox(0.1, 0.02, 0.9, 0.06),
        ))
        # Logo on first 10 pages
        if page <= 10:
            elements.append(GeometricElement(
                content="company-logo.png",
                page=page, type=ElementType.FIGURE,
                bbox=BoundingBox(0.02, 0.02, 0.08, 0.06),
            ))
        # Page-specific content
        elements.append(GeometricElement(
            content=f"Section content for page {page}",
            page=page, type=ElementType.TEXT,
            bbox=BoundingBox(0.1, 0.3, 0.9, 0.5),
        ))
        # Footer with page number
        elements.append(GeometricElement(
            content=f"© 2024 Page {page}",
            page=page, type=ElementType.FOOTER,
            bbox=BoundingBox(0.1, 0.95, 0.9, 0.98),
        ))

    # ===== Detect all recurrence =====
    groups = engine.detect(elements)
    print(f"Detected {len(groups)} recurrence groups")

    # ===== Show each type =====
    print("\n=== Headers ===")
    for g in engine.get_headers():
        print(f"  {g.recurrence_id}: count={g.count}, pages={g.pages[:5]}...")
        print(f"    Compression: {g.compression_ratio():.3f} ({g.compression_ratio()*100:.1f}%)")

    print("\n=== Footers ===")
    for g in engine.get_footers():
        print(f"  {g.recurrence_id}: count={g.count}")

    print("\n=== Logos ===")
    for g in engine.get_logos():
        print(f"  {g.recurrence_id}: count={g.count}")

    print("\n=== Duplicates ===")
    for g in engine.get_duplicates():
        print(f"  {g.recurrence_id}: count={g.count}")

    # ===== Compression stats =====
    stats = engine.compression_stats()
    print("\n=== Compression Statistics ===")
    print(f"  Groups found: {stats['n_groups']}")
    print(f"  Template groups: {stats['n_template_groups']}")
    print(f"  Average compression: {stats['avg_compression']:.3f}")
    print(f"  Space saved: {stats['compression_ratio_pct']:.1f}%")
    print(f"  Bytes saved (est): {stats['estimated_storage_saved_bytes']:,}")

    # ===== Storage plan =====
    plan = engine.compress_storage(elements)
    print("\n=== Storage Plan ===")
    print(f"  Templates to store once: {len(plan['templates'])}")
    print(f"  Unique elements: {len(plan['unique_elements'])}")
    print(f"\n  Top templates by compression:")
    sorted_templates = sorted(
        plan["templates"], key=lambda t: t["compression"], reverse=False
    )
    for t in sorted_templates[:5]:
        print(f"    {t['id']}: {t['type']}, count={t['count']}, "
              f"compression={t['compression']:.3f}")

    # ===== Statistics =====
    print("\n=== Statistics ===")
    stats = engine.statistics()
    print(f"  Elements: {stats.n_elements}")
    print(f"  Groups: {stats.n_groups}")
    print(f"  Templates: {stats.n_template_groups}")
    print(f"  Dominant: {stats.n_dominant_groups}")
    print(f"  Max frequency: {stats.max_frequency}")
    print(f"  Group types: {stats.group_types}")


if __name__ == "__main__":
    main()
