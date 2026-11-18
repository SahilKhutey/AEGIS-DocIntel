# Release Pipeline & Supply Chain Architecture

**Phase:** PROT-FINAL-04  
**Date:** 2026-11-18T03:48:37.665500+00:00  

---

## 1. Target Pipeline Architecture
The evaluation client build and verification pipeline follows strict separation-of-concerns:

```mermaid
flowchart TD
    Repo[Source Repository / Git Tag] --> CI[Isolated CI Build Worker]
    CI --> Web[Frontend Production Compile]
    CI --> Launch[Launcher Assembly]
    Web --> Assembly[Client Allowlist Assembly]
    Launch --> Assembly
    Assembly --> Boundary[Artifact Boundary Validation]
    Boundary --> SBOM[CycloneDX SBOM Generation]
    SBOM --> Scan[Secret & Vulnerability Scanners]
    Scan --> Sign[Ed25519 Manifest Signing]
    Sign --> Prov[SLSA v1.0 Provenance Generation]
    Prov --> Dist[Production Distribution]
```

## 2. Private Engine Isolation Invariant
The private reasoning engine (`src/core/`, `src/engine/`) is deployed exclusively to isolated private VPC infrastructure. It is strictly prohibited from entering the client assembly pipeline.
