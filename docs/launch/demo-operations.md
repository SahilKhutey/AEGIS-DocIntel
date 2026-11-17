# AEGIS-DocIntel — Demo Operations & Sandbox Maintenance

This runbook describes operational management, maintenance, and automated reset procedures for the hosted **AEGIS Live Demo**.

---

## 1. Operational Goals

1. **Zero-Drift Baseline:** Every visitor must experience a clean, fully populated sample workspace regardless of what prior visitors uploaded.
2. **Strict Multi-Tenant Boundary:** Visitors to the demo sandbox cannot probe or view records from other enterprise tenants.
3. **Resource Protection:** Enforce rate limits and upload size boundaries to protect backend compute and disk storage.

---

## 2. Automated Workspace Reset

To prevent ephemeral user uploads from cluttering the demo workspace or filling disk storage, an automated reset should be executed periodically (e.g. every 6 hours):

### Reset Command
```bash
# Via CLI script against live container
python demo/scripts/reset_demo.py --api-url http://127.0.0.1:8000 --token aegis-demo-token-sandbox

# Or via HTTP POST request
curl -X POST http://127.0.0.1:8000/api/v1/demo/reset \
  -H "Authorization: Bearer aegis-demo-token-sandbox" \
  -H "X-Tenant-ID: demo-tenant"
```

### Recommended Cron Configuration
```cron
# Reset demo workspace every 6 hours at minute 0
0 */6 * * * /usr/local/bin/python /app/demo/scripts/reset_demo.py --api-url http://127.0.0.1:8000
```

---

## 3. Rate Limiting & Resource Caps

The demo environment enforces the following limits:

| Resource | Setting | Enforcement Point |
| :--- | :--- | :--- |
| **Max Upload File Size** | 15 MB | Nginx (`client_max_body_size`) & API Middleware |
| **HTTP Request Rate** | 20 requests/sec | Nginx (`limit_req zone=demo_rate_limit`) |
| **Monthly Token Budget** | 50,000 tokens | `TenantContext.monthly_token_limit` |
| **External LLM Egress** | Disabled (`false`) | Model Provider Policy (`AEGIS_ALLOW_EXTERNAL_LLM`) |

---

## 4. Monitoring & Telemetry Probes

- **Liveness:** `GET /health` (returns HTTP 200 with `{"status": "healthy"}`)
- **Readiness:** `GET /readiness` (verifies SQLite database read/write and memory state)
- **Demo Status:** `GET /api/v1/demo/session` (checks active session and seed document counts)
