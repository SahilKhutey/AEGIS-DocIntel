# AEGIS-DocIntel — Accepted Risks Register (WP-09.03)
**Document ID**: `RSK-ACC-20261104-01`  
**Candidate Version**: `1.0.0-rc.1`  
**Approval Authority**: Release Authorization Board  
**Review Status**: `APPROVED`

---

## 1. Register of Accepted Non-Blocking Risks

| Risk ID | Title | Severity | Impact Summary | Compensating Control / Mitigation | Remediation Target | Authorized Approver |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| **AR-001** | Air-gapped speech transcription fallback | P3 | Audio transcription falls back to deterministic signal segmenter when Whisper weights are unavailable offline. | Deterministic segmenter generates timestamped regions; local weights pre-caching supported. | v1.1.0 | Lead ML Architect |
| **AR-002** | Complex nested table spanning (>50 pages) | P3 | Extreme tables spanning over 50 contiguous pages may partition into page-level sub-tables. | Each sub-table retains coordinate provenance and column headers; single-page & normal tables 100% reconstructed. | v1.1.0 | Data Pipeline Lead |
| **AR-003** | Local development sandbox port collision | P4 | Development environments may require port overrides if port 8000 is occupied. | `AEGIS_API_PORT` configurable via environment variable or `.env`. | Ongoing | DevOps Lead |

---

## 2. Risk Acceptance Governance
1. **Zero Blocker Policy**: Under no circumstances is a P0 (Critical) or P1 (High) security or data integrity vulnerability accepted.
2. **Review Schedule**: All accepted P3/P4 items are scheduled for review and enhancement in the v1.1.0 release cycle.
3. **Approval Status**: The above 3 non-blocking items have been reviewed, bounded, and approved for MVP release candidate `1.0.0-rc.1`.
