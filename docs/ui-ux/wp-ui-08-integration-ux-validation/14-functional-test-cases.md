# WP-UI-08: Functional Test Cases

## 1. Test Catalogue Overview

This catalogue records the automated functional test cases validating the complete AEGIS-DocIntel application across unit, integration, and end-to-end levels.

---

## 2. Functional Test Specifications

| Test Case ID | Capability Area | Description | Expected Outcome | Verification Level |
| :--- | :--- | :--- | :--- | :--- |
| **TC-INT-001** | API Client | `apiRequest()` appends `X-Workspace-ID` and `X-Tenant-ID` headers | Headers present in outgoing fetch options | Vitest `api-client.test.ts` |
| **TC-INT-002** | API Client | AbortController terminates stalled requests exceeding `timeoutMs` | Throws timeout ApiError | Vitest `api-client.test.ts` |
| **TC-INT-003** | API Client | Centralized error hierarchy parses HTTP status codes correctly | Identifies 401, 403, 404, 409, 422, 429, 500 | Vitest `api-client.test.ts` |
| **TC-AUTH-001**| RBAC Engine | `hasPermission()` evaluates canonical backend roles accurately | Grants access based on `ROLE_PERMISSION_MAP` | Vitest `auth-permissions.test.ts` |
| **TC-AUTH-002**| Session | Decodes claims from development and production JWT tokens | Extracts `tenant_id`, `sub`, and roles | Vitest `auth-permissions.test.ts` |
| **TC-AUTH-003**| Route Guard | `checkRouteAccess()` blocks unauthorized paths | Returns `authorized: false` on missing rights | Vitest `auth-permissions.test.ts` |
| **TC-RT-001** | Real-Time | Bounded LRU ring buffer suppresses duplicate incoming events | Drops identical `event_id` within cache window | Vitest `realtime.test.ts` |
| **TC-RT-002** | Real-Time | `ReconnectStrategy` calculates exponential backoff with jitter | Retries with backoff between 1s and 30s | Vitest `realtime.test.ts` |
| **TC-UI-001** | Components | `PermissionGate` renders fallback when permissions are lacking | Fallback UI visible; children hidden | Vitest `components.test.tsx` |
| **TC-UI-002** | Components | `AccessDenied` displays required permission role guidance | Accessible alert (`role="alert"`) rendered | Vitest `components.test.tsx` |
| **TC-UI-003** | Components | `SessionExpired` triggers refresh callback or sign-in routing | Calls `onRefresh` and `onSignIn` cleanly | Vitest `components.test.tsx` |
| **TC-UI-004** | Components | `ConnectionStatus` reflects real-time stream status changes | Renders connected, reconnecting, disconnected | Vitest `components.test.tsx` |
| **TC-E2E-001** | Journey 1 | Document inspection to grounded question answering journey | Submits question, verifies answer & citation | Playwright `e2e-user-journeys.spec.ts` |
| **TC-E2E-002** | Journey 2 | Cross-document comparison to governance review queue | Inspects conflicts, fact verification, audit trail | Playwright `e2e-user-journeys.spec.ts` |
| **TC-E2E-003** | Journey 3 | Operational observability and engineering telemetry | Inspects analytics, math, pipelines, monitoring | Playwright `e2e-user-journeys.spec.ts` |
| **TC-SEC-001** | Security | Workspace selector switches tenant context cleanly | Displays listbox and updates active workspace | Playwright `isolation-and-security.spec.ts` |
| **TC-SEC-002** | Security | SSRF validator blocks private and loopback webhooks | Rejects `localhost` and `192.168.1.1` | Playwright `developer.spec.ts` |
