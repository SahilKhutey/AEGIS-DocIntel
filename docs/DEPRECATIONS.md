# Deprecations

## Policy

* **Minor versions** may deprecate. They may **not** remove.
* Removal happens in the **next-major** or the next-but-one minor, **never sooner**.
* Every deprecation emits a `DeprecationWarning` and is logged in the **major audit log** at `release/v0.X.Y/decisions.md`.
* The `legacy_bridge.py` shim is removed in **0.4.0** (a generous 18-month window from 0.2.0).

## v0.3.0 — Closes These Windows

| Symbol | Replaced by | Status change |
| ------- | ------------ | -------------- |
| `from backend.src.*` (any) | `from amdi.*` | **REMOVED** (no bridge) |
| `from src.amdi.*` (still teaching new learners) | `from amdi.*` | **WARNING up** |
| `legacy_bridge.engine_geometry` and 11 siblings | `engines.geometry` | **WARNING up** |
| `legacy_bridge.hybrid_retriever` and 5 siblings | `retrieval.hybrid` | **WARNING up** |
| `legacy_bridge.pdf_loader` and 8 siblings | `ingestion.pdf` | **WARNING up** |
| `legacy_bridge.pii_engine` and 1 sibling | `compliance.pii` | **WARNING up** |

## v0.4.0 — Final Removal

The entire `src/amdi/legacy_bridge.py` file is deleted. The supported
public surface is exactly the `src/amdi/` package tree.

## v1.0.0 — Hardened

* All public types finalized (`Query`, `Evidence`, `RetrievalResult`).
* All SDKs reach `1.0.0` (semantic stability per language).
* Helm chart promoted to `1.0.0`.
