# AMDI-OS Security Remediation Plan

This document details the remediation actions taken to address issues identified during the security audit of v1.0.0 and tracks ongoing low-severity items.

---

## 1. Completed Remediations (v1.0.0 Release)

### Issue #1: Bandit B104 (Hardcoded host bind)
* **Severity:** Medium
* **Description:** API server bound to all interfaces (`0.0.0.0`) by default, exposing development setups to public networks.
* **Remediation:** Refactored FastAPI runner to read server host binding from environment variable `AMDI_HOST`, defaulting to `127.0.0.1` for local safety.
* **Status:** ✅ FIXED

### Issue #2: Bandit B603 (Insecure Subprocess call)
* **Severity:** Medium
* **Description:** worker invoked shell-like processing scripts using unstructured string commands, risking command injection.
* **Remediation:** Refactored code to pass execution arguments as structured lists and set `shell=False` to bypass system shell interpolation.
* **Status:** ✅ FIXED

### Issue #3: npm Moderate Vulnerability (Transitive dependency CVE)
* **Severity:** Moderate
* **Description:** `d3-color` package imported by charting libraries had a denial of service vulnerability.
* **Remediation:** Ran `npm audit fix --force` and added resolution overrides inside package.json to pin version to `3.1.0`.
* **Status:** ✅ FIXED

---

## 2. Active Tracking & Low-Priority Items

The following accepted low-severity risks are slated for patching in the upcoming v1.0.1 maintenance release:

| Item | CVE / Linter ID | Package / File | Accepted Risk Context | Planned Fix |
|------|-----------------|----------------|-----------------------|-------------|
| 1. Base Image CVEs | CVE-2023-4567 | python:3.12-slim | OS package issue not directly reachable. | Re-base to alpine or latest stable slim in v1.0.1 |
| 2. libcurl minor | CVE-2024-1122 | libcurl | Only triggers in rare proxy configurations. | Upgrade package dependencies in C++ SDK |
| 3. Random Module | Bandit B311 | `utils.py` | Warnings flagged on use of `random` for non-cryptographic utility operations. | No fix needed. (Cryptographic paths use `secrets`). |
