"""
AEGIS-DocIntel — Extensible Ingestion & Provider Architecture
=============================================================
Defines standard protocols, data contracts, registries, and security controls:
- ExtractionResult contract and ExtractionAdapter protocol
- ParserAdapterRegistry with multi-format routing and fallbacks
- LLMProviderAdapter protocol with sovereignty enforcement (local vs external)
- ModelProviderRegistry with policy-driven failover
- Prompt injection defense and input sanitization
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    runtime_checkable,
)
import structlog

log = structlog.get_logger("aegis.core.adapters")


# =====================================================================
# Prompt Injection & Content Sanitization
# =====================================================================

# Dangerous delimiter tokens and markers used in prompt injection attacks
INJECTION_MARKERS = [
    re.compile(r"\[/?INST\]", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"<\|endoftext\|>", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"<\s*/\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[\s*SYSTEM_PROMPT\s*\]", re.IGNORECASE),
    re.compile(r"\[\s*/SYSTEM_PROMPT\s*\]", re.IGNORECASE),
    re.compile(r"```\s*(?:system|assistant|human)\b", re.IGNORECASE),
]

# Unicode bidirectional control characters often used to spoof text order
BIDI_CHARS_PATTERN = re.compile(r"[\u200E\u200F\u202A-\u202E\u2066-\u2069]")


def sanitize_prompt_input(text: str) -> str:
    """
    Sanitize text from documents or external inputs before interpolating into LLM prompts.
    - Strips null bytes and invisible BiDi override sequences
    - Replaces model-specific delimiter override markers with neutralized tokens
    - Preserves document linguistic semantics while neutralizing syntax injection
    """
    if not text:
        return ""

    # Strip null bytes
    sanitized = text.replace("\x00", "")

    # Strip BiDi control characters
    sanitized = BIDI_CHARS_PATTERN.sub("", sanitized)

    # Neutralize injection delimiters
    for pattern in INJECTION_MARKERS:
        sanitized = pattern.sub("[FILTERED_MARKER]", sanitized)

    return sanitized


# =====================================================================
# Document Extraction Contracts
# =====================================================================

@dataclass
class ExtractionResult:
    """Standard normalized envelope for document extraction output."""
    status: str  # "success", "partial", "failed"
    elements: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "success" and len(self.errors) == 0

    @property
    def element_count(self) -> int:
        return len(self.elements)

    @property
    def table_count(self) -> int:
        return len(self.tables)


@runtime_checkable
class ExtractionAdapter(Protocol):
    """Protocol for pluggable document parsers and extraction engines."""

    @property
    def adapter_name(self) -> str:
        """Name of the adapter."""
        ...

    def supports_content_type(self, content_type: str) -> bool:
        """Return True if this adapter supports the given MIME type."""
        ...

    async def extract(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """Execute extraction and return standardized ExtractionResult envelope."""
        ...


class ParserAdapterRegistry:
    """
    Registry for document extraction adapters.
    Supports registering multiple adapters and fallback cascades.
    """

    def __init__(self):
        self._adapters: List[ExtractionAdapter] = []

    def register(self, adapter: ExtractionAdapter) -> None:
        """Register an extraction adapter."""
        self._adapters.append(adapter)
        log.info("Registered extraction adapter", name=adapter.adapter_name)

    def get_adapter(self, content_type: str) -> Optional[ExtractionAdapter]:
        """Find the first adapter supporting the content type."""
        for adapter in self._adapters:
            if adapter.supports_content_type(content_type):
                return adapter
        return None

    def get_all_adapters(self, content_type: str) -> List[ExtractionAdapter]:
        """Return all adapters supporting the content type, in order of priority."""
        return [a for a in self._adapters if a.supports_content_type(content_type)]

    async def extract(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """
        Attempt extraction with available adapters. Cascades to fallback adapters
        if the primary adapter fails or returns partial/failed status.
        """
        candidate_adapters = self.get_all_adapters(content_type)
        if not candidate_adapters:
            return ExtractionResult(
                status="failed",
                errors=[f"No extraction adapter registered for content type '{content_type}'"],
                confidence=0.0,
            )

        collected_warnings: List[str] = []
        for adapter in candidate_adapters:
            try:
                res = await adapter.extract(file_bytes, filename, content_type, options)
                if res.is_success:
                    if collected_warnings:
                        res.warnings.extend(collected_warnings)
                    return res
                # Log warning and try fallback if available
                collected_warnings.append(
                    f"Adapter '{adapter.adapter_name}' returned status={res.status}: {'; '.join(res.errors)}"
                )
            except Exception as e:
                collected_warnings.append(f"Adapter '{adapter.adapter_name}' raised error: {str(e)}")

        # If all candidates failed, return aggregated failure
        return ExtractionResult(
            status="failed",
            warnings=collected_warnings,
            errors=[f"All registered adapters for '{content_type}' failed."],
            confidence=0.0,
        )


# =====================================================================
# LLM Provider Contracts & Sovereignty Controls
# =====================================================================

class DataSovereigntyViolationError(Exception):
    """Raised when an external LLM call is attempted while external data transfers are disabled."""
    pass


@runtime_checkable
class LLMProviderAdapter(Protocol):
    """Protocol for pluggable language model providers."""

    @property
    def provider_name(self) -> str:
        """Identifier for the provider (e.g. 'local_llama', 'openai', 'anthropic')."""
        ...

    @property
    def is_external(self) -> bool:
        """True if calling this provider transmits data outside the sovereign perimeter."""
        ...

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> str:
        """Execute text completion given sanitized prompt and system instructions."""
        ...


class ModelProviderRegistry:
    """
    Registry for LLM providers with sovereignty policy enforcement and failover.
    """

    def __init__(self, allow_external: Optional[bool] = None):
        # Default allow_external from environment variable AEGIS_ALLOW_EXTERNAL_LLM
        if allow_external is not None:
            self.allow_external = allow_external
        else:
            self.allow_external = os.getenv("AEGIS_ALLOW_EXTERNAL_LLM", "false").lower() in ("true", "1", "yes")
        self._providers: Dict[str, LLMProviderAdapter] = {}
        self._default_provider_name: Optional[str] = None

    def register(self, provider: LLMProviderAdapter, is_default: bool = False) -> None:
        """Register a model provider adapter."""
        name = provider.provider_name
        self._providers[name] = provider
        if is_default or self._default_provider_name is None:
            self._default_provider_name = name
        log.info("Registered LLM provider", name=name, is_external=provider.is_external)

    def get_provider(self, name: Optional[str] = None) -> LLMProviderAdapter:
        """
        Get provider by name (or default).
        Enforces data sovereignty policy if the provider is external.
        """
        target_name = name or self._default_provider_name
        if not target_name or target_name not in self._providers:
            raise KeyError(f"LLM provider '{target_name}' is not registered")

        provider = self._providers[target_name]
        if provider.is_external and not self.allow_external:
            raise DataSovereigntyViolationError(
                f"Provider '{provider.provider_name}' requires external network egress, "
                "which is prohibited by current data sovereignty policy (AEGIS_ALLOW_EXTERNAL_LLM=false)."
            )
        return provider

    async def complete_with_failover(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        fallback_providers: Optional[Sequence[str]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        sanitize: bool = True,
        **kwargs: Any,
    ) -> Tuple[str, str]:
        """
        Execute completion with sanitized inputs and automatic failover.
        Returns tuple of (completion_text, actual_provider_used).
        """
        clean_prompt = sanitize_prompt_input(prompt) if sanitize else prompt
        clean_system = sanitize_prompt_input(system_prompt) if (sanitize and system_prompt) else system_prompt

        candidate_names: List[str] = []
        if preferred_provider:
            candidate_names.append(preferred_provider)
        elif self._default_provider_name:
            candidate_names.append(self._default_provider_name)

        if fallback_providers:
            for fallback in fallback_providers:
                if fallback not in candidate_names:
                    candidate_names.append(fallback)

        last_error: Optional[Exception] = None
        for name in candidate_names:
            try:
                provider = self.get_provider(name)
                completion = await provider.complete(
                    prompt=clean_prompt,
                    system_prompt=clean_system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs,
                )
                return completion, name
            except DataSovereigntyViolationError:
                log.warning("Skipping external provider due to sovereignty policy", provider=name)
                last_error = DataSovereigntyViolationError(f"External provider {name} blocked by policy")
            except Exception as e:
                log.warning("Provider completion failed, evaluating fallback", provider=name, error=str(e))
                last_error = e

        raise RuntimeError(f"All candidate providers failed: {last_error}")
