"""Examples of using the template engine."""
import sys
from pathlib import Path
# Repository Audit follow-up: this previously pointed at the now-archived
# amdi-os/ directory, which no import in this file actually used (every
# import below is from src.*) -- the repo root is what these standalone
# scripts actually need on sys.path to resolve src.* imports when run
# directly (e.g. `python examples/matrix_usage.py`) from any working dir.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engines.template import TemplateEngine
from src.core.geometric_element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox


def main():
    engine = TemplateEngine()

    # ===== Sample document: 20-page invoice batch =====
    pages = {}
    for page in range(1, 21):
        pages[page] = [
            GeometricElement(
                content=f"INVOICE #{page:03d}",
                page=page, type=ElementType.HEADING,
                bbox=BoundingBox(0.1, 0.05, 0.5, 0.1),
            ),
            GeometricElement(
                content="ACME Corporation",
                page=page, type=ElementType.TEXT,
                bbox=BoundingBox(0.1, 0.12, 0.5, 0.17),
            ),
            GeometricElement(
                content="| Item | Qty | Unit | Total |\n|---|---|---|---|\n| Widget A | 10 | $50 | $500 |\n| Widget B | 5 | $100 | $500 |",
                page=page, type=ElementType.TABLE,
                bbox=BoundingBox(0.1, 0.3, 0.9, 0.6),
            ),
            GeometricElement(
                content=f"Page {page}",
                page=page, type=ElementType.FOOTER,
                bbox=BoundingBox(0.4, 0.95, 0.6, 0.98),
            ),
        ]

    # ===== 1. Fingerprint Generation =====
    print("=== Fingerprint Generation ===")
    fp1 = engine.generate_fingerprint(1, pages[1])
    print(f"Page 1 fingerprint:")
    print(f"  Elements: {fp1.n_elements}")
    print(f"  Types: {fp1.type_histogram}")
    print(f"  Tables: {fp1.n_tables}, Figures: {fp1.n_figures}")
    print(f"  Total area: {fp1.total_area:.3f}")
    print(f"  Text density: {fp1.text_density:.1f}")
    print(f"  Signature norm: {sum(fp1.signature**2)**0.5:.3f}")
    print(f"  Content hash: {fp1.content_hash}")

    # ===== 2. Signature Creation =====
    print("\n=== Signature Creation ===")
    print(f"Signature shape: {fp1.signature.shape}")
    print(f"Signature (first 5 dims): {fp1.signature[:5]}")

    # ===== 3. Template Clustering =====
    print("\n=== Template Clustering (DBSCAN) ===")
    templates = engine.build_templates(pages)
    print(f"Found {len(templates)} template families")

    for i, t in enumerate(templates, 1):
        print(f"\n  Template {i}: {t.template_id}")
        print(f"    Pages: {t.pages[:5]}{'...' if len(t.pages) > 5 else ''}")
        print(f"    Size: {t.cluster_size}")
        print(f"    Is template: {t.is_template}")
        print(f"    Is dominant: {t.is_dominant}")
        print(f"    Compression: {t.compression_ratio:.3f} (saves {(1-t.compression_ratio)*100:.1f}%)")
        print(f"    Composition: {t.composition}")

    # ===== 4. Duplicate Detection =====
    print("\n=== Duplicate Detection ===")
    # Exact duplicates
    exact_dupes = engine.find_exact_duplicates()
    print(f"Exact duplicate groups: {len(exact_dupes)}")
    for d in exact_dupes:
        print(f"  Group {d.group_id}: pages {d.pages} (hash: {d.content_hash})")

    # Near duplicates
    near_dupes = engine.detect_duplicates()
    print(f"Near-duplicate groups: {len(near_dupes)}")
    for d in near_dupes:
        print(f"  Group {d.group_id}: pages {d.pages}, similarities: {d.similarity_scores}")

    # ===== Dominant Templates =====
    print("\n=== Dominant Templates ===")
    dominant = engine.get_dominant_templates()
    for d in dominant:
        print(f"  {d.template_id}: {d.cluster_size} pages, "
              f"compression={d.compression_ratio:.3f}")

    # ===== Statistics =====
    print("\n=== Statistics ===")
    stats = engine.statistics()
    print(f"  Pages: {stats.n_pages}")
    print(f"  Templates: {stats.n_templates}")
    print(f"  Dominant templates: {stats.n_dominant_templates}")
    print(f"  Compression ratio: {stats.compression_ratio:.3f}")
    
    # ===== Compression Report =====
    print("\n=== Compression Report ===")
    report = engine.compression_report()
    print(f"  Overall savings: {report['overall_savings_pct']:.1f}%")


if __name__ == "__main__":
    main()
