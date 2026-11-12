# AEGIS-DocIntel — Release Configuration Register

> **Release**: `v1.0.0-rc.1`  
> **Status**: **FROZEN CONFIGURATION**  
> **Date**: 2026-11-04  

---

## 1. Frozen Configuration Files & Hashes

| Configuration Asset | Purpose | Format | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| [`configs/security/policy.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/configs/security/policy.yaml) | Security policies, lockout thresholds, privacy masking | YAML | `f6aca9763fba69ed2c27bdd18efd1d7b3fd5b3ca10041d6e8d7721b1e978f2fd` |
| [`pyproject.toml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/pyproject.toml) | Python project metadata, dependencies & pytest settings | TOML | `9d41178e33b783c66c4c6aa818e9fe88967b3569fe55d0baaa58bfef035f87a6` |
| [`.env.example`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/.env.example) | Canonical environment variable template | Env | `de4aa46aa05b8be70068467055fc279fd2205ccfd7e930121dac790f2f0256c9` |
| [`configs/audit/default.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/configs/audit/default.yaml) | Master audit runner profile & suite configurations | YAML | `0f2e4fab1f8672c7a938b0a52ed7a3289b6b3cad814765df2fefac110778bbc6` |
| [`deploy/docker-compose.yml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/deploy/docker-compose.yml) | Hardened container service definitions | YAML | `40a95f3912c012bc6f20ba85553c3c724f03f7f6a516dbf35a5988eec683d11d` |
| [`deploy/nginx/aegis.conf`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/deploy/nginx/aegis.conf) | Reverse proxy & TLS ingress routing | Conf | `dd8c32f7d37c12d660487a0b34d5e53588376db1644b9c6b117d36606217a193` |
| [`openapi.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/openapi.json) | Full OpenAPI 3.1.0 specification (76 endpoints) | JSON | `1c121e0c8b79eff81b177f4d6f3086ce550f32ed8f8a11faf795c8bc51f482ea` |
| [`contracts/openapi.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/contracts/openapi.yaml) | YAML OpenAPI contract authority | YAML | `5e3c04874da10f140eb20010f15637c47bf67a63c9faf651dcb8e6f02bf2ef92` |
| [`web/package.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/web/package.json) | Frontend dependencies & Next.js scripts | JSON | `8879ed6af15754a1a002d578d84bf23dd218b75a199485d35d10a90c7c40b052` |
| [`web/tsconfig.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/web/tsconfig.json) | TypeScript strict compiler configuration | JSON | `dbacf04aa5f38c1ce4b0f030fbb84e5adff19306fb785b2e4aafef9c58705658` |

---

## 2. Configuration Governance Rules
1. **Immutable Freeze**: Any manual modification to the above configuration files invalidates the release candidate.
2. **Environment Separation**: Actual runtime secrets (`DATABASE_URL`, `JWT_PUBLIC_KEY`, `S3_SECRET_KEY`) are injected via environment variables at deployment time; no plaintext secrets exist in repository configurations.

---

## 3. Production Release v1.1.0 Configuration Register
> **Release**: `v1.1.0`  
> **Status**: **RELEASED CONFIGURATION**  
> **Date**: 2026-11-12  
> **Commit SHA**: `c54a7e6`

| Configuration Asset | Purpose | Format |
| :--- | :--- | :--- |
| `web/next.config.ts` | Next.js 16 standalone server configuration (`output: "standalone"`) | TypeScript |
| `web/Dockerfile` | Multi-stage production container for web workbench | Dockerfile |
| `deploy/docker-compose.yml` | Multi-service stack orchestrating API, Web, Prometheus, Grafana, and Nginx | YAML |
| `deploy/nginx/aegis.conf` | Ingress reverse proxy routing `/api/`, `/v1/`, and `/` routes | Conf |
| `scripts/verify_production_release.py` | Automated production release & packaging verification suite | Python |
