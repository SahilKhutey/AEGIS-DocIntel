# AEGIS-DocIntel — Security & Responsible Disclosure Policy

**Version:** 1.0.0-beta.1  

---

## 1. Security Architecture Highlights
- **Cryptographic Asymmetric Licensing:** Evaluation tokens are verified using Ed25519 signatures. The private signing key resides strictly in an isolated offline air-gapped signing vault.
- **Fail-Closed Execution:** Any signature mismatch, expired entitlement, or unrecognized device challenge immediately locks down protected workflows.
- **Pre-Retrieval Tenant Isolation:** All SQL and vector queries are bound to your verified tenant ID at the database query level, preventing cross-tenant data leakage.
- **Zero Local Privileges:** The application installer and portable client execute with standard unprivileged user permissions.

---

## 2. Reporting Vulnerabilities
If you identify a security issue, potential vulnerability, or suspected credential exposure in AEGIS-DocIntel:
1. Please report it privately via email to: `security@aegis-docintel.internal`.
2. Do not disclose vulnerabilities publicly or on social media before a patch is published.
3. Include detailed steps to reproduce, affected versions, and system environment.
4. The security response team will acknowledge your report within 24 hours and provide regular status updates until remediation is verified.
