# WP-04.05 Dossier 08: Frontend Entitlement Integration

**Work Package:** PROT-04.05  
**Title:** Evaluator Client Integration, Safe Schema & Anti-Tampering Protocol  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Architectural Mandate: Presentation Only

In downloadable software distributions, the client application runs on hardware fully controlled by the end user or a prospective evaluator. Any control enforced solely in JavaScript, React state, or browser local storage can be trivially bypassed using DevTools, debugger breakpoints, memory manipulation, or custom HTTP clients (cURL, Postman).

Consequently, the AEGIS-DocIntel Protected Demo Edition enforces the following architectural mandate:

> **The Frontend Mandate:**  
> 1. The client UI uses entitlement information **strictly to optimize user experience** (hiding disabled features, presenting upgrade calls-to-action, disabling unavailable controls).  
> 2. The client UI **never** serves as a security boundary.  
> 3. The server independently verifies all four factors ($\mathbf{I} \land \mathbf{L} \land \mathbf{D} \land \mathbf{E} \land \mathbf{R}$) on every single request.

---

## 2. Safe Entitlement Summary Contract

Evaluator clients must display their current tier and available features without exposing sensitive infrastructure details. Evaluator principals fetch their entitlement state via:

```http
GET /v1/evaluation/license/entitlements
Authorization: Bearer <evaluation-jws-token>
```

### Response Schema (`SafeEntitlementResponse`)
The server provides a sanitized, safe entitlement document:

```json
{
  "license_id": "eval-lic-001",
  "policy_name": "Evaluation Basic",
  "tier": "basic",
  "granted_features": [
    "document.upload",
    "document.preview",
    "query.ask_aegis",
    "query.cross_document",
    "table.view",
    "export.json"
  ],
  "enabled_permissions": [
    "document.upload",
    "document.read",
    "document.delete",
    "query.execute",
    "table.read",
    "export.create"
  ],
  "feature_flags": {
    "feature_document_upload": true,
    "feature_document_preview": true,
    "feature_ask_aegis": true,
    "feature_cross_doc_query": true,
    "feature_table_extractor": true,
    "feature_json_export": true,
    "feature_comparison_view": false,
    "feature_batch_processing": false,
    "feature_redaction_tools": false,
    "feature_pdf_export": false,
    "feature_excel_export": false,
    "feature_streaming_events": false
  },
  "limits": {
    "max_documents": 25,
    "max_file_size_mb": 15,
    "max_queries_per_day": 100,
    "max_comparison_documents": 0,
    "max_pages_per_doc": 20
  },
  "expires_at": "2026-12-31T23:59:59Z",
  "warnings": []
}
```

### Strictly Excluded Fields (Data Leakage Prevention)
The `SafeEntitlementResponse` schema strictly redacts:
- Internal database row IDs and primary keys.
- Cryptographic private keys or signature verification salts.
- Evaluator administrator capabilities or hidden API endpoints.
- Policy document source ASTs or engine rule definitions.
- Other tenants' identifiers or cross-evaluator usage statistics.

---

## 3. Client UI Integration Model

In the React frontend (`web/src/`), entitlements are consumed via a read-only React context and hook:

```typescript
// web/src/contexts/EntitlementContext.tsx
interface EntitlementContextType {
  features: Set<string>;
  permissions: Set<string>;
  hasFeature: (feature: string) => boolean;
  canPerform: (action: string) => boolean;
  limits: PolicyLimits;
  isLoading: boolean;
}

export const useEntitlements = () => useContext(EntitlementContext);
```

### Component Rendering Pattern
Buttons and navigation items conditionally render based on server-provided entitlements:

```tsx
// Example: Comparison Action Button
const CompareButton = () => {
  const { hasFeature } = useEntitlements();

  if (!hasFeature("comparison.view")) {
    return (
      <Tooltip content="Comparison view is available in Evaluation Pro">
        <Button disabled variant="outline">
          <LockIcon className="w-4 h-4 mr-2" />
          Compare Documents (Pro)
        </Button>
      </Tooltip>
    );
  }

  return <Button onClick={handleCompare}>Compare Documents</Button>;
};
```

---

## 4. Deconstruction of Attack & Bypass Scenarios

| Attack Vector | Client Action | Server-Side Defense | Test Assertion |
| :--- | :--- | :--- | :--- |
| **Local Storage Tampering** | Attacker edits `localStorage.setItem('user_tier', 'pro')` or modifies cached feature array. | Server never reads client storage. Evaluates authoritative policy on incoming token. Request fails with `403 Forbidden`. | `BYPASS-001` |
| **DOM Manipulation** | Attacker removes `disabled` attribute from DOM button or synthesizes click event. | Server intercepts request at `require_entitlement` dependency; rejects operation with `403 Forbidden`. | `BYPASS-002` |
| **Header Injection** | Attacker adds `X-User-Role: admin` or `X-Entitlements: feature_comparison_view`. | Server ignores untrusted headers; validates only cryptographically signed JWS claims. | `RBAC-004`, `RBAC-005` |
| **Direct API Synthesis** | Attacker crafts raw HTTP `POST /v1/evaluation/compare` using cURL with valid Basic token. | Server evaluates `ent_resolver.resolve(...)`, detects feature missing from Basic tier, returns `403`. | `ENT-004`, `BYPASS-003` |

---

## 5. Automated Frontend Security Verification

Frontend authentication and entitlement boundaries are statically and dynamically verified:
```bash
npm --prefix web run verify:auth
```
- **Result:** 0 violations detected.
- Verified: Zero hardcoded mock credentials, zero fallback `dev-default-tenant` tokens, zero client-authoritative role checks in production build paths.
