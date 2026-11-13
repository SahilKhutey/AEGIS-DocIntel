# PROT-01: Container & Runtime Exposure Audit

**Document:** 06_CONTAINER_AND_RUNTIME_AUDIT.md  
**Audit Objective:** Evaluate Dockerfiles, Compose network configurations, port bindings, volume mounts, and container layer exposure.  

---

## 1. Container Exposure Matrix

Cataloged in `distribution/audit/container_exposure_register.csv`:

| Container Service | Base Image | Build Context | Exposed Ports | Distributable? | Audit Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`aegis-api`** | `python:3.12-slim` | Root (`.`) | 8000, 9090 | **NO** | **EXCLUDE (PROT-F01)**: Raw Python source packaged. |
| **`aegis-web`** | `node:20-alpine` | `web/` | 3000 | **YES (Compiled)** | **ALLOW (RESTRICTED)**: Standalone Next.js bundle. |
| **`aegis-demo-web`** | `node:20-alpine` | Pre-built standalone | 3000 (bridge only) | **YES** | **ALLOW**: Shipped in demo Compose. |
| **`aegis-demo-proxy`** | `nginx:alpine` | Config mount | 3000 (host) | **YES** | **ALLOW**: Reverse proxy with admin blocking. |
| **`prometheus`** | `prom/prometheus` | Config mount | 9090 | **NO** | **EXCLUDE**: Internal metrics; omitted from demo. |
| **`grafana`** | `grafana/grafana` | Config mount | 3001 | **NO** | **EXCLUDE**: Internal dashboard; omitted from demo. |

---

## 2. In-Depth Analysis of Finding PROT-F03

### Finding Statement:
`deploy/docker-compose.yml` was designed for platform self-hosting, running the full API backend, web frontend, Prometheus, and Grafana.

### Audit Findings:
1. Distributing `deploy/docker-compose.yml` requires building `Dockerfile` (which leaks source code, PROT-F01) or pulling proprietary backend images.
2. Prometheus and Grafana add unnecessary complexity and 1.5+ GB of download weight to an evaluation experience.
3. The original Compose file bound services to `127.0.0.1:8000` directly without ingress route filtering.

### Technical Resolution:
A dedicated, lightweight evaluation Compose configuration was authored at:  
`distribution/demo-edition/deploy/compose.yaml`

```yaml
services:
  web:
    image: ghcr.io/sahilkhutey/aegis-docintel-demo-web:v1.1.0
    container_name: aegis-demo-web
    networks:
      - aegis-demo-net
  proxy:
    image: nginx:alpine
    container_name: aegis-demo-proxy
    ports:
      - "3000:80"
    volumes:
      - ./nginx-demo-proxy.conf:/etc/nginx/nginx.conf:ro
    environment:
      - AEGIS_GATEWAY_URL=${AEGIS_GATEWAY_URL:-https://gateway.aegis-docintel.io}
    networks:
      - aegis-demo-net
```

---

## 3. Ingress Route Hardening & Administrative Protection

The demo reverse proxy configuration (`distribution/demo-edition/deploy/nginx-demo-proxy.conf`) introduces defense-in-depth:
1. **Administrative Route Blocking:**
   ```nginx
   location ~* /api/v[0-9]+/admin {
       return 403 '{"error": "FORBIDDEN", "message": "Administrative interfaces are disabled in the Evaluation Edition."}';
   }
   ```
   Verified by test `SEC-DEMO-004`.
2. **Payload Size Enforcement:** `client_max_body_size 10M;` strictly drops oversized uploads at the reverse proxy boundary.
3. **Security Headers:** Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Referrer-Policy: strict-origin-when-cross-origin`.
