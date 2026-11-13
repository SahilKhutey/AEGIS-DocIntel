# PROT-01: Protected Demo Architecture Specification

**Document:** 08_PROTECTED_ARCHITECTURE.md  
**Audit Objective:** Specify the cryptographic and network architecture separating the local evaluation distribution from central proprietary services.  

---

## 1. The Three Delivery Zones

```
+─────────────────────────────────────────────────────────────────────────────+
| ZONE 1: LOCAL EVALUATION PACKAGE (Shipped to User)                          |
|                                                                             |
|  • Next.js 16 Standalone Web Application (Port 3000)                        |
|  • Local Nginx Reverse Proxy (Routes /api to central gateway)               |
|  • PowerShell / Bash Orchestrators (start-demo.ps1, verify-package.ps1)     |
|  • Synthetic Evaluation Corpus (demo-data/)                                 |
|  • Ed25519 Public Verification Key (license/public-key.pem)                 |
|  • Signed 14-Day Evaluation License (license/evaluation.lic)                |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                        HTTPS / TLS 1.3│ X-Evaluation-License
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
| ZONE 2: PROTECTED CLOUD INFRASTRUCTURE (AEGIS Hosted)                       |
|                                                                             |
|  • Evaluation Gateway (FastAPI microservice)                                |
|    - Ed25519 signature & temporal expiration verification                   |
|    - Server-side quota counters (5 docs, 20 queries/day, 5 comparisons/day) |
|    - Device fingerprinting & brute-force activation protection              |
|    - Revocation registry check (revocation_list.json)                       |
|    - Strict tenant isolation (anti-IDOR) & error sanitation                 |
|                                                                             |
|  • Private Proprietary Core Engines (Air-Gapped Behind Gateway)              |
|    - Sheaf Laplacian multi-document spectral topology solver                |
|    - Submodular knapsack diversity & token-entropy context packing          |
|    - Abstract interpretation governance & contradiction engine              |
|    - Production LLM provider integrations & confidential prompt recipes     |
+─────────────────────────────────────────────────────────────────────────────+
                                       │
+──────────────────────────────────────▼──────────────────────────────────────+
| ZONE 3: SEPARATELY LICENSED THIRD-PARTY / OPEN-SOURCE TOOLS                 |
|                                                                             |
|  • aegis-docprep (Apache 2.0 open-source document preparation library)      |
|  • Python / Node.js runtime libraries (MIT / BSD-3-Clause)                  |
|  • PyMuPDF / Poppler-Utils (Isolated on backend execution boundaries)       |
+─────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Cryptographic Handshake & License Lifecycle

1. **Initial Activation:**
   - Evaluator runs `start-demo.ps1`.
   - The launcher uses the pre-issued `evaluation.lic` or queries `POST /api/v1/gateway/activate`.
   - The Gateway signs an Ed25519 license envelope containing `license_id`, `expires_at` (14 days), `features`, and `quotas`.
2. **Local Verification:**
   - `verify-package.ps1` verifies the signature using `public-key.pem` before starting containers.
3. **Gateway Ingress Validation:**
   - Every API call carries `X-Evaluation-License: <token>`.
   - The gateway parses and verifies the signature using the server's public key.
   - The gateway verifies `expires_at > now()` and `license_id not in revocation_registry`.
4. **Quota Decrementing:**
   - The gateway atomically verifies and updates sliding-window usage counters in `quotas.py`.
   - Requests exceeding limits return HTTP 429 with clean upgrade notifications.
