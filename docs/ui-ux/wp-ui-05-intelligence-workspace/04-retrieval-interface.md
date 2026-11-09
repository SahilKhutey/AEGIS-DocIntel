# 04 — Retrieval Interface Specification

## 1. Functional Scope
The Document Retrieval Interface (`/intelligence/retrieval`) enables analysts to inspect what the retrieval pipeline extracts before or independently of LLM synthesis.
Key features:
1. **Passage Querying**: Search across authorized documents with query expansion and BM25 + dense hybrid search.
2. **Document Scoping**: Restrict queries to individual documents or search tenant-wide.
3. **Relevance & Ranking Transparency**: Displays raw backend relevance scores and ranking order.
4. **Passage Inspection**: Shows section headers, page numbers, and verbatim text chunks.
5. **Direct Evidence Handoff**: Each passage card includes an "Inspect evidence" link routing directly to the Evidence Explorer.

## 2. Component Architecture
```
web/src/features/intelligence/
├── api/
│   └── retrieval.api.ts        # POST /api/v1/retrieve with fallback to document chunks
└── components/
    ├── RetrievalSearch.tsx     # Search form with query input and submit button
    └── RetrievalResult.tsx     # Result card displaying score, rank, and passage
```

## 3. UI States
- **Initial State**: Empty state prompting the user to enter a search query.
- **Searching / Loading**: Search button disabled with "Searching..." indicator.
- **Populated Results**: Cards showing rank (`#1`, `#2`), document name, page number, section title, quoted text snippet, and backend relevance score.
- **No Results Found**: Descriptive empty state suggesting query refinement or scope adjustments.
- **Error State**: Displays API error details with a retry action.
