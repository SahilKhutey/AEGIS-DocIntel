# Database Schema & Migrations

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## Relational Tables (SQLite WAL)
- `tenants`: Multi-tenant organization boundaries.
- `users`: User identities, hashed credentials, and role assignments.
- `documents`: Document metadata, SHA-256 checksums, status, and tenant IDs.
- `pages`: Page-level extracted text, layout metadata, and dimensions.
- `jobs`: Background processing jobs, queue leases, and retry budgets.
- `audit_logs`: Immutable security and operation audit trail.
