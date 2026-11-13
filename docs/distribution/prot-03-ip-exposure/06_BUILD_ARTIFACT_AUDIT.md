# PROT-03: Build & Container Artifact Exposure Audit

**Document:** 06_BUILD_ARTIFACT_AUDIT.md  
**Audit Scope:** Inspection of container layers, build contexts, intermediate build stages, and distribution archives.  

---

## 1. Container Layer Extraction Analysis

### The Vulnerability of Monolithic Docker Images:
Standard Docker images distribute all intermediate filesystem modifications across compressed tarball layers. An evaluator who pulls an image containing source files can extract every file using:
```bash
docker save <image_name> -o image.tar
tar -xf image.tar
# Every layer's filesystem is exposed in plain text
```

### Audit of Root `Dockerfile`:
The root `Dockerfile` contained:
```dockerfile
COPY --chown=aegis:aegis src/ ./src/
COPY --chown=aegis:aegis backend/ ./backend/
COPY --chown=aegis:aegis config/ ./config/
COPY --chown=aegis:aegis openapi.json ./
```
Distributing this image would allow evaluators to extract all 847 Python files in `src/` within seconds.

---

## 2. Technical Remediation: The Two-Tier Container Architecture

The distribution pipeline implements a **strict separation between presentation and computation**:

```
+-------------------------------------------------------------+
| TIER 1: Downloadable Evaluation Containers (DISTRIBUTED)    |
|                                                             |
|  1. aegis-demo-web (ghcr.io/sahilkhutey/aegis-demo-web)     |
|     • Base Image: node:20-alpine                            |
|     • Build Context: Next.js standalone output              |
|     • Contents: Minified JS, HTML, CSS, public static assets|
|     • Excluded: Zero Python files, zero sourcemaps          |
|                                                             |
|  2. aegis-demo-proxy (nginx:alpine)                         |
|     • Base Image: nginx:1.27-alpine                         |
|     • Contents: nginx-demo-proxy.conf (read-only mount)     |
|     • Function: Local ingress, reverse proxy to Gateway     |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
| TIER 2: Private Core Engine Containers (AIR-GAPPED / CLOUD) |
|                                                             |
|  1. aegis-evaluation-gateway                                |
|     • Base Image: python:3.12-slim                          |
|     • Deployed exclusively on AEGIS AWS/GCP cloud cluster   |
|     • Accessible only via authenticated HTTPS API           |
|                                                             |
|  2. aegis-intelligence-engine                              |
|     • Private microservice behind VPC private subnet        |
|     • Houses Sheaf topology, submodular packing, math logic |
+-------------------------------------------------------------+
```

---

## 3. Package Denylist & Physical Exclusion Verification

The distribution assembly process enforces the rules in `distribution/audit/prot-03/private_module_denylist.txt`:
- All `*.py` files are strictly excluded from the downloadable zip package.
- All `*.map` files are strictly excluded.
- All `.env*` credential files are excluded.
- All `*private*.pem` keys are excluded.

### Automated Test Assertion:
Test `SEC-DEMO-001` and `IP-TEST-006` execute automated scans over the release archive `AEGIS-DocIntel-Demo-Edition.zip` and assert that:
$$\text{Count}(\text{Leaked Private Modules}) = 0$$
$$\text{Count}(\text{Python Source Files}) = 0$$
