# AEGIS-DocIntel — Launch-Day Operational Runbook

**Workstream:** `launch/product-hunt/campaign`  
**Phase:** `PROT-FINAL-09`  
**Launch Time:** 12:01 AM Pacific Time (00:01 PT) / 1:31 PM Indian Standard Time (13:31 IST)  

---

## 1. Launch-Day Operational Timeline

```
[13:00 IST] Pre-Launch Health Audit
     |
[13:31 IST] Product Hunt Launch Goes LIVE (00:01 PT)
     |
[13:35 IST] Post First Maker Comment
     |
[13:35 - 15:30 IST] Initial Response Window & Onboarding Health Check
     |
[15:30 - 18:30 IST] Europe / Asia Peak Hours & Telemetry Monitoring
     |
[18:30 - 21:30 IST] Mid-Day Operational Check & Community Triage
     |
[21:30+ IST / Morning PT] North America Morning Traffic Shift
```

---

## 2. Detailed Hour-by-Hour Actions

| Time (IST) | Time (PT) | Operator Phase | Mandatory Operational Actions |
| :--- | :--- | :--- | :--- |
| **12:30–13:00** | 23:00–23:30 | Pre-flight | Check gateway health (`/health/ready`), database connections, and disk quotas. |
| **13:00–13:30** | 23:30–00:00 | Standby | Open Product Hunt dashboard, Twitter/X, and support logging console. |
| **13:31** | **00:01** | **L-HOUR** | Confirm product page is published live on Product Hunt front page. |
| **13:35** | 00:05 | Engagement | Post prepared **First Maker Comment**. Pin to top if supported. |
| **13:35–15:30** | 00:05–02:00 | Early Wave | Monitor initial registrations; verify license challenge-response activations; reply to comments within 15 mins. |
| **15:30–18:30** | 02:00–05:00 | Afternoon | Review error logs; monitor parser processing queues; record usability suggestions. |
| **18:30–21:30** | 05:00–08:00 | Mid-Flight | Share mid-day engineering update in PH thread; check quota hold settlements. |
| **21:30–01:30** | 08:00–12:00 | US Morning | Engage with North American traffic; answer architecture & security questions. |
| **01:30–05:30** | 12:00–16:00 | Evening | Secondary review; follow up with evaluators who completed first document run. |

---

## 3. Incident Escalation & Response Protocol

| Severity | Incident Definition | Response SLA | Mitigation Action |
| :--- | :--- | :--- | :--- |
| **P0 (Critical)** | Gateway crash, database failure, credential leak, or total activation failure. | **< 5 minutes** | Fail-closed circuit breaker, redirect landing page to graceful maintenance notice, deploy hotfix. |
| **P1 (High)** | Document parser queue latency > 30s, or individual activation challenge failures. | **< 15 minutes** | Scale parser worker processes; clear stuck temporary scratchpads. |
| **P2 (Medium)** | UI cosmetic defects, non-critical documentation link errors, or feedback submission delays. | **< 1 hour** | Patch frontend static assets or documentation; respond to user directly. |
| **P3 (Low)** | General feature requests, stylistic suggestions, or non-blocking questions. | **< 4 hours** | Log into feature backlog; thank evaluator. |
