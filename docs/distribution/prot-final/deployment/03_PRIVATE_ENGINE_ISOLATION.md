# Private Engine Isolation Architecture (DEP-03)

## Boundary Invariants
1. **Zero Public Ports:** The private engine is declared with `expose: ["8000"]` and NEVER maps ports to host interfaces (`DEP-TEST-001`).
2. **Cryptographic Service Authentication:** Direct engine requests without valid HMAC-SHA256 tokens signed by the gateway are rejected (`DEP-TEST-002`, `DEP-TEST-004`).
3. **Replay Detection:** Engine tracks one-time `request_id` and quota reservation IDs, preventing token replay attacks.
4. **Evaluator Privilege Denial:** Administrative operations (`admin.*`) requested by evaluator roles are strictly denied.
