# WP-UI-08: Security Controls & Validation

## 1. Multi-Tenant Security & Workspace Boundaries

AEGIS-DocIntel enforces strict multi-tenant data boundaries at both the transport and UI layers:

1. **Contextual Header Enforcement**:
   Every request made via `apiRequest()` injects `X-Workspace-ID` and `X-Tenant-ID`. The server-side FastAPI middleware validates that the authenticated identity possesses valid role bindings for the specified tenant.
2. **Real-Time Stream Segregation**:
   The `RealtimeManager` inspects every incoming WebSocket/SSE event. If an event's `workspace_id` does not match the currently active workspace, the event is immediately discarded.

---

## 2. Server-Side Request Forgery (SSRF) Defense

In the Developer Hub (`/developer`), users may register webhook endpoints. The frontend enforces strict SSRF pre-validation:
- **Loopback Blocking**: Disallows `localhost`, `127.0.0.1`, `::1`.
- **RFC 1918 Private Subnets**: Blocks `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- **Cloud Metadata Endpoints**: Explicitly blocks `169.254.169.254`.

---

## 3. Formula Injection Neutralization

When exporting analytics metrics or review logs to CSV (`exportCsv`), all values are scanned for dangerous formula trigger prefixes:
- Dangerous characters: `=`, `+`, `-`, `@`, `\t`, `\r`.
- **Remediation**: Leading formula characters are prefixed with a single quote `'` and wrapped in quotes, neutralizing spreadsheet code execution in Excel and LibreOffice.

---

## 4. XSS & Formula Injection Matrix

| Threat Vector | Affected Capability | Countermeasure Implemented | Test Verification |
| :--- | :--- | :--- | :--- |
| **XSS via Document Titles** | Library, Reviews | React JSX default escaping & text node rendering | Vitest `component-contracts.test.tsx` |
| **Formula Injection** | Analytics CSV Export | OWASP neutralization prefixing (`sanitizeCsvCell`) | Vitest `export-data.test.ts` |
| **SSRF Webhook Abuse** | Developer Platform | Regex & hostname pre-validation (`validateWebhookUrl`) | Playwright `developer.spec.ts` |
| **Cross-Workspace Bleed**| Shell & Streams | Workspace barrier dropping on switch (`RealtimeManager`) | Playwright `isolation-and-security.spec.ts`|
