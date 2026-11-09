# 10 — Security & Sovereign Data Handling

## 1. Security Architecture Principles

In sovereign enterprise document intelligence environments, handling sensitive source materials demands defense-in-depth across client-side validation, authenticated transport, and tenant boundary isolation.

```
[ User Browser ]
   │
   ├─► Pre-Flight Policy Validation (File size <= 200MB, MIME allowlist, empty check)
   │
   ├─► Client Data Sanitization (XSS filtering, file name normalization)
   │
   ├─► Authenticated Request (Bearer token, Tenant Header: dev-default-tenant)
   │
[ Reverse Proxy / API Gateway ]
   │
[ FastAPI Backend / Sovereign Enclave ]
```

---

## 2. Multi-Tenant Boundary Isolation

- **Tenant Header Injection**: All API calls initiated via `apiRequest()` (`lib/api-client.ts`) automatically inject standard authentication headers (`Authorization: Bearer <devToken>`).
- **Resource Ownership Scoping**: Every document record and background job payload includes `tenant_id`. Documents and jobs cannot be fetched, inspected, or retried across unauthorized tenant boundaries.
- **Tenant Context Preservation**: Tenant boundaries established in WP-UI-03 via the workspace selector are passed downstream to all core workspace service queries.

---

## 3. Client-Side Pre-Flight Security Checks

Before any document payload is transmitted over the network to `POST /api/v1/documents/upload`, the pure validation engine (`features/uploads/upload-validation.ts`) executes synchronous security verifications:
1. **Size Boundary Verification**: Prevents denial-of-service / resource exhaustion by strictly rejecting any file larger than `200 * 1024 * 1024` bytes.
2. **Zero-Byte File Rejection**: Rejects empty files (0 bytes) that could corrupt chunking parsers or vector indices.
3. **MIME Type Allowlisting**: Restricts acceptable MIME types strictly to supported document formats (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `text/html`, `text/plain`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). Executables, archive formats (.zip, .tar), and shell scripts are rejected client-side before transport.

---

## 4. Secure Document Preview Sandbox

1. **Format-Restricted Rendering**: Only authenticated, validated document formats (PDF, HTML) are granted preview rendering.
2. **Isolated In-Browser Preview**: Rendered previews run within isolated container elements without execution privileges for embedded scripts.
3. **Graceful Fallback for Non-Visual Formats**: Proprietary or non-visual binary formats display safe metadata and extracted text chunks rather than attempting unsafe raw binary rendering.
