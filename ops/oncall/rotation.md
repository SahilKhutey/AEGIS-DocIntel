# On-call rotation

Single-engineer rotation, weekly flip, Tuesday 09:00 UTC.

| Week | Primary | Backup |
| ---- | ------- | ------ |
| 2026-10-01 -> 07 | Alice | Bob |
| 2026-10-08 -> 14 | Bob | Carol |
| 2026-10-15 -> 21 | Carol | Alice |
| 2026-10-22 -> 28 | Alice | Bob |

* Acknowledge any paged alert within 5 minutes during business hours,
  within 30 minutes off-hours.
* Mitigation SLA per `docs/SLA.md#4-incident-response`.
* Always run a postmortem, even if the resolution was trivial.
