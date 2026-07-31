# AI Agent Connectors

The AI Agent Connectors package provides unified client connectors for transmitting document context packages (using Universal Export Objects or standard RAG queries) to major LLM interfaces and local models.

## Core Features

1. **Connector Base**: Defines standard interfaces for running text completions, RAG queries, checking token budgets, and executing exponential backoff retries.
2. **Unified Response Parser**: Normalizes outputs from different agents into a consistent structure, extracting sections, references/bibliographies, citation tags, and confidence markers.
3. **Agent Token Budgets**: Tracks maximum context limits and maximum output token windows per model.
4. **Agent Connectors**:
   * **ChatGPT Connector**: Integrates with OpenAI's API (`gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`) or any OpenAI-compatible API.
   * **Gemini Connector**: Google Generative AI API (`gemini-1.5-pro`, `gemini-1.5-flash`), supporting multimodal inputs and system instructions.
   * **Claude Connector**: Anthropic Claude API (`claude-3.5-sonnet`, `claude-3-opus`).
   * **DeepSeek Connector**: DeepSeek chat models.
   * **Qwen Connector**: Alibaba DashScope Qwen models (OpenAI compatible).
   * **Local Connector**: Supports local LLM servers via Ollama HTTP API or standard OpenAI-compatible endpoints (vLLM, LM Studio, llama.cpp).
5. **Connector Factory**: A central factory for dynamic connector creation and configuration based on agent type and settings.
6. **Dry-Run/Mock Mode**: Every connector supports automatic dry-run mock fail-safes if API keys are absent or endpoints are unreachable, enabling robust offline testing and execution.

## Directory Structure

```
backend/src/connectors/
├── __init__.py
├── connector_base.py          # Base connector interface
├── connector_factory.py       # Factory for connector instantiation
├── chatgpt_connector.py       # OpenAI ChatGPT connector
├── gemini_connector.py        # Google Gemini connector
├── claude_connector.py        # Anthropic Claude connector
├── deepseek_connector.py      # DeepSeek connector
├── qwen_connector.py          # Alibaba Qwen connector
├── local_connector.py         # Local models (Ollama, llama.cpp, vLLM)
├── token_budget.py            # Per-agent token budgets
├── response_parser.py          # Unified response parser
├── exceptions.py               # Custom exceptions
└── README.md
```

## Setup & Usage

To retrieve and call a connector:

```python
from src.connectors import get_connector, ConnectorConfig

# Configure ChatGPT
config = ConnectorConfig(
    api_key="your-api-key",
    model="gpt-4o",
    temperature=0.7
)
connector = get_connector("chatgpt", config)

# Run Query
response = connector.query("Analyze the document context.")
if response.success:
    print(response.text)
```
