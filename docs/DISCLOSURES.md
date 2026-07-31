# Security advisories policy

## Reporting

* Email: `security@aegis-docintel.invalid` (replace with project email).
  Use the **GitHub Security Advisory** draft UI for confidential reports.
* PGP key: TBD — until a key ships, GitHub drafts are the canonical channel.

## What we commit to

| Stage | Target | Contact |
| ----- | ------ | ------- |
| Acknowledge | <= 2 business days | public-issue acknowledgement |
| Triage | <= 5 business days | CVE assignment (if warranted) |
| Mitigation plan | <= 30 days | update advisory + draft patch |
| Public release | <= 90 days | GitHub Security Advisory -> GHSA |

## Coordinated disclosure timeline

```
Day 0     : report received
Day 2     : acknowledgement + triage
Day 30    : mitigation agreed
Day 60    : patch ready; pre-disclosure notice to reporters
Day 90    : GHSA published; patches released in next patch version
```

## Severity grading

| Severity | Definition |
| -------- | ---------- |
| Critical | Remote, unauthenticated, data-loss or full RCE |
| High | Authenticated user can escalate or exfiltrate data |
| Medium | Conditions required but realistic; non-trivial impact |
| Low | Theoretical; requires unusual configuration |

## Embargoes

We honour reasonable embargoes when requested by reporters — typically
<= 90 days, renewable up to another 30 days in exceptional cases.

See `docs/POSTMORTEMS/2026-07-15-ingestion-slow.md` for a sample incident
write-up.
