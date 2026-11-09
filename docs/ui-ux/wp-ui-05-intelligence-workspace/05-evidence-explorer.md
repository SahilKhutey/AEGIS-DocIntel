# 05 — Evidence Explorer & Provenance Specification

## 1. Functional Scope
The Evidence Explorer (`/intelligence/evidence`) is the core verification layer of AEGIS. It bridges generated statements and verbatim source text.
Key features:
1. **Verbatim Evidence Records**: Displays exact extracted passages with chunk IDs and page coordinates.
2. **Deep Linking**: Supports deep linking from citations via `?document_id=...&passage_id=...`, highlighting target evidence.
3. **Citation Integrity Engine**: Pure client-side validation (`validateAnswerCitations`, `findBrokenCitationReferences`) checking that every claim reference maps to a real citation ID.
4. **Document Navigation**: Direct "Open source document" links routing into the Document Inspection Workspace (`/documents/[documentId]`).

## 2. Integrity Distinctions
The UI enforces strict distinctions between grounding states:
- **Source Exists**: The referenced document or passage exists and is readable in the repository.
- **Citation Resolves**: The citation points to a valid chunk or coordinate.
- **Claim Supported**: A formal evaluation establishes that the quote supports the claim.
- **Claim Verified**: A human reviewer in the Governance Queue has confirmed the fact.

## 3. Component Architecture
```
web/src/features/intelligence/
├── api/
│   └── evidence.api.ts         # GET /api/v1/documents/{id}/chunks
├── components/
│   └── EvidenceDetail.tsx      # Card displaying evidence snippet, page, and link
└── utils/
    └── citation-utils.ts       # validateAnswerCitations, getClaimCitations, etc.
```
