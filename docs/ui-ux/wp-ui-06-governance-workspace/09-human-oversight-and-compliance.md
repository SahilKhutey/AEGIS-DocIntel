# 09 — Human Oversight and Compliance

## 1. Compliance Philosophy

AI models in AEGIS-DocIntel operate strictly as **advisory engines**. Under no circumstance does the software auto-approve or auto-resolve findings without human adjudication.

The Governance Workspace embeds compliance safeguards into the core user journey to ensure adherence to standards such as ISO 27001, SOC 2, HIPAA, and GDPR auditability guidelines.

---

## 2. Guardrails Implemented

### 2.1 Explicit Actor Attribution
Every action captures the authenticated user's ID (`actor_id`) and tenant context (`tenant_id`). Anonymous or unauthenticated decision commits are strictly blocked.

### 2.2 Mandatory Rationale Thresholds
- **Decisions (`approve`, `reject`, `request_evidence`)**: Min 3 characters required.
- **Corrections (`correct`)**: Min 3 characters rationale + ground-truth value + source quote.
- **Conflict Resolution**: Min 5 characters rationale explaining cross-document adjudication.
- **Administrative Reopen**: Min 5 characters explaining legal or compliance justification.

### 2.3 User Certification Guard
A dedicated compliance checkbox prevents accidental or robotic form submissions:
```html
[x] I certify that I have verified the evidence citations and that this decision complies with governance policies.
```
The submit button remains disabled until this checkbox is explicitly selected.

---

## 3. Tamper-Evident Trail
Audit events are sequenced monotonically (`sequence: 1, 2, 3...`) and stored append-only. No UI or standard API provides functionality to delete or alter historical audit entries.
