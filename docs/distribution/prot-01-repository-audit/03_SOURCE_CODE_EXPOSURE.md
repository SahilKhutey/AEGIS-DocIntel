# PROT-01: Source Code Exposure & Decompilation Risk Audit

**Document:** 03_SOURCE_CODE_EXPOSURE.md  
**Audit Objective:** Analyze reverse-engineering, layer extraction, and decompilation risks for all platform components.  

---

## 1. Technical Realities of Local Software Distribution

When distributing software that executes locally on an evaluator's machine, standard obfuscation or container packaging provides **zero cryptographic protection**:
1. **Python Bytecode (`.pyc`):** Compiled `.pyc` files can be effortlessly decompiled back into readable source using tools like `decompyle++` or `uncompyle6`.
2. **Docker Image Layers:** Any Docker image pulled to a client machine (`docker pull` or `docker load`) allows the user to run `docker export` or `dive`, extracting the entire internal filesystem and all copied application files.
3. **Frontend JavaScript:** Even when minified, frontend bundles reveal API endpoints, data models, schema contracts, and client-side logic.

**Conclusion:** The only defensible method to protect proprietary Python algorithms and orchestration logic is **physical withholding**—hosting them exclusively on private cloud infrastructure behind an authenticated gateway.

---

## 2. In-Depth Analysis of Finding PROT-F01

### Finding Statement:
The repository's root `Dockerfile` contained:
```dockerfile
# Copy source code and config
COPY --chown=aegis:aegis src/ ./src/
COPY --chown=aegis:aegis backend/ ./backend/
COPY --chown=aegis:aegis config/ ./config/
COPY --chown=aegis:aegis openapi.json ./
```

### Attack Vector Analysis:
If the resulting `aegis-api` image were distributed to evaluators (via Docker Hub, GitHub Container Registry, or an exported `.tar` archive):
1. Evaluator runs `docker save -o aegis.tar <image-tag>`.
2. Evaluator extracts layers with `tar -xf aegis.tar`.
3. In layer tarballs, the entire `src/` tree (including `src/engines/topology/sheaf.py`, `src/engines/context/submodular.py`, etc.) is exposed in plain text.
4. All trade secrets, algorithmic mathematics, and internal implementations are fully compromised.

### Remediation & Architectural Gate:
1. **Root `Dockerfile` Blocked:** The root Dockerfile is classified as `PRIVATE` and barred from the distribution pipeline (verified by `SEC-DEMO-001`).
2. **Dedicated Demo Compose:** The downloadable package contains a dedicated `compose.yaml` that pulls only:
   - `aegis-demo-web`: Compiled Next.js standalone container.
   - `aegis-demo-proxy`: Stock `nginx:alpine` image mounting a read-only routing configuration.
3. **Zero Python Source in Package:** The downloadable archive `AEGIS-DocIntel-Demo-Edition.zip` contains **zero `.py` files**, ensuring no Python code ever touches the evaluator's filesystem.

---

## 3. Frontend Source Exposure Assessment

The frontend workbench (`web/`) is distributed as a compiled standalone container:
- **Source Maps Audited:** All `.map` files are strictly stripped during `next build`. Automated test `SEC-DEMO-003` verifies zero `.map` files exist.
- **Client Bundling:** Code is minified, dead-code eliminated, and uglified by SWC/Turbopack.
- **Client Boundary:** The frontend contains UI components, layout rendering, and synthetic state visualization. No proprietary mathematical logic or server credentials exist within the client bundle.
