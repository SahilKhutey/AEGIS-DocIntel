# Security Architecture

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## Defense-in-Depth
1. **Identity**: JWT with RS256 / HS256 signatures, short expiration, token revocation.
2. **Authorization**: Strict RBAC (Admin, Analyst, Editor, Viewer).
3. **Isolation**: Anti-IDOR cross-tenant barriers returning HTTP 404.
4. **Privacy**: Regex and NLP-based PII masking for SSN, credit cards, emails, and API keys.
