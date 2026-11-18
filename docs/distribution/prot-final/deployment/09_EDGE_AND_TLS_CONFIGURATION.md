# Edge Reverse Proxy & TLS Configuration (DEP-08)

## Caddy Configuration
Edge reverse proxy terminates TLS with modern cipher suites and enforces security headers:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self' ...`
- Strips `X-Tenant-ID` and `X-Tenant-Context` headers before proxying to gateway.
