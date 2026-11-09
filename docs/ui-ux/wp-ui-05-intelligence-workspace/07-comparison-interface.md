# 07 — Comparison Interface Specification

## 1. Functional Scope
The Cross-Document Comparison interface (`/compare`) allows analysts and compliance officers to detect variances, alignment, and conflicts across two or more documents.
Key features:
1. **Document Selection Grid**: Select 2 or more authorized tenant documents with instant count indicators.
2. **Comparison Modes**: Toggle between `structured` (fact-level), `semantic` (passage meaning), and `content` (textual alignment).
3. **Difference & Variance Cards**: Shows category, description, significance (`high`, `medium`, `low`), and left/right evidence quotes.
4. **Conflict Detection**: Explicitly highlights contradictions (e.g., conflicting liability caps or termination notice periods).
5. **Governance Queue Handoff**: Quick action linking detected conflicts to `/reviews` for human adjudication.
6. **Detailed Alignment Table**: Side-by-side table comparing subject, attribute, Document A value, Document B value, and alignment status badges.

## 2. Component Architecture
```
web/src/features/intelligence/
├── api/
│   └── comparison.api.ts       # Calls POST /api/v1/intelligence/compare
└── components/
    ├── ComparisonWorkspace.tsx # Multi-doc selection grid and mode selector
    └── ComparisonResult.tsx    # Summary card, difference items, and source quotes
```

## 3. Backward Compatibility
The `/compare` route retains the heading `Document Intelligence & Cross-Document Comparison` and the full alignment table to ensure complete continuity with legacy test suites (`workbench.spec.ts:421`).
