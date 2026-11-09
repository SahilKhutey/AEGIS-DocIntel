# 08 — Concurrency and Version Control

## 1. Concurrency Model

Enterprise review queues frequently involve multiple analysts, reviewers, and compliance officers working simultaneously. Without strict concurrency control, "lost updates" can occur if two reviewers decide the same item at the same time.

AEGIS-DocIntel enforces **Optimistic Concurrency Control (OCC)** combined with **Idempotency Safeguards**.

---

## 2. Version Concurrency Protocol

1. **Version Representation**: Every `ReviewItem` possesses an integer `version` field starting at `1`.
2. **Payload Requirement**: Every decision mutation (`/decisions`, `/claim`, `/reopen`) requires an `expected_version` property matching the version loaded by the client.
3. **Atomic Verification**:
   - The backend checks `if current_item.version != expected_version: raise ReviewVersionConflictError()`.
   - If a mismatch occurs, the backend rejects the transaction with HTTP 409 Conflict.
4. **UI Response**:
   - The UI intercepts HTTP 409 Conflict via `ApiError.isConflict`.
   - An alert banner is immediately displayed:
     > *"⚠️ Stale review version detected! Another reviewer has modified this item. Please reload to inspect the latest state."*
   - A single-click "Reload Latest" button re-fetches the latest state and audit records.

---

## 3. Idempotency Key Handling

To safeguard against duplicate transactions caused by network hiccups, double clicks, or automatic retries:
1. When a reviewer initiates a session on an item, a cryptographically unique key is generated:
   ```typescript
   idempotencyKeyRef.current = `idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
   ```
2. The key is transmitted in the `Idempotency-Key` HTTP header.
3. The backend caches the response associated with this key. If a repeated request arrives with the same key within the TTL window, the cached response is returned without executing duplicate transitions or generating redundant audit events.
4. Upon successful commit, the client refreshes the idempotency key for the next operation.
