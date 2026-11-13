# PROT-04.05: Entitlement Matrix & Server-Side Enforcement

**Work Package:** PROT-04.05  
**Target:** Canonical Capability Vocabulary, Capability Authorization & Anti-Spoofing  
**Status:** **IMPLEMENTED & VERIFIED**

---

## 1. Canonical Capability Vocabulary

Rather than using generic role strings (`admin`, `editor`, `viewer`), PROT-04 enforces fine-grained capability checks defined in `distribution/policy/evaluation-entitlements.yaml`:

| Capability Identifier | Category | Granted in Demo? | Operational Scope |
| :--- | :--- | :--- | :--- |
| `documents.read` | Documents | **ALLOWED** | View uploaded documents, metadata, page counts, and text previews. |
| `documents.upload` | Documents | **ALLOWED** | Upload local evaluation documents (.pdf, .txt, .md, .json) subject to 10 MB limit. |
| `intelligence.query` | Intelligence | **ALLOWED** | Run Ask AEGIS queries with deterministic citations and contradiction detection. |
| `documents.compare` | Comparison | **ALLOWED** | Run topological comparisons and identify invariance/contradictions between specs. |
| `evidence.inspect` | Citations | **ALLOWED** | Inspect exact text grounding spans and SHA-256 genesis hash chaining. |
| `users.manage` | Administration | **DENIED (403)** | Create, list, or modify users or team members. |
| `platform.admin` | Platform | **DENIED (403)** | Modify system parameters, database connections, or logging levels. |
| `workspaces.create` | Workspaces | **DENIED (403)** | Provision additional tenants or multi-tenant workspaces. |
| `models.configure` | AI Models | **DENIED (403)** | Inspect or tune LLM parameters, weights, prompts, or provider API keys. |
| `integrations.manage` | Integrations | **DENIED (403)** | Configure external enterprise webhooks, ERP bridges, or cloud storage. |

---

## 2. Server-Side Enforcement Mechanism

In `services/evaluation_gateway/entitlements.py`:
- The dependency `get_current_entitlement` resolves the verified caller into an `EntitlementContext`.
- Protected route handlers call `ctx.require_feature("<capability_id>")`.
- If the capability is missing or belongs to `DISALLOWED_ENTITLEMENTS`:
  - A structured security audit event is logged (`entitlement.denied`).
  - An immutable HTTP 403 Forbidden response is returned:
    ```json
    {
      "error": "FEATURE_NOT_ENTITLED",
      "feature": "users.manage",
      "message": "Feature 'users.manage' is not enabled in your evaluation tier. Contact sales@aegis-docintel.io to unlock full enterprise capabilities."
    }
    ```

---

## 3. Anti-Spoofing & Privilege Escalation Immunity

The system was subjected to rigorous adversarial testing:

1. **Header Spoofing Attack (`ENT-004`):**
   - An attacker passes custom headers such as `X-User-Role: admin`, `Role: admin`, or `X-Tenant-Role: platform_admin`.
   - *Verification:* The gateway ignores client headers completely; only the cryptographically signed claims and server database context govern authorization. Administrative routes return HTTP 403.
2. **Entitlement Modification Attack (`ENT-005`):**
   - An attacker modifies the returned JSON response in browser memory or passes `X-Client-Entitlements: {"platform.admin": true}`.
   - *Verification:* The server independently authorizes every single request. Client-side tampering produces zero privilege escalation.
