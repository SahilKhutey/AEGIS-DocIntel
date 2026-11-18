# Data Retention & Deletion Policy (POL-007)

## Lifecycle Schedules
- **Primary Evaluator Documents:** 30 days default or immediate upon user-initiated deletion request.
- **Extracted Text & Table Artifacts:** Co-terminated with primary document deletion.
- **Vector Embeddings & Indexes:** Purged immediately upon document deletion or session termination.
- **Cached Answers & Session History:** Purged after 7 days of inactivity.
- **Security Audit Event Ledger:** Retained for 365 days for regulatory defense and compliance verification.
