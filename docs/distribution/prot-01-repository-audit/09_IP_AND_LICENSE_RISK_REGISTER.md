# PROT-01: Intellectual Property & Licensing Risk Register

**Document:** 09_IP_AND_LICENSE_RISK_REGISTER.md  
**Audit Objective:** Catalog IP, legal, and licensing risks, assess pre- and post-mitigation severity, and resolve dual-licensing ambiguities (`PROT-F04`).  

---

## 1. Analysis of Finding PROT-F04 (Dual-Licensing Boundary)

### Finding Statement:
The repository contains both a proprietary root license (`LICENSE`) and an open-source license (`aegis-docprep/LICENSE` under Apache-2.0). If boundaries are blurred:
- Outside users could claim proprietary parts are Apache-2.0.
- Or, licensors might inadvertently restrict rights granted under Apache-2.0, triggering license compliance disputes.

### Resolution & Legal Clarity:
1. **Explicit Separation in Root `LICENSE`:** Section 1 explicitly identifies `/aegis-docprep` as Apache-2.0, while Section 2 governs AMDI-OS / AEGIS-DocIntel as proprietary evaluation and commercial software.
2. **Dedicated Evaluation License for Demo:** The downloadable package ships with `LICENSE-EVALUATION.md`, clearly stating that evaluation rights are limited, revocable, 14-day, non-commercial, and forbid reverse engineering.
3. **No Code Mixing:** Apache-2.0 code from `aegis-docprep` is packaged as an independent module with its own copyright and notice headers.

---

## 2. IP & Licensing Risk Register

| Risk ID | Risk Description | Pre-Mitigation Score | Mitigation Implemented | Post-Mitigation Score |
| :--- | :--- | :--- | :--- | :--- |
| **RISK-IP-01** | Proprietary algorithm extraction from Docker container | **CRITICAL (25)** | Full backend Dockerfile excluded; only compiled frontend + proxy distributed. Core runs behind cloud gateway. | **LOW (4)** |
| **RISK-IP-02** | Competitive cloning via frontend sourcemap reverse engineering | **HIGH (16)** | All `.map` files stripped during build; SWC minification enabled (`SEC-DEMO-003`). | **NEGLIGIBLE (2)** |
| **RISK-IP-03** | Cloud provider API key leak via browser-visible variables | **CRITICAL (25)** | `NEXT_PUBLIC_AEGIS_DEV_TOKEN` stripped; all cloud provider keys remain on private backend. | **NEGLIGIBLE (1)** |
| **RISK-IP-04** | License signature forgery allowing unmetered usage | **HIGH (20)** | 256-bit Ed25519 asymmetric cryptography; private key retained exclusively on gateway KMS. | **NEGLIGIBLE (2)** |
| **RISK-IP-05** | AGPL copyleft contamination via PyMuPDF | **HIGH (15)** | PyMuPDF excluded from client package; isolated across CLI subprocess boundaries in docprep. | **LOW (3)** |
| **RISK-IP-06** | Cross-tenant document leakage (IDOR) on shared gateway | **CRITICAL (25)** | Strict tenant boundary enforcement in `app.py`; all document queries filtered by `license_id`. | **LOW (3)** |
| **RISK-IP-07** | In-transit tampering of downloadable archive | **MEDIUM (10)** | `package-manifest.json` and `SHA256SUMS` provide automated SHA-256 verification. | **NEGLIGIBLE (1)** |
