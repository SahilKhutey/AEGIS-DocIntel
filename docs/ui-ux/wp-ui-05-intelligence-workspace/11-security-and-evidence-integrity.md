# 11 — Security & Evidence Integrity

## 1. Security Architecture & Threat Model
1. **Sovereign Multi-Tenancy**:
   - The frontend never allows cross-tenant query construction.
   - All requests carry the tenant bearer token in the `Authorization` header.
   - The FastAPI backend remains the final authorization authority.
2. **Untrusted Evidence Sanitization**:
   - Quoted document snippets and LLM-generated answers are treated as untrusted text.
   - Rendered with safe text-node escapes; no raw `dangerouslySetInnerHTML` is used.
3. **Prompt Injection & Indirect Injection Defense**:
   - Document chunks containing adversarial prompts or instructions are rendered purely inside semantic blockquotes without execution.

## 2. Citation Integrity Engine
The pure function `validateAnswerCitations`:
```typescript
export function validateAnswerCitations(answer: {
  claims?: { claimId: string; citationIds: string[] }[];
  citations: { citationId: string; documentId?: string }[];
}): CitationValidationResult
```
Ensures:
- Every claim citation ID points to a valid entry in `citations`.
- If an ungrounded or broken citation ID is detected, the UI displays a clear integrity alert:
  *"Citation Integrity Warning: Found N citation reference(s) that do not resolve to available source records."*
- Unreferenced citations are audited and flagged.

## 3. Grounding Integrity Rules
- The UI strictly differentiates between:
  1. *Source exists*
  2. *Citation resolves*
  3. *Claim is supported*
  4. *Claim is verified*
- An answer is never marked as "Verified Grounded" if the backend reports `insufficient_evidence: true` or returns missing citations.
