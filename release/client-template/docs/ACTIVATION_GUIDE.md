# AEGIS-DocIntel — Activation and Licensing Guide

**Version:** 1.0.0-beta.1  

---

## 1. Overview
The AEGIS-DocIntel downloadable evaluation distribution requires an authorized evaluation license issued by the AEGIS Licensing Authority. Licenses are cryptographically signed using Ed25519 asymmetric cryptography.

---

## 2. Activation Modes

### Mode A: Online Challenge-Response Activation (Recommended)
1. Launch the application.
2. In the Activation Dialog, paste your assigned Evaluation Token:
   `<YOUR_EVALUATION_TOKEN>`
3. Click **Activate Device**.
4. The client transmits your local hardware challenge to the evaluation gateway, which verifies your entitlement, registers your device, and activates the session.

### Mode B: Air-Gapped Offline License File
1. If your machine is disconnected from the internet, request an offline `evaluation.lic` package from your AEGIS release coordinator.
2. In the application, click **Import Offline License File**.
3. Select your `.lic` file.
4. The client uses the embedded public key (`keys/license-verification-public.pem`) to verify the signature offline.

---

## 3. Evaluation Quotas & Entitlements
During the evaluation period, the default quota allowances are:
- **Active Documents:** Up to 5 concurrent documents.
- **Max File Size:** 10 MB per file.
- **Analytical Queries:** 20 queries per session.
- **Active Devices:** 1 authorized workstation per license.
- **Validity:** 14 calendar days from activation.

---

## 4. Activation Error Codes & Recovery

| Error Code | Meaning | User Recovery Action |
| :--- | :--- | :--- |
| `ERR_LIC_EXPIRED` | Evaluation term has concluded | Contact coordinator to renew evaluation entitlement |
| `ERR_DEVICE_LIMIT` | License is already bound to another PC | Deactivate previous device or request device release |
| `ERR_SIG_INVALID` | License file was altered or corrupted | Re-download clean `evaluation.lic` from portal |
| `ERR_QUOTA_EXHAUSTED`| Query quota reached | Contact administrator for quota top-up |
