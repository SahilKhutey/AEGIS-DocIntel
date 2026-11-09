# 10 — State Management & Error Handling

## 1. State Lifecycle Architecture
Every intelligence capability adheres to an explicit 8-stage state lifecycle:

```
[Initial] ──(User Input)──> [Loading / Thinking]
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       [Success]            [Empty]            [Error]
            │                                     │
   ┌────────┴────────┐                            ▼
   ▼                 ▼                         [Retry]
[Grounded]    [Safe Abstention]
```

## 2. Capabilities & States

| Capability | Initial | Loading | Success | Empty | Partial / Abstain | Error |
|---|---|---|---|---|---|---|
| **Ask AEGIS** | Form ready, history empty | "Thinking...", textarea disabled | Grounded answer with citations | No documents found | Safe Abstention: Insufficient Evidence | ErrorState with retry |
| **Retrieval** | Prompt to search | "Searching...", disabled button | Ranked passage cards | No matching passages | Partial document scope | ErrorState with retry |
| **Evidence** | Document scope selector | "Loading passages..." | Verbatim quotes with coordinates | No indexed chunks | Missing page numbers | ErrorState with retry |
| **Knowledge** | Document scope selector | "Constructing graph..." | SVG Canvas & Tabular view | No extracted entities | Subgraph filter active | ErrorState with retry |
| **Comparison**| Document select grid (min 2) | "Comparing..." | Difference cards & aligned table | No overlapping facts | Partial match / conflicts | ErrorState with retry |

## 3. Request Cancellation & Stale Protection
All API services (`askAegis`, `retrieveDocuments`, `getDocumentEvidence`, `getKnowledgeGraph`, `compareDocuments`) accept an optional `AbortSignal`. When users submit a new query or re-trigger a search, in-flight requests can be cancelled cleanly to avoid race conditions and stale DOM updates.
