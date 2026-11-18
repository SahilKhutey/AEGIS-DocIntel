# Build Provenance & Deterministic Reproducibility

**Phase:** PROT-FINAL-04  
**Provenance Standard:** SLSA v1.0 / in-toto Statement v1  
**Date:** 2026-11-18T04:20:09.415275+00:00  

---

## 1. Provenance Statement (`release/provenance/build-provenance.json`)
The provenance statement establishes:
- Subject artifacts: `AEGIS-DocIntel-Demo-Edition.zip` and `manifest.json`.
- Source commit: `1025069eb10be62d10f431ab51ead62eef4aa2c8`.
- Build definition: Workflow `.github/workflows/evaluation-release.yml`.
- Resolved dependency digests: `package-lock.json` and `requirements-core.txt`.

## 2. Deterministic Archive Generation
Zip packaging normalizes timestamp metadata to `2026-01-01 00:00:00 UTC` and enforces standard permissions (`0o644`), eliminating timestamp-induced digest variance.
