"""
AEGIS-DocIntel Usage Metering Service (PROT-04 WP-04.06)
Measures server-side execution units: upload bytes, LLM tokens, queries, and OCR pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TokenUsageResult:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    is_estimated: bool
    model: str
    provider: str


class UsageMeteringService:
    def __init__(self, max_file_size_bytes: int = 10 * 1024 * 1024):
        self.max_file_size_bytes = max_file_size_bytes

    def meter_file_upload(self, file_content: bytes, max_allowed_bytes: Optional[int] = None) -> int:
        """
        Validates and measures actual uploaded bytes received on server.
        Raises ValueError if payload exceeds ceiling.
        """
        limit = max_allowed_bytes if max_allowed_bytes is not None else self.max_file_size_bytes
        size_bytes = len(file_content)
        if size_bytes > limit:
            raise ValueError(
                f"File size {size_bytes} bytes exceeds maximum evaluation limit of {limit} bytes ({limit // (1024*1024)} MB)"
            )
        return size_bytes

    def meter_llm_response(
        self,
        provider: str,
        response_payload: Any,
        fallback_input_text: Optional[str] = None,
        fallback_output_text: Optional[str] = None,
    ) -> TokenUsageResult:
        """
        Extracts token usage across provider responses (OpenAI, Anthropic, Gemini, or Mock).
        Provides conservative character-based heuristic if provider metadata is unavailable.
        """
        prov_lower = provider.lower()
        model_name = "unknown"

        # 1. Inspect dict or object usage
        usage_obj = None
        if isinstance(response_payload, dict):
            usage_obj = response_payload.get("usage")
            model_name = response_payload.get("model", "unknown")
        elif hasattr(response_payload, "usage"):
            usage_obj = getattr(response_payload, "usage")
            model_name = getattr(response_payload, "model", "unknown")

        if usage_obj:
            if isinstance(usage_obj, dict):
                in_tok = usage_obj.get("input_tokens") or usage_obj.get("prompt_tokens", 0)
                out_tok = usage_obj.get("output_tokens") or usage_obj.get("completion_tokens", 0)
                tot_tok = usage_obj.get("total_tokens") or (in_tok + out_tok)
            else:
                in_tok = getattr(usage_obj, "input_tokens", getattr(usage_obj, "prompt_tokens", 0))
                out_tok = getattr(usage_obj, "output_tokens", getattr(usage_obj, "completion_tokens", 0))
                tot_tok = getattr(usage_obj, "total_tokens", in_tok + out_tok)

            return TokenUsageResult(
                input_tokens=int(in_tok),
                output_tokens=int(out_tok),
                total_tokens=int(tot_tok),
                is_estimated=False,
                model=str(model_name),
                provider=provider,
            )

        # 2. Conservative fallback heuristic (~4 chars per token)
        est_in = len(fallback_input_text or "") // 4 if fallback_input_text else 500
        est_out = len(fallback_output_text or "") // 4 if fallback_output_text else 200
        return TokenUsageResult(
            input_tokens=est_in,
            output_tokens=est_out,
            total_tokens=est_in + est_out,
            is_estimated=True,
            model=str(model_name),
            provider=provider,
        )


default_usage_metering_service = UsageMeteringService()
