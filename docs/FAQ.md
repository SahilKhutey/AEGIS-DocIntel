# Frequently Asked Questions

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

### Q1: What makes AEGIS different from standard RAG?
Standard RAG relies on raw chunking and probabilistic vector similarity. AEGIS compiles documents into mathematical tensor spaces with explicit bounding box provenance, ensuring claims are verifiable before LLM generation.

### Q2: How does AEGIS prevent multi-tenant data leaks?
AEGIS implements fail-closed Anti-IDOR security. Any query attempting to access a resource belonging to another tenant returns HTTP 404 (Not Found) rather than 403, preventing resource enumeration and data leakage.
