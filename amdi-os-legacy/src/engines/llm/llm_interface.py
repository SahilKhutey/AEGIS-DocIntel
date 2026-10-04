"""
llm_interface.py
================
AEGIS-AMDI-OS — LLM Inference Interface

Thin abstraction over language-model backends that:

* Provides a **mock** provider for offline testing and CI.
* Delegates to **litellm** for any real provider (OpenAI, Anthropic,
  Cohere, Vertex AI, Azure, local Ollama, etc.) when available.
* Parses ``[N]`` citation references from the model's response.
* Computes a grounding score and a human-readable confidence label.
* Supports async streaming via :meth:`LLMInterface.stream_reason`.

Typical usage
-------------
>>> llm = LLMInterface(provider="openai", model="gpt-4o", api_key="sk-…")
>>> built = builder.build(question, retrieval_ctx)
>>> response = await llm.reason(question, built, hits, tables)
>>> print(response.answer)
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional litellm import
# ---------------------------------------------------------------------------
try:
    import litellm  # type: ignore

    _LITELLM_AVAILABLE = True
    logger.info("litellm loaded — real LLM providers available.")
except ImportError:
    litellm = None  # type: ignore
    _LITELLM_AVAILABLE = False
    logger.warning(
        "litellm is not installed — only the 'mock' provider is available. "
        "Install with: pip install litellm"
    )

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class LLMResponse:
    """
    The structured output of a single LLM inference call.

    Attributes
    ----------
    answer:
        The model's textual response.
    citations:
        List of citation dicts extracted from the answer.
        Each dict has ``{"ref": int, "text": str}`` where *text* is the
        surrounding sentence fragment.
    confidence:
        Float in [0, 1] representing the system's confidence in the answer.
    confidence_label:
        Human-readable label: ``'HIGH'``, ``'MEDIUM'``, or ``'LOW'``.
    grounded:
        ``True`` if the answer contains at least one citation AND is longer
        than 20 characters.
    model:
        The model identifier used to generate this response.
    input_tokens:
        Number of tokens in the prompt (0 if unavailable).
    output_tokens:
        Number of tokens in the completion (0 if unavailable).
    """

    answer: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    confidence_label: str = "LOW"
    grounded: bool = False
    model: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0


# ---------------------------------------------------------------------------
# LLMInterface
# ---------------------------------------------------------------------------


class LLMInterface:
    """
    Async LLM inference interface for AMDI.

    Parameters
    ----------
    llm_provider:
        Provider identifier.  Use ``'mock'`` for offline testing, or any
        provider slug supported by *litellm* (``'openai'``, ``'anthropic'``,
        ``'cohere'``, ``'ollama'``, etc.).
    model:
        Model name/identifier forwarded to the provider.
    api_key:
        API key string.  If empty the value of the relevant environment
        variable (e.g. ``OPENAI_API_KEY``) is used by litellm automatically.
    endpoint:
        Optional custom base URL for self-hosted or Azure endpoints.

    Examples
    --------
    >>> llm = LLMInterface(llm_provider="mock")
    >>> resp = await llm.reason("What is revenue?", built_ctx, hits, tables)
    >>> assert resp.grounded is False  # mock has no real citations
    """

    def __init__(
        self,
        llm_provider: str = "mock",
        model: str = "gpt-4o",
        api_key: str = "",
        endpoint: str = "",
    ) -> None:
        self._provider = llm_provider.lower().strip()
        self._model = model
        self._api_key = api_key
        self._endpoint = endpoint

        if self._provider != "mock" and not _LITELLM_AVAILABLE:
            logger.warning(
                "Provider '%s' requested but litellm is unavailable. "
                "Falling back to mock provider.",
                self._provider,
            )
            self._provider = "mock"

        logger.info(
            "LLMInterface initialised — provider=%s model=%s",
            self._provider,
            self._model,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def reason(
        self,
        question: str,
        context: Any,
        hits: Any,
        tables: Any,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Run a single-turn LLM inference call and return a structured response.

        Parameters
        ----------
        question:
            The user's question.
        context:
            A :class:`~src.engines.context.context_builder.BuiltContext`
            (or any object with a ``messages`` list and ``source_map`` dict).
        hits:
            Raw retrieval hits (used for citation enrichment; may be ``None``).
        tables:
            Structured table results (used for confidence boosting).
        **kwargs:
            Additional keyword arguments forwarded to litellm
            (e.g. ``temperature``, ``max_tokens``).

        Returns
        -------
        LLMResponse
            Structured response with answer, citations, and confidence.
        """
        messages = getattr(context, "messages", [])
        source_map: Dict[int, str] = getattr(context, "source_map", {})
        table_count: int = getattr(context, "table_count", 0)

        if self._provider == "mock":
            return self._mock_response(question, source_map, table_count)

        # Real provider via litellm
        return await self._litellm_reason(
            question=question,
            messages=messages,
            source_map=source_map,
            table_count=table_count,
            **kwargs,
        )

    async def stream_reason(
        self,
        question: str,
        context: Any,
        hits: Any,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream LLM tokens as an async generator.

        For the mock provider, words are yielded one by one with a small
        simulated delay.  For real providers, litellm's streaming interface
        is used.

        Parameters
        ----------
        question:
            The user's question.
        context:
            A :class:`~src.engines.context.context_builder.BuiltContext`.
        hits:
            Raw retrieval hits.
        **kwargs:
            Additional keyword arguments forwarded to litellm.

        Yields
        ------
        str
            Token fragments as they arrive from the model.
        """
        if self._provider == "mock":
            async for token in self._mock_stream(question):
                yield token
            return

        if not _LITELLM_AVAILABLE:
            async for token in self._mock_stream(question):
                yield token
            return

        messages = getattr(context, "messages", [])
        model_id = self._build_model_id()
        try:
            stream = await litellm.acompletion(
                model=model_id,
                messages=messages,
                stream=True,
                api_key=self._api_key or None,
                base_url=self._endpoint or None,
                **kwargs,
            )
            async for chunk in stream:
                delta = (
                    chunk.choices[0].delta.content
                    if chunk.choices and chunk.choices[0].delta
                    else None
                )
                if delta:
                    yield delta
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("litellm stream error: %s", exc)
            yield f"[ERROR: {exc}]"

    # ------------------------------------------------------------------
    # Private — mock provider
    # ------------------------------------------------------------------

    def _mock_response(
        self,
        question: str,
        source_map: Dict[int, str],
        table_count: int,
    ) -> LLMResponse:
        """
        Generate a deterministic mock response for testing.

        The mock answer acknowledges the question and lists available
        source references so that downstream citation logic can be
        exercised without a live LLM.

        Parameters
        ----------
        question:
            The user's question.
        source_map:
            Mapping of citation numbers to element IDs.
        table_count:
            Number of table elements in the context.

        Returns
        -------
        LLMResponse
        """
        source_refs = " ".join(f"[{n}]" for n in sorted(source_map)) if source_map else ""
        answer = (
            f"[MOCK] Based on the provided documents, here is a synthesised "
            f"answer to: \"{question}\". "
            f"The relevant information was found in the following sources: "
            f"{source_refs if source_refs else '(no sources available)'}. "
            f"This is a mock response generated without a live language model."
        )
        citations = self._parse_citations(answer)
        grounded = bool(citations) and len(answer) > 20
        has_table = table_count > 0

        confidence = self._compute_confidence(grounded, has_table)
        label = self._confidence_label(confidence)

        logger.debug("Mock LLMResponse generated — citations=%d", len(citations))
        return LLMResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            confidence_label=label,
            grounded=grounded,
            model="mock",
            input_tokens=0,
            output_tokens=0,
        )

    @staticmethod
    async def _mock_stream(question: str) -> AsyncIterator[str]:
        """
        Yield words of the mock answer one by one with a 30 ms delay.

        Parameters
        ----------
        question:
            The user's question (embedded in the mock answer).

        Yields
        ------
        str
            Individual word tokens followed by spaces.
        """
        answer = (
            f"[MOCK STREAM] Streaming answer to: \"{question}\". "
            "This simulates token-by-token output from a language model."
        )
        for word in answer.split():
            yield word + " "
            await asyncio.sleep(0.03)

    # ------------------------------------------------------------------
    # Private — litellm provider
    # ------------------------------------------------------------------

    async def _litellm_reason(
        self,
        question: str,
        messages: List[Dict[str, str]],
        source_map: Dict[int, str],
        table_count: int,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Call litellm.acompletion and parse the response into an LLMResponse.

        Parameters
        ----------
        question:
            The original question (for logging).
        messages:
            OpenAI-style message list.
        source_map:
            Mapping of citation numbers to element IDs.
        table_count:
            Number of table elements in the context.
        **kwargs:
            Forwarded to litellm.acompletion.

        Returns
        -------
        LLMResponse
        """
        model_id = self._build_model_id()
        logger.info("litellm.acompletion — model=%s messages=%d", model_id, len(messages))

        try:
            response = await litellm.acompletion(
                model=model_id,
                messages=messages,
                api_key=self._api_key or None,
                base_url=self._endpoint or None,
                **kwargs,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("litellm.acompletion failed: %s", exc)
            return LLMResponse(
                answer=f"[LLM ERROR: {exc}]",
                citations=[],
                confidence=0.0,
                confidence_label="LOW",
                grounded=False,
                model=model_id,
                input_tokens=0,
                output_tokens=0,
            )

        # Extract answer text
        answer = ""
        try:
            answer = response.choices[0].message.content or ""
        except Exception:  # pylint: disable=broad-except
            logger.warning("Could not extract answer text from litellm response.")

        # Token usage
        input_tokens = 0
        output_tokens = 0
        try:
            usage = response.usage
            if usage:
                input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage, "completion_tokens", 0) or 0
        except Exception:  # pylint: disable=broad-except
            pass

        citations = self._parse_citations(answer)
        grounded = bool(citations) and len(answer) > 20
        has_table = table_count > 0

        confidence = self._compute_confidence(grounded, has_table)
        label = self._confidence_label(confidence)

        logger.info(
            "LLMResponse — model=%s input_tokens=%d output_tokens=%d "
            "citations=%d grounded=%s confidence=%.2f",
            model_id,
            input_tokens,
            output_tokens,
            len(citations),
            grounded,
            confidence,
        )

        return LLMResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            confidence_label=label,
            grounded=grounded,
            model=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    # ------------------------------------------------------------------
    # Private — helpers
    # ------------------------------------------------------------------

    def _build_model_id(self) -> str:
        """
        Construct the litellm model identifier string.

        For providers other than OpenAI, litellm requires the format
        ``<provider>/<model>`` (e.g. ``anthropic/claude-3-opus-20240229``).

        Returns
        -------
        str
        """
        if self._provider in {"openai", "mock", ""}:
            return self._model
        return f"{self._provider}/{self._model}"

    @staticmethod
    def _parse_citations(text: str) -> List[Dict[str, Any]]:
        """
        Extract ``[N]`` citation references from *text*.

        For each citation found, the surrounding sentence fragment (up to
        80 characters on each side) is captured as context.

        Parameters
        ----------
        text:
            Model output text to scan for citation markers.

        Returns
        -------
        list[dict]
            List of ``{"ref": int, "text": str}`` dicts, one per unique
            citation number found.

        Examples
        --------
        >>> LLMInterface._parse_citations("Revenue grew 10% [1] year-over-year [2].")
        [{"ref": 1, "text": "Revenue grew 10% [1] year-over-year [2]."}, ...]
        """
        pattern = re.compile(r"\[(\d+)\]")
        citations: List[Dict[str, Any]] = []
        seen: set = set()

        for match in pattern.finditer(text):
            ref_num = int(match.group(1))
            if ref_num in seen:
                continue
            seen.add(ref_num)

            # Capture surrounding context
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            surrounding = text[start:end].strip()

            citations.append({"ref": ref_num, "text": surrounding})

        logger.debug("_parse_citations found %d citations", len(citations))
        return citations

    @staticmethod
    def _compute_confidence(grounded: bool, has_table_answer: bool) -> float:
        """
        Compute a scalar confidence score.

        Rules
        -----
        * Grounded answer + table answer → 0.95 (highest confidence)
        * Grounded answer only           → 0.80 (medium-high)
        * Not grounded                   → 0.50 (low)

        Parameters
        ----------
        grounded:
            Whether the answer contains at least one citation and is
            longer than 20 characters.
        has_table_answer:
            Whether at least one direct table answer was included in the
            context.

        Returns
        -------
        float
        """
        if grounded and has_table_answer:
            return 0.95
        if grounded:
            return 0.80
        return 0.50

    @staticmethod
    def _confidence_label(conf: float) -> str:
        """
        Map a confidence float to a human-readable label.

        Thresholds
        ----------
        * ≥ 0.85 → ``'HIGH'``
        * ≥ 0.65 → ``'MEDIUM'``
        * < 0.65 → ``'LOW'``

        Parameters
        ----------
        conf:
            Confidence value in [0, 1].

        Returns
        -------
        str
            One of ``'HIGH'``, ``'MEDIUM'``, ``'LOW'``.
        """
        if conf >= 0.85:
            return "HIGH"
        if conf >= 0.65:
            return "MEDIUM"
        return "LOW"
