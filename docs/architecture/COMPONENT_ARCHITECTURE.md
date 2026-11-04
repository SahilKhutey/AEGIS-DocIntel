# Component Architecture

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## 1. Subsystem Decomposition
- **`src.api`**: FastAPI routers, middleware, authentication guards.
- **`src.core`**: Tensor representations and Algebraic Evidence Language.
- **`src.engines`**: Pluggable OCR, layout, reading order, and table reconstruction engines.
- **`src.llm_service`**: Prompt packaging, grounded QA synthesis, and claim verification.
- **`src.repositories`**: SQLite WAL data access objects with ACID guarantees.
