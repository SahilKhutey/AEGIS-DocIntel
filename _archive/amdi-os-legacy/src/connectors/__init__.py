"""
AMDI-OS AI Agent Connectors
============================

Connectors for sending AMDI-OS UEO outputs to AI agents.

Supported Agents:
    - ChatGPT       (OpenAI)       gpt-4o, gpt-4-turbo, gpt-3.5-turbo
    - Gemini        (Google)       gemini-1.5-pro, gemini-1.5-flash
    - Claude        (Anthropic)    claude-3.5-sonnet, claude-3-opus
    - DeepSeek      (DeepSeek)     deepseek-chat, deepseek-reasoner
    - Qwen          (Alibaba)      qwen-2.5, qwen-max
    - Local Models  (Ollama, etc.) llama3, mistral, qwen2, etc.

Mathematical Foundation:
    Token budget per agent:
        B_agent = max_context_tokens - safety_margin

    Response timing:
        T_total = T_request + T_processing + T_tokens / rate

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .connector_base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorResponse,
    ConnectionStatus,
)
from .connector_factory import ConnectorFactory, get_connector
from .chatgpt_connector import ChatGPTConnector
from .gemini_connector import GeminiConnector
from .claude_connector import ClaudeConnector
from .deepseek_connector import DeepSeekConnector
from .qwen_connector import QwenConnector
from .local_connector import LocalConnector
from .token_budget import AgentTokenBudget, AGENT_SPECS
from .response_parser import ResponseParser, ParsedResponse
from .exceptions import (
    ConnectorError,
    AuthenticationError,
    RateLimitError,
    TokenLimitError,
    ConnectionTimeoutError,
    InvalidResponseError,
)

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorResponse",
    "ConnectionStatus",
    "ConnectorFactory",
    "get_connector",
    "ChatGPTConnector",
    "GeminiConnector",
    "ClaudeConnector",
    "DeepSeekConnector",
    "QwenConnector",
    "LocalConnector",
    "AgentTokenBudget",
    "AGENT_SPECS",
    "ResponseParser",
    "ParsedResponse",
    "ConnectorError",
    "AuthenticationError",
    "RateLimitError",
    "TokenLimitError",
    "ConnectionTimeoutError",
    "InvalidResponseError",
]

__version__ = "1.0.0"