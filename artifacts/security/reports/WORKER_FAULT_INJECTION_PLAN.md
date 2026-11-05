# AEGIS-DocIntel — Worker Fault Injection Plan

> **Document ID**: `WORKER_FAULT_INJECTION_PLAN.md`  
> **Work Item**: WP-07.05  
> **Status**: **ACTIVE & ENFORCED**  

---

## 1. Fault Scenarios

| Test ID | Injected Fault | Injection Mechanism | Expected System Recovery |
| :--- | :--- | :--- | :--- |
| `WORK-001` | Worker Crash | Kill worker process mid-execution | Lease expiration allows job recovery / safe termination. |
| `WORK-002` | Partial Write Crash | Worker aborts after writing partial chunk | Atomic database transaction rolls back; no corrupt final state. |
| `WORK-003` | Queue Broker Restart | Broker process restarts with pending messages | Durable persistence preserves all queued messages. |
| `WORK-004` | Database Disconnect | SQLite connection drops during query | Worker retries with exponential backoff and recovers. |
| `WORK-005` | Storage Target Disconnect | File storage throws transient IO error | Bounded retry without marking job complete prematurely. |
| `WORK-006` | Duplicate Job Delivery | Send identical job payload twice | Idempotency guard detects existing result; executes once. |
| `WORK-007` | Concurrent Race | Two workers claim same job simultaneously | Atomic database update (`WHERE status = 'QUEUED'`) gives 1 winner. |
| `WORK-008` | Operation Timeout | Task hangs past configured timeout | Task cancelled via timeout watchdog; worker freed. |
| `WORK-009` | Retry Exhaustion | Failure persists across 3 retry attempts | Job moves to dead-letter / `FAILED` state. |
| `WORK-010` | Malformed Payload | Invalid JSON or missing required fields | Immediate permanent failure; no retry loop. |
| `WORK-011` | Temp Storage Full | Disk write returns ENOSPC | Worker catches IO error, cleans scratch files, fails safely. |
| `WORK-012` | Memory Exhaustion | Memory limit exceeded | Process isolation contains crash; supervisor restarts worker. |
| `WORK-013` | Tenant Mismatch | Job payload specifies mismatched tenant | Worker security guard rejects job immediately. |
| `WORK-014` | Mid-Queue Deletion | Target document deleted while job queued | Job cancelled prior to execution start. |
| `WORK-015` | Network Drop Post-Commit | Worker loses network after committing | Duplicate retry checks commit status and skips re-execution. |
| `WORK-016` | Interrupted Deletion | Worker stops during multi-target cleanup | Subsequent worker re-runs deletion to clean remaining targets. |
