# PROT-01: Secret Exposure & Credential Leakage Audit

**Document:** 05_SECRET_EXPOSURE_AUDIT.md  
**Audit Objective:** Scan repository files, git history, environment configurations, and build templates for active credentials, private keys, and sensitive tokens.  

---

## 1. Secret Scanning Scope & Methodology

A full-repository automated and manual secret scan was conducted across all 4,668 tracked files, specifically targeting:
- Cloud provider API keys (`sk-`, `ghp_`, `AKIA...`)
- Private cryptographic keys (`BEGIN PRIVATE KEY`, `BEGIN EC PRIVATE KEY`, `.pem`, `.key`)
- Database connection strings (`postgresql://`, `mongodb://`)
- JWT signing secrets (`AEGIS_JWT_SECRET`)
- Browser-visible development tokens (`NEXT_PUBLIC_*`)

Results are recorded in `distribution/audit/secret_scan_summary.json`.

---

## 2. In-Depth Analysis of Finding PROT-F02

### Finding Statement:
`web/src/lib/validation/environment.ts` declared:
```typescript
const PublicEnvironmentSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_AEGIS_API_URL: z.string().url().optional(),
  NEXT_PUBLIC_APP_ENV: z.enum(["development", "test", "staging", "production"]).default("development"),
  NEXT_PUBLIC_AEGIS_DEV_TOKEN: z.string().optional(),
});
```

### Risk Analysis:
1. In Next.js, all environment variables prefixed with `NEXT_PUBLIC_` are statically inlined into browser JavaScript bundles at build time.
2. If `NEXT_PUBLIC_AEGIS_DEV_TOKEN` is set during a demo build or left with a default, any visitor opening Developer Tools (`F12`) can read the token from client scripts.
3. If this token were accepted by the backend as an administrative bypass or unmetered entitlement key, any visitor could bypass quotas or access restricted endpoints.

### Remediation & Architectural Controls:
1. **Token Removal:** `NEXT_PUBLIC_AEGIS_DEV_TOKEN` is strictly prohibited in production demo builds.
2. **Asymmetric Licensing Model:** Demo authentication is cryptographically anchored to Ed25519-signed evaluation licenses (`X-Evaluation-License`), not development bearer tokens.
3. **Automated Verification:** Test `SEC-DEMO-002` scans all files in the downloadable package and asserts that no API keys, private keys, or credentials exist.

---

## 3. Cryptographic Key Separation Audit

The evaluation architecture relies on asymmetric cryptography to prevent key leakage:
- **Root Private Key (`private-key.pem`):**
  - Used by the central Evaluation Gateway to sign 14-day evaluation licenses.
  - Stored exclusively in `services/evaluation_gateway/keys/`.
  - Classified as `PRIVATE`. Never packaged into Docker images or distribution zip archives.
- **Root Public Key (`public-key.pem`):**
  - Shipped with the demo package in `distribution/demo-edition/license/public-key.pem`.
  - Safe for public distribution. Allows local launcher scripts (`verify-package.ps1`) and reverse proxies to verify signatures without exposing signing capability.

---

## 4. Environment File Hygiene
- `.env` and `.env.production` are classified as `PRIVATE` and barred from git tracking and distribution archives.
- Only `.env.example` and `.env.production.example` exist in the public repository, containing verified synthetic dummy strings.
