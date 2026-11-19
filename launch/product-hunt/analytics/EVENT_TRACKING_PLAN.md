# AEGIS-DocIntel — Privacy-Preserving Event Tracking Plan

**Workstream:** `launch/product-hunt/analytics`  
**Phase:** `PROT-FINAL-09`  
**Privacy Invariant:** Zero PII, Cookieless Telemetry, GDPR / DPDP 2023 Compliant  

---

## 1. Core Event Schema

| Event Key | Trigger Condition | Payload Properties (Non-PII Only) |
| :--- | :--- | :--- |
| `ph_referral_landed` | User enters landing page with `ref=producthunt` or `utm_source=producthunt`. | `referrer`, `landing_path`, `timestamp` |
| `hero_cta_clicked` | User clicks "Try Evaluation" or "Watch Demo" buttons. | `button_id`, `destination_anchor` |
| `demo_video_played` | User starts playing the 75s walkthrough video. | `duration_seconds`, `playback_rate` |
| `evaluation_registered`| User submits evaluation request form. | `segment` (researcher/analyst/dev), `status` |
| `package_download_started`| Evaluator clicks signed package download link. | `package_version` (0.1.0), `os` (windows) |
| `device_activated` | Evaluator completes challenge-response key binding. | `installation_id_hash`, `activation_latency_ms` |
| `first_doc_processed` | First document upload and DAG parsing completes. | `doc_type` (pdf/img), `page_count`, `duration_ms` |
| `query_submitted` | Evaluator executes Ask AEGIS or Compare query. | `query_type` (ask/compare), `citation_count` |
| `feedback_submitted` | Evaluator submits feedback modal form. | `category` (ux/retrieval/bug), `rating` (1-5) |

---

## 2. Strict Privacy & Redaction Invariants

- **No Personal Identifiers:** Never collect names, email addresses, corporate domains, or phone numbers in telemetry payloads.
- **No IP Addresses:** Client IP addresses are stripped at edge proxy before event logging.
- **No Document Text:** Document contents, query text, and retrieved answers are **strictly excluded** from analytics logs.
- **Cryptographic Hashing:** Evaluator IDs and device installation identifiers are anonymized using HMAC-SHA256 with an ephemeral daily salt.
