# 04 - Evaluator Lifecycle State Machine
```
INVITED -> REGISTERED -> LICENSE_ISSUED -> ACTIVATION_PENDING -> ACTIVE
  |            |               |                    |              |
  v            v               v                    v              v
EXPIRED     EXPIRED         EXPIRED             EXPIRED        SUSPENDED
                                                                   |
                                                                   v
                                                                REVOKED
                                                                   |
                                                                   v
                                                              TERMINATED
```
### Invariant Rules
1. `EXPIRED`, `REVOKED`, and `TERMINATED` states cannot transition back to `ACTIVE`.
2. Reinstating from `SUSPENDED` requires explicit operator authorization with documented justification.
3. Device deactivation revokes linked sessions immediately.
