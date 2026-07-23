"""Examples of using the matrix engine."""
import sys
from pathlib import Path
# Repository Audit follow-up: this previously pointed at the now-archived
# amdi-os/ directory, which no import in this file actually used (every
# import below is from src.*) -- the repo root is what these standalone
# scripts actually need on sys.path to resolve src.* imports when run
# directly (e.g. `python examples/matrix_usage.py`) from any working dir.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engines.matrix import MatrixEngine, TableMatrix
from src.core.geometric_element import GeometricElement, ElementType


def main():
    engine = MatrixEngine()

    # ===== Sample table in markdown =====
    table_content = """| Product | Q1 Sales | Q2 Sales | Q3 Sales | Q4 Sales |
|---------|----------|----------|----------|----------|
| Alpha   | 100K     | 120K     | 150K     | 200K     |
| Beta    | 80K      | 90K      | 85K      | 110K     |
| Gamma   | 50K      | 45K      | 60K      | 70K      |"""

    element = GeometricElement(
        element_id="table-1",
        page=1,
        type=ElementType.TABLE,
        content=table_content
    )

    # ===== Detect and extract table matrix =====
    tables = engine.find_tables([element])
    print(f"Extracted {len(tables)} tables.")

    table = tables[0]
    print(f"\n=== Table Matrix Info ===")
    print(f"  Shape: {table.shape}")
    print(f"  Headers: {table.headers}")
    print(f"  Markdown format:\n{table.to_markdown()}")

    # ===== Aggregations =====
    print("\n=== Row & Column Aggregations ===")
    print(f"  Q1 Sales sum: {table.column_sum(1):,.2f}")
    print(f"  Q4 Sales mean: {table.column_mean(4):,.2f}")
    print(f"  Alpha product total (row 0 sum): {table.row_sum(0):,.2f}")

    # ===== Growth & CAGR =====
    print("\n=== Growth Analysis ===")
    print(f"  Growth of Q4 Sales from Alpha to Gamma (rows 0 to 2): {table.growth_rate_between(4, 0, 2):+.2%}")

    # Let's check growth of columns from first row (Alpha) to last row (Gamma)
    print(f"  Q1 relative growth from Alpha to Gamma: {table.growth_rate_between(1, 0, 2):+.2%}")
    # Compound growth across quarters (Q1 to Q4) for Alpha
    # Alpha sales: 100K, 120K, 150K, 200K
    # Wait, the row represents the quarters, so to calculate CAGR across columns we can transpose or compute directly
    # In table, columns 1 to 4 represent Q1-Q4. Let's see the CAGR of Q1 Sales column:
    # Q1 Sales: 100K, 80K, 50K.
    # CAGR of Q1 Sales: (50/100)^(1/2) - 1 ≈ -29.29%
    cagr_q1 = table.cagr(1)
    print(f"  CAGR of Q1 Sales (across products): {cagr_q1 * 100:.2f}%" if cagr_q1 is not None else "  CAGR of Q1 Sales: N/A")

    # ===== Correlation =====
    print("\n=== Correlation Analysis ===")
    pearson = table.correlation(1, 2, method="pearson")
    spearman = table.correlation(1, 2, method="spearman")
    print(f"  Pearson corr between Q1 and Q2: {pearson:.4f}")
    print(f"  Spearman corr between Q1 and Q2: {spearman:.4f}")

    # ===== Matrix Summary =====
    stats = table.statistics()
    print("\n=== Statistical Summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # ===== Natural Language Queries =====
    print("\n=== Natural Language Querying ===")
    print(f"  Query: 'what is total Q4 Sales?'")
    print(f"  Answer: {engine.query_table(table, 'what is total Q4 Sales?')}")


if __name__ == "__main__":
    main()
