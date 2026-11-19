# AEGIS-DocIntel Canonical Processing Contracts

**Document Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-10 (Section 3.3)  
**Status:** Canonical Engineering Specification  
**Classification:** Internal Core Architecture  

---

## 1. Executive Summary

This specification establishes the standardized data models and schemas for inter-engine communication in AEGIS-DocIntel. Prior iterations exhibited schema divergence where individual extraction, parsing, and retrieval components invented custom dictionary schemas. This contract standardizes:
1. Document intake identity and storage encapsulation (`DocumentSource`).
2. Structural, layout-aware content blocks (`ExtractedBlock`).
3. Pipeline execution outputs and diagnostics (`ProcessingResult`).

---

## 2. Security Invariant: Opaque Storage References

To prevent path traversal (`../../`), arbitrary file disclosure, and server-side request forgery (SSRF), client-supplied filesystem paths are strictly prohibited as storage identifiers.

### Authorized Opaque URI Schemes
- `blob://<opaque-uuid>` (Internal blob storage)
- `s3://<bucket>/<opaque-uuid>` (Object storage)
- `opaque:<sha256-or-uuid>` (Encrypted payload reference)
- `urn:amdi:blob:<id>` (Standard URN identifier)
- `sqlite:blob:<id>` (Internal relational blob store)

### Prohibited Storage Formats
- Relative directory traversals: `../`, `..\\`
- Operating system drive letters: `C:\`, `D:/`
- Absolute filesystem paths: `/etc/passwd`, `/var/data`, `\\Windows\\System32`

---

## 3. Data Contracts Specification

### 3.1 DocumentSource

Encapsulates intake metadata and points to verified, tamper-evident stored bytes.

```python
@dataclass(frozen=True, slots=True)
class DocumentSource:
    document_id: str
    tenant_id: str
    filename: str
    media_type: str
    checksum_sha256: str
    storage_reference: str
```

### 3.2 ExtractedBlock

Represents an individual structural unit of a document while preserving exact layout and section provenance.

```python
@dataclass(frozen=True, slots=True)
class ExtractedBlock:
    block_id: str
    text: str
    block_type: str  # paragraph, heading, table, header, footer, list_item, code
    page_number: int | None = None
    section_path: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 3.3 ProcessingResult

Represents the deterministic outcome of a pipeline processing stage.

```python
@dataclass(frozen=True, slots=True)
class ProcessingResult:
    document_id: str
    pipeline_version: str
    status: str
    blocks: list[ExtractedBlock]
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

## 4. Submodular Knapsack Context Optimization Contract

Retrieved `ExtractedBlock` elements are packed into context windows using the submodular knapsack optimizer (`aegis_docprep.context_packer`):
- Maximizes facility-location relevance and coverage under token budget $B$.
- Guarantees $(1 - 1/e)/2 \approx 0.316$ approximation bound.
- Prevents silent truncation: if retrieved evidence exceeds the context budget, the optimizer explicitly records rejected candidates with justification rather than silently dropping content.
