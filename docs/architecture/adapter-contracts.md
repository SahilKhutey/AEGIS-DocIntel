# Pluggable Adapter Contracts & Provider Architecture

## 1. Document Extraction Protocol

To support diverse multi-format ingestion pipelines (PDFs, DOCX, scanned TIFFs, HTML, structured Markdown), AEGIS-DocIntel decouples ingestion engines using the `ExtractionAdapter` protocol:

```python
@runtime_checkable
class ExtractionAdapter(Protocol):
    @property
    def adapter_name(self) -> str: ...

    def supports_content_type(self, content_type: str) -> bool: ...

    async def extract(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult: ...
```

### Standardized `ExtractionResult` Envelope
All parsers normalize their output into the unified `ExtractionResult` contract:
- `status`: `"success"`, `"partial"`, or `"failed"`
- `elements`: Bounding-box anchored layout objects (headings, paragraphs, headers/footers)
- `tables`: Extracted tabular matrices with row/column spans
- `warnings`: Diagnostic non-fatal warnings (e.g. OCR quality degradation)
- `errors`: Fatal processing errors
- `confidence`: Calibrated parsing confidence score $[0.0, 1.0]$

`ParserAdapterRegistry` orchestrates priority routing and automatic fallback cascading if a primary parser fails.

---

## 2. LLM Provider Protocol & Data Sovereignty

External LLM calls represent a major data exfiltration vector in enterprise environments. AEGIS-DocIntel isolates model providers via `LLMProviderAdapter`:

```python
@runtime_checkable
class LLMProviderAdapter(Protocol):
    @property
    def provider_name(self) -> str: ...

    @property
    def is_external(self) -> bool: ...

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> str: ...
```

### Sovereignty Policy Enforcement
1. Every provider explicitly reports `is_external: bool`.
2. `ModelProviderRegistry` checks the authoritative runtime flag `AEGIS_ALLOW_EXTERNAL_LLM`.
3. If `AEGIS_ALLOW_EXTERNAL_LLM=false` (the enterprise default):
   - Any attempt to resolve an external provider (e.g. OpenAI, Anthropic, Google Cloud Vertex) immediately raises `DataSovereigntyViolationError`.
   - `complete_with_failover` automatically skips prohibited external egress and falls back to compliant on-premise local inference engines (e.g. `local_llama`).

---

## 3. Prompt Injection Defense & Input Sanitization

Untrusted document text and user inputs are strictly sanitized before interpolation into reasoning prompts via `sanitize_prompt_input()`:

- **Delimiter Collisions**: Neutralizes prompt instruction escape tokens:
  `[INST]`, `[/INST]`, `<|im_start|>`, `<|im_end|>`, `[SYSTEM_PROMPT]`, ````system`.
- **Unicode Spoofing**: Strips invisible bidirectional text control sequences (`\u202A` to `\u202E`, `\u2066` to `\u2069`) used in prompt obfuscation.
- **Null Byte Injection**: Strips `\x00` characters that can disrupt C-string parsing in underlying model tokenizers.
