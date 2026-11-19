# AEGIS-DocIntel — Privacy and Data Handling Disclosures

**Version:** 1.0.0-beta.1  

---

## 1. Zero Model Training Guarantee
**Your evaluation documents, queries, and extracted data are NEVER used to train, retrain, fine-tune, or evaluate public or proprietary AI foundation models.** All LLM reasoning requests are executed through enterprise API agreements that explicitly prohibit data logging, retention, and training.

---

## 2. Data Boundary & Processing Architecture
- **Local Application Tier:** Standalone UI runs on your local machine. It stores no document contents outside your designated `%LOCALAPPDATA%\AEGIS-DocIntel` session directory.
- **Evaluation Gateway:** Validates your device signature, authenticates requests, and records atomic quota deductions. It never logs prompt text, document text, or raw answers.
- **Private Intelligence Engine:** Processes documents in ephemeral memory sandboxes. Stored documents and chunks are strictly isolated under tenant-scoped SQLite and vector schemas.

---

## 3. Cryptographically Verified Cascading Erasure
When you click **Delete Document** in the application interface:
1. Active memory representations and vector index entries are purged.
2. The document record and raw byte blobs in SQLite are deleted.
3. Temporary extraction artifacts on disk are securely overwritten.
4. The deletion is permanently recorded in the immutable audit ledger.
Once deleted, the document cannot be recovered by any user or administrator.
