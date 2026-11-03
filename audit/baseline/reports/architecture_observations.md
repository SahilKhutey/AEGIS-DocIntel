# AEGIS-DocIntel — Architecture Observations
**Baseline ID**: AEGIS-BASELINE-001  
**Generated Date**: 2026-11-03  

## 1. Architectural Strengths
1. **Formal Master State Invariant**: Centralizing all processing around the immutable 10-tuple $\mathcal{D} = (P, S, G, R, F, M, T, X, H, E)$ provides strict type contracts and deterministic traceability.
2. **Decoupled Production Primitives**: Extracting `aegis-docprep` with minimal dependencies (`numpy` only) isolates high-risk dependencies (e.g. PyTorch) from core lightweight pre-processing.
3. **Fail-Closed Security Posture**: The ASGI `AuthGuardMiddleware` defaults to deny-all, strictly whitelist-checking public routes (`/`, `/ui`, `/health`) and enforcing tenant isolation.
4. **Durable Job State Machine**: Job orchestration under `src.operations` utilizes atomic SQLite/Postgres lease acquisition and structured recovery states.

## 2. Identified Technical Debt & Boundary Inconsistencies
1. **Legacy Backend Directory Overlap**: `backend/src` and `src/` contain historical structural overlap. Canonical imports are consolidated under `src.*`.
2. **Global Python Environment Dependency Isolation**: The project must strictly enforce `.venv` execution to avoid transitive conflicts with global host packages.
3. **Research Module Quarantine**: Speculative research domains (`src/ael`, `src/math_concepts`) must remain decoupled from the production API pipeline.
