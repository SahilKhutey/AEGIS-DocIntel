# AEGIS-DocIntel — Troubleshooting & Diagnostics Guide

This guide covers common operational, deployment, and configuration issues encountered when setting up the Product Launch Edition.

---

## 1. Authentication & 401 Unauthorized Issues

### Issue: Requests return HTTP 401 in production
- **Root Cause:** In `AEGIS_ENVIRONMENT=production`, the application strictly enforces RS256 JWT signatures or configured SHA-256 API keys. Dev tokens (`dev-*`) and demo tokens are rejected.
- **Solution:**
  1. If running the public demo, ensure `AEGIS_DEMO_MODE=true` is set in your `.env` or Compose file.
  2. If running production, provide a valid RSA public key in `AEGIS_JWT_PUBLIC_KEY` or hashed keys in `AEGIS_API_KEYS`.

### Issue: "Configured key is not an RSA public key"
- **Root Cause:** A symmetric key or malformed PEM string was supplied to `AEGIS_JWT_PUBLIC_KEY`.
- **Solution:** Generate a valid RSA 2048-bit keypair using `openssl genrsa` and provide the public PEM starting with `-----BEGIN PUBLIC KEY-----`.

---

## 2. Ingress & Reverse Proxy (HTTP 502 / CORS)

### Issue: Browser displays "Network Error" or CORS failure when calling API
- **Root Cause:** The browser attempted to connect to `127.0.0.1:8000` or an internal Docker hostname (`http://aegis-api:8000`) directly from an external client.
- **Solution:**
  - With the Product Launch Edition, Next.js rewrites and Nginx reverse proxy routes all requests via same-origin `/api/v1/...`.
  - In `web/src/lib/api/client.ts`, leave `NEXT_PUBLIC_API_BASE_URL` empty (`""`) in browser deployments so that requests resolve to the same-origin reverse proxy.

### Issue: Nginx returns "502 Bad Gateway"
- **Root Cause:** The backend container `aegis-api` is still starting up or failed its healthcheck.
- **Solution:**
  - Inspect container logs: `docker-compose -f deploy/docker-compose.demo.yml logs -f aegis-api`
  - Ensure `aegis-api` reaches `healthy` status via `curl http://localhost:8000/health`.

---

## 3. Demo Workspace & Seed State

### Issue: No documents appear in the demo workspace
- **Root Cause:** The database volume was started clean without running the seeder.
- **Solution:**
  - Execute the seed script:
    ```bash
    docker-compose -f deploy/docker-compose.demo.yml exec aegis-api python demo/scripts/seed_demo.py
    ```
  - Alternatively, click **"Reset Demo Data"** directly on the dashboard home screen.

### Issue: "Need at least 2 elements for analysis" error on tiny text files
- **Root Cause:** Topological manifold analysis requires at least two distinct layout elements to form a graph edge.
- **Solution:** Ensure test documents contain at least two paragraphs or sections.

---

## 4. Diagnostics & Health Probes

Run diagnostic commands against the running stack:

```bash
# Check container status
docker-compose -f deploy/docker-compose.demo.yml ps

# Check core health probe
curl -s http://localhost/health | jq .

# Run automated pre-launch verification
python demo/scripts/verify_demo.py --api-url http://localhost
```
