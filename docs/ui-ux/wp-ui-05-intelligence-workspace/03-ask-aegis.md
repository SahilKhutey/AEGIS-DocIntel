# 03 — Ask AEGIS Specification

## 1. Functional Scope
The Ask AEGIS capability (`/ask`) provides an intelligent Q&A interface over the tenant's indexed documents.
Key features:
1. **Conversational Multi-Turn History**: Maintains chat context across queries.
2. **Document Scope Restriction**: Allows scoping queries to specific document subsets or searching all authorized documents.
3. **Strict Citation Grounding**: Every answer is annotated with numbered citations `[1]`, `[2]` linked to verbatim evidence.
4. **Safe Abstention**: Clearly flags when retrieved evidence is insufficient or contradictory.
5. **Interactive Evidence Inspection**: Clicking any citation badge highlights the passage in the persistent side panel and enables navigation to the full document.

## 2. Component Architecture
```
web/src/features/intelligence/
├── api/
│   └── ask.api.ts              # Calls /api/v1/ask or /v1/query, normalizes response
├── components/
│   ├── QuestionComposer.tsx    # Accessible textarea with submit and loading states
│   ├── ChatMessage.tsx         # User questions & AEGIS grounded answers
│   └── CitationList.tsx        # Interactive citation badges with integrity flags
└── hooks/
    └── useAskAegis.ts          # State management hook for asking questions
```

## 3. UI States
- **Initial / Empty**: Scope filter visible, QuestionComposer ready, instruction text.
- **Loading / Thinking**: Submit button displays "Thinking...", textarea disabled, input preserved.
- **Grounded Answer**: Answer text, verified grounding badge, copy button, numbered citation pills, and warnings.
- **Safe Abstention**: Amber warning banner "Safe Abstention: Insufficient Evidence" displayed when confidence threshold is not met.
- **Citation Integrity Warning**: Rose warning banner displayed if claim references do not resolve to citation records.
- **Error State**: Displays error message with "Retry" action.
