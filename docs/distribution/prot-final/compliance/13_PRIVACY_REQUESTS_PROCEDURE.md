# Privacy Requests & Data Subject Rights Procedure (WP 07.07)

## Standard Operating Procedure
1. **Intake:** Request submitted via `/v1/compliance/privacy-requests`.
2. **Authentication:** Proportional verification of requester identity and tenant ownership.
3. **Execution:** Cascading deletion across primary storage, embeddings, caches, and scratchpads.
4. **Verification & Audit:** Evidence generated and request marked `VERIFIED_CLOSED`.
