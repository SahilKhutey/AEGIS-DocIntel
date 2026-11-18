# 01 - Product Overview
AEGIS-DocIntel is a privacy-first, enterprise-grade document intelligence platform designed to extract, analyze, synthesize, and cross-reference complex multi-page documents with strict mathematical grounding and provenance.

### Core Architectural Separation
The evaluation release enforces an immutable boundary between:
- **Downloadable Client**: A compiled, lightweight Windows presentation layer and local proxy.
- **Public Evaluation Gateway**: The TLS-terminated gateway enforcing Ed25519 licensing, device authorization, rate limits, and quota metering.
- **Private Processing Engine**: The isolated backend executing parsing, vector embeddings, grounded reasoning, and LLM orchestration. Evaluators have zero direct access to private backend code or LLM credentials.
