# Release cadence

| Cadence | What ships | Window |
| -------- | ---------- | ------ |
| weekly | Nightly sweep results (drift, CVE, audit) | Mondays |
| monthly | Patch versions (`vX.Y.Z`) for security + bug fixes | First Tue |
| quarterly | Minor versions (`vX.Y.0`) | 1st of Q end |
| annual | Major versions (`vX.0.0`) | March |

## SLAs

| Severity | Response | Mitigation |
| -------- | -------- | ---------- |
| Critical | ≤ 24 h | Hot-fix within 48 h |
| High | ≤ 5 d | Patch within 14 d |
| Medium | ≤ 14 d | Next minor |
| Low | next minor | next minor |

## Security disclosures

* Email `security@aegis-docintel.invalid` (PGP key TBD).
* Until a key ships, use a GitHub security advisory draft.

## First patch-week notes (v0.3.0)

The first week after v0.3.0 demonstrated the cadence works:
- Sweep bots filed auto-PRs within 24 h of tag push.
- v0.3.1 was cut 7 days later, covering all Sev-2/Sev-3/security items.
- Weekly digest was published to #release channel on Monday.
