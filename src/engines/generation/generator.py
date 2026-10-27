"""
src/engines/generation/generator.py
===================================
Provider-neutral generation interface and adapter protocol.
"""

from __future__ import annotations

from typing import Protocol


class ModelGenerationError(RuntimeError):
    """The configured model could not produce a usable response."""


class TextModel(Protocol):
    """Protocol for model inference clients."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """Return raw model output, preferably constrained to JSON."""
        ...


class AnswerGenerator:
    """Orchestrates interaction with an underlying TextModel implementation."""

    def __init__(
        self,
        model: TextModel,
        *,
        max_output_tokens: int = 1500,
    ) -> None:
        if max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        self._model = model
        self._max_output_tokens = max_output_tokens

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> str:
        """Invoke the model provider and return the raw generated text response."""
        try:
            output = self._model.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_output_tokens=self._max_output_tokens,
            )
        except Exception as exc:
            raise ModelGenerationError(f"Underlying model generation failed: {exc}") from exc

        if not isinstance(output, str):
            raise ModelGenerationError(f"Model returned non-string response: {type(output)}")

        if not output.strip():
            raise ModelGenerationError("Model returned empty response")

        return output
