# Semantic Versioning & Branching Policy

**Phase:** PROT-FINAL-04  
**Date:** 2026-11-18T03:48:37.665500+00:00  

---

## 1. Versioning Standard
AEGIS Evaluation follows strict Semantic Versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR (1.x -> 2.x):** Breaking protocol changes, incompatible client API modifications.
- **MINOR (1.0 -> 1.1):** Backward-compatible feature enhancements, new evaluation capabilities.
- **PATCH (1.1.0 -> 1.1.1):** Security remediations, bug fixes, performance improvements.

## 2. Release Tagging Rules
Release tags must follow the format `vMAJOR.MINOR.PATCH` (e.g. `v1.1.0`). Tags are signed and pushed only after all 12 release gates have been certified.
