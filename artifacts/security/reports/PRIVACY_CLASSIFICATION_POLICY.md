# AEGIS-DocIntel — Privacy & Sensitive Data Classification Policy

> **Document ID**: `PRIVACY_CLASSIFICATION_POLICY.md`  
> **Work Item**: WP-07.03  
> **Status**: **ACTIVE & ENFORCED**  
> **Regulatory Reference**: General Data Protection Regulation (GDPR), Digital Personal Data Protection Act, 2023 (DPDP Act)  

---

## 1. Data Classification Hierarchy

| Level | Classification | Definition & Examples | Default Security Action | Downstream Handling |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | `PUBLIC` | Freely published research, SEC public filings, press releases. | Allow full pipeline processing. | Retain verbatim. |
| **L2** | `INTERNAL` | Non-public organizational memos, project roadmaps, architectures. | Authenticated tenant access. | Restrict to tenant. |
| **L3** | `CONFIDENTIAL` | Commercial agreements, non-public financials, vendor terms. | Restricted role access (`editor`, `admin`). | Mask in public exports. |
| **L4** | `SENSITIVE_PERSONAL_DATA` | Personal Identifiable Information (PII): SSNs, government IDs, phone numbers, personal emails, residential addresses. | Mandatory masking / tokenization. | Replace with `[REDACTED_...]`. |
| **L5** | `HIGHLY_RESTRICTED` | Plaintext API keys, RSA private keys, passwords, database credentials, payment card PANs. | Block / Quarantine / Strict mask. | 0% leakage tolerance. |

---

## 2. Detection & Masking Taxonomy

1. **Email Addresses**: RFC 5322 standard patterns. Masked as `[REDACTED_EMAIL]`.
2. **Phone Numbers**: International E.164 and local formats. Masked as `[REDACTED_PHONE]`.
3. **Government Identifiers / SSN**: Pattern matching with validation checks. Masked as `[REDACTED_SSN]`.
4. **Payment Card Information**: Luhn mod-10 algorithm check. Masked as `[REDACTED_CREDIT_CARD]`.
5. **API Keys & Cryptographic Secrets**: High-entropy prefix matching (`sk-*`, `ghp_*`, `AKIA*`, `ASIA*`, `-----BEGIN PRIVATE KEY-----`). Masked as `[REDACTED_SECRET]`.
6. **Structured Table & OCR Content**: Bounding box coordinate redaction in addition to textual token replacement.

---

## 3. Privacy Safety Invariants

- **Invariant 1 (Zero Output Leakage)**: No Level 4 or Level 5 raw string may ever appear in external reports, exports, or LLM context prompts without authorized unmasking.
- **Invariant 2 (Log Telemetry Sanitization)**: Telemetry summaries must only log entity type counts and confidence scores, never the verbatim matched string.
- **Invariant 3 (Fail-Closed Enforcement)**: If a privacy detector encounters an internal exception, the system must fail closed (block the document) rather than passing uninspected text downstream.
