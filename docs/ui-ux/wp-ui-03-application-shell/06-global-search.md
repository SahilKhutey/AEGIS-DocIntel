# 06 — Global Search Interface

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-06`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Functional Scope & Debounce

The Global Search interface (`GlobalSearch`) enables rapid discovery across indexed documents, structured entities, citations, and pending review cases.

- **Debounce**: User input is debounced by $300\text{ms}$ using `useDebounce` hook to prevent redundant network requests.
- **Clear Action**: A dedicated clear button (`aria-label="Clear search"`) resets the query and closes results immediately.
- **Safe Navigation**: All internal result URLs are verified through `isSafeInternalHref()` to prevent open redirect vulnerabilities.

---

## 2. Search Result Contract

```ts
export type SearchCategory =
  | "documents"
  | "evidence"
  | "reviews"
  | "entities"
  | "actions";

export interface SearchResult {
  id: string;
  category: SearchCategory;
  title: string;
  snippet?: string;
  url: string;
  metadata?: Record<string, string>;
}

export interface GlobalSearchResponse {
  query: string;
  totalResults: number;
  items: SearchResult[];
}
```

---

## 3. Security & Validation

1. **Safe URL Sanitization**:
   - `isSafeInternalHref(href)` enforces that any navigation target must start with `/` and must NOT start with `//` or contain protocol schemes (`javascript:`, `data:`, `https:`).
2. **Permission Boundary**:
   - Search results are filtered according to user permissions (e.g. documents require `documents.read`, reviews require `governance.read`).

---

## 4. Backend API Contract Mapping

- **OpenAPI Reality**: There is no dedicated `/v1/search` omni-search endpoint in `contracts/openapi.yaml`.
- **Existing Search Primitives**:
  - Documents: `/v1/documents` with query parameters.
  - Intelligence queries: `/v1/query` with semantic retrieval.
- **Integration Strategy**: `DefaultSearchService` wraps document querying and provides structured mapping. Unsupported global entity searches are explicitly documented.
