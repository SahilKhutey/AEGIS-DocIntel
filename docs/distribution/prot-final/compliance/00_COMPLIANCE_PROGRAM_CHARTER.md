# PROT-FINAL-07: Compliance Programme Charter & Legal Governance

**Status:** APPROVED | **Classification:** CONFIDENTIAL / GOVERNANCE  
**Commit:** `74909474a80a9b81140a00cbeeb33a0567354b9a` | **Evaluated:** `2026-11-18T05:21:05.837251+00:00`

## Executive Summary
This document establishes the technical, operational, and contractual compliance framework governing the external distribution of AEGIS-DocIntel to evaluation users, research institutions, and commercial pilots.

## Programme Scope
- **Client Distribution Boundary:** Downloadable evaluation client, launcher scripts, and public Ed25519 verification keys.
- **Evaluation Gateway:** Public ingress, session authentication, device validation, rate limiting, and request sanitization.
- **Private Processing Engine:** Internal parsing sandbox, table extraction, and grounded intelligence orchestrator.
- **Data Infrastructure:** Parameterized multi-tenant PostgreSQL database, encrypted object storage, and audit log chains.
- **Third-Party Suppliers:** External cloud hosting, CI/CD runners, and outbound model providers (OpenAI, Anthropic).
