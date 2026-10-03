# AMDI-OS Penetration Testing Report

**Date:** 2026-01-08
**Scope:** API endpoints (`/api/v1/*`), Dashboard UI, Ingestion worker nodes
**Methodology:** OWASP Top 10 web application testing standards (Black-box & White-box)

---

## 1. Test Targets & Vulnerability Coverage

### SQL Injection (SQLi)
* **Test Vector:** Parameter tampering on `/api/v1/documents` and query-based parameters on search.
* **Findings:** Zero SQLi vulnerabilities found. The application strictly utilizes SQLAlchemy ORM with fully parameterized queries.
* **Status:** ✅ PASS

### Cross-Site Scripting (XSS)
* **Test Vector:** Injecting `<script>alert(1)</script>` inside document names, metadata tables, and tags.
* **Findings:** Frontend templates escape all rendered variables via React default binding. Content Security Policy (CSP) headers are configured on index.html to block arbitrary inline script executions.
* **Status:** ✅ PASS

### Path Traversal
* **Test Vector:** Uploading documents with filenames like `../../../../etc/passwd` or calling download endpoints with relative path paths.
* **Findings:** Ingestion engine cleans filenames using secure filename wrappers, stripping path delimiters. Absolute paths are resolved and validated within strict workspace directories.
* **Status:** ✅ PASS

### Server-Side Request Forgery (SSRF)
* **Test Vector:** Modifying connector webhook endpoints to resolve local loops (`http://localhost:5432` or `http://169.254.169.254/`).
* **Findings:** Webhook connections undergo strict DNS validation, rejecting private subnet IP ranges and local loops.
* **Status:** ✅ PASS

### Authorization Escalation (IDOR)
* **Test Vector:** Authenticating as user A and trying to request `GET /api/v1/documents/{id_of_user_B}`.
* **Findings:** API layer asserts ownership rules on every resource retrieval query, yielding 404/403 errors on mismatches.
* **Status:** ✅ PASS
