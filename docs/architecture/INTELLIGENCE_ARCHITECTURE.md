# Intelligence Architecture

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## Retrieval & Grounding
- **Hybrid Retrieval**: Convex combination of BM25 score and vector cosine similarity:
  `Score = α * BM25 + (1 - α) * Cosine(q, d)`
- **Mathematical Context Compiler**: Packages evidence tokens into constrained context windows.
- **Citation Precision**: Automated claim decomposition verifying that every claim entails from cited tokens.
