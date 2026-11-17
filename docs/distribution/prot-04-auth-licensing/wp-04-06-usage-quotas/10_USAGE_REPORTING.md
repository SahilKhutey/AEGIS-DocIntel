# WP-04.06 Dossier 10: Usage Reporting

**Work Package:** PROT-04.06  
**Title:** Evaluator Usage Dashboard, API Contracts & Safe Reporting Schemas  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Evaluator Transparency Principle

Evaluators must have clear, real-time visibility into their capacity utilization to plan their evaluation workflows and understand when an upgrade to AEGIS Enterprise is required. However, reporting endpoints must deliver this transparency without exposing sensitive internal cost structures, provider telemetry, or cross-tenant data.

---

## 2. Evaluator API Reporting Contracts

Evaluators interact with four dedicated usage reporting endpoints:

### 2.1 Live Usage Summary (`GET /v1/evaluation/usage`)
Returns the complete multi-dimensional capacity utilization for the caller's evaluation license:

```json
{
  "license_id": "eval-lic-001",
  "policy_version": "evaluation-1.0",
  "documents": {
    "used": 6,
    "limit": 20,
    "remaining": 14,
    "unit": "documents"
  },
  "storage_bytes": {
    "used": 31457280,
    "limit": 104857600,
    "remaining": 73400320,
    "unit": "bytes"
  },
  "queries": {
    "used": 18,
    "limit": 100,
    "remaining": 82,
    "unit": "queries"
  },
  "comparisons": {
    "used": 3,
    "limit": 10,
    "remaining": 7,
    "unit": "comparisons"
  },
  "generated_at": "2026-11-14T11:00:00Z"
}
```

### 2.2 Usage Ledger History (`GET /v1/evaluation/usage/history`)
Returns the immutable, chronological event history for the caller's evaluation license. Evaluators can verify when and where each consumption event occurred (`operation_id`, `amount`, `timestamp`).

### 2.3 Effective Limits Contract (`GET /v1/evaluation/usage/limits`)
Returns the baseline quota definitions for the assigned tier, enabling client UIs to render static threshold indicators and upgrade prompts.

### 2.4 Operation Status Query (`GET /v1/evaluation/usage/operations/{operation_id}`)
Returns the reservation and settlement state (`PENDING`, `COMMITTED`, `RELEASED`) for a specific asynchronous background job or request.

---

## 3. Data Sanitization & Leakage Prevention Invariants

The reporting layer strictly redacts all confidential infrastructure details:
1. **Zero Provider Cost Leakage:** Usage responses never report dollar costs, wholesale provider margins, or commercial API rates.
2. **Zero Provider Identity Leakage:** Responses do not disclose whether an inference was routed to Google Vertex AI, Anthropic Bedrock, or internal GPU clusters.
3. **Strict Tenant Isolation:** Every usage query validates `ctx.license_id`. An evaluator can never inspect another tenant's usage history (`QUOTA-012`).

---

## 4. Frontend UI Integration Pattern

In the desktop application and web UI (`web/src/components/dashboard/UsageOverview.tsx`), usage metrics power clean capacity meters:

```tsx
export const UsageMeter = ({ title, used, limit, unit }: UsageProps) => {
  const percentage = Math.min(100, Math.round((used / limit) * 100));
  const isWarning = percentage >= 80;
  const isExhausted = percentage >= 100;

  return (
    <div className="p-4 border rounded-lg bg-card">
      <div className="flex justify-between mb-2">
        <span className="font-medium text-sm">{title}</span>
        <span className="text-sm text-muted-foreground">
          {used} / {limit} {unit}
        </span>
      </div>
      <ProgressBar value={percentage} variant={isExhausted ? "destructive" : isWarning ? "warning" : "default"} />
      {isExhausted && (
        <p className="mt-2 text-xs text-destructive">
          Quota exhausted. Contact sales@aegis-docintel.io for full enterprise access.
        </p>
      )}
    </div>
  );
};
```

---

## 5. Verification & Test Evidence

- **`RECON-006`**: `GET /v1/evaluation/usage` returns complete multi-dimensional summary (**PASS**).
- **`QUOTA-011`**: Utilization updates immediately and reflects across connected client sessions (**PASS**).
