# Software Bill of Materials (SBOM) Generation & Validation

**Phase:** PROT-FINAL-04  
**Standard:** CycloneDX 1.5 JSON  
**Date:** 2026-11-18T04:20:09.415275+00:00  

---

## 1. Segregated SBOM Artifacts
Two independent SBOMs are maintained:
1. **Client Distribution SBOM:** `release/sbom/client-sbom.cdx.json` (553 components, includes web runtime, launcher scripts, nginx proxy, and demo assets).
2. **Backend Deployment SBOM:** `release/sbom/backend-sbom.cdx.json` (71 components, includes FastAPI, Pydantic, PyMuPDF, cryptography, and server dependencies).

## 2. Integrity Linkage
The release manifest links directly to the client SBOM's cryptographic SHA-256 digest, ensuring verifiable supply chain traceability.
