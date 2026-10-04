# Export Engine

The Export Engine provides structured context packaging, formatting, and verification for human-readable formats (JSON, Markdown, YAML) and AI-agent consumable context payloads.

## Core Features

1. **JSON Exporter**: Structured serialization of context metadata, summary, citations, and engine reports.
2. **Markdown Exporter**: Beautiful, human-readable document context layout with formatted tables, block citations, and YAML/JSON metadata blocks.
3. **YAML Exporter**: Concise key-value serialization optimal for metadata exchange and pipeline configurations.
4. **Universal Export Object (UEO)**: An agent-agnostic canonical representation of AMDI engine outputs.
5. **Agent-Specific Formatter**: Tailors the UEO to the input schema of different LLM interfaces:
   * **ChatGPT**: Structured system prompt, context, and bibliography metadata.
   * **Gemini**: Multimodal payload with tables, graphs, images, and concatenated text.
   * **Claude**: Long-context structure emphasizing summaries, semantic relationships, and references.
   * **DeepSeek**: Chat-structured system-content payloads.
   * **Qwen**: Metadata-rich chat packaging.
   * **Local**: Raw JSON/dictionary format.
6. **Token Budget Manager**: Monitors context window limits and dynamically down-scales content using proportional allocations to prevent truncation errors.
7. **Integrity Verifier**: Pre-export validation evaluating confidence thresholds, citation formatting, and hallucination heuristics (low content with high confidence).

## Directory Structure

```
backend/src/export/
├── __init__.py
├── export_engine.py           # Main orchestrator
├── json_exporter.py           # JSON format exporter
├── markdown_exporter.py       # Markdown format exporter
├── yaml_exporter.py            # YAML format exporter
├── universal_exporter.py       # Universal Export Object (UEO)
├── formatters.py               # Shared citation/table helpers
├── token_budget.py             # Agent token budget allocator
├── verification.py             # Pre-export validation layer
├── exceptions.py               # Export engine custom exceptions
└── README.md
```

## Agent Token Budgets

| Agent | Default Context Limit |
|---|---|
| Gemini 1.5 Pro | 1,000,000 |
| Gemini 1.5 Flash | 1,000,000 |
| Claude 3.5 Sonnet | 200,000 |
| Claude 3 Opus | 200,000 |
| ChatGPT-4o | 128,000 |
| ChatGPT-4 Turbo | 128,000 |
| DeepSeek-V3 | 64,000 |
| Qwen-2.5 | 32,000 |
| ChatGPT-3.5 Turbo | 16,000 |
| Local Default | 8,000 |

## Verification Logic

The pre-export verification layer performs the following checks:
* **Confidence Check**: Confirms the document processing confidence exceeds the specified minimum threshold.
* **Citations Validation**: Validates citation structure and checks that references are not empty (if required).
* **Token Budget Fit**: Ensures total estimated tokens fit within the agent's safe limit.
* **Hallucination Heuristics**: Generates warnings if high confidence scores are combined with extremely small extracted contexts.
* **Conservation Heuristics**: Generates warnings if conservation errors (from physical engines) exceed the tolerance threshold.
