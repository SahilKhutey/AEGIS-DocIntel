# Data Flow Architecture

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## Document Lifecycle Stream
1. **Intake**: Client POST `/api/v1/documents` -> Storage -> SHA-256 Checksum.
2. **Extraction**: Worker -> OCR -> Layout -> Reading Order -> Table Reconstruction.
3. **Normalization**: Token geometry normalization -> Provenance binding.
4. **Indexing**: SQLite FTS5 lexical index + Dense vector embeddings.
5. **Inference**: User Query -> Hybrid Retrieval -> Context Compiler -> Grounded Synthesis -> Verification.
