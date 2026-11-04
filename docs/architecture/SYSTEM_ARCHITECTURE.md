# System Architecture

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## 1. High-Level Architecture
AEGIS-DocIntel adopts a modular Clean Architecture with five core layers:
```
[ Frontend: Next.js 16 / React 19 ]
               │
               ▼ HTTP / OpenAPI 3.1
[ API Layer: FastAPI / Pydantic ]
               │
               ▼ Dependency Injection
[ Core Services Layer: Orchestration & Business Logic ]
       │                │                │
       ▼                ▼                ▼
[ Processing ]   [ Intelligence ]   [ Storage & Persistence ]
 (OCR, Layout,    (Hybrid Query,     (SQLite WAL, Blob Store,
  Table Engines)   Context Compiler)   Vector Cache)
```
