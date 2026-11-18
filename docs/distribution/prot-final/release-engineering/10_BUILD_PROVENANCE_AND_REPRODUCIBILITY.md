# Build Provenance & Deterministic Reproducibility

**Phase:** PROT-FINAL-04  
**Provenance Standard:** SLSA v1.0 / in-toto Statement v1  
**Date:** 2026-11-18T03:48:37.665500+00:00  

---

## 1. Provenance Statement (`release/provenance/build-provenance.json`)
The provenance statement establishes:
- Subject artifacts: `AEGIS-DocIntel-Demo-Edition.zip` and `manifest.json`.
- Source commit: `cee7fc9b8b656e5419ec85ca527a0b7c5434da4a`.
- Build definition: Workflow `.github/workflows/evaluation-release.yml`.
- Resolved dependency digests: `package-lock.json` and `requirements-core.txt`.

## 2. Deterministic Archive Generation
Zip packaging normalizes timestamp metadata to `2026-01-01 00:00:00 UTC` and enforces standard permissions (`0o644`), eliminating timestamp-induced digest variance.
