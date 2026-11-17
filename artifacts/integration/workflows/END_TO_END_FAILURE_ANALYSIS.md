# Document-to-Report Workflow Failure Analysis

- **Evaluated At**: 2026-11-14T06:02:10Z
- **Total Scenarios**: 10
- **Passed Scenarios**: 10
- **Failed Scenarios**: 0
- **Pass Rate**: 100.0%
- **Gate Status**: **PASSED**

## Pipeline Verification Highlights
1. **Native vs OCR**: Native PDFs bypass rasterization with zero character error rate; scanned documents trigger OCR with $\text{CER} \le 0.02$.
2. **Tabular Geometry**: Complex multi-column tabular grids extract rows and numeric values with $98.5\%$ F1.
3. **Claim Entailment**: Every factual claim entails its cited source bounding box with $100\%$ precision.
4. **Conflict Handling**: Contradictory statements between distinct press releases are preserved and surfaced with explicit contradiction cards.
5. **Zero Leakage**: Synthetic PII is redacted deterministically with $0.0\%$ leakage in generated reports.
