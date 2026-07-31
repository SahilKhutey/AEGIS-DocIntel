"""Token-budget cap (helper for as_tokens and LLM token optimization)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from amdi.retrieval.schemas import Evidence


def estimate_tokens(text: str) -> int:
    # Cheap approximation: 4 chars per token; good enough for budgeting.
    return max(1, len(text) // 4)


def trim_to_budget(
    items: list["Evidence"],
    *,
    budget: int,
    shrink_factor: float = 0.9,
) -> str:
    """Serialize to a compact string that fits in `budget` tokens."""
    used = 0
    blocks: list[str] = []
    headers = sum(estimate_tokens(h) for h in ("", "[CITS] "))
    used += headers

    for ev in items:
        block = _serialize(ev)
        cost = estimate_tokens(block)
        if used + cost > budget:
            # Try a smaller version
            small = ev.text[: int(len(ev.text) * shrink_factor)]

            from amdi.retrieval.schemas import Evidence as EvClass
            block2 = _serialize(EvClass(text=small, citations=ev.citations))
            cost2 = estimate_tokens(block2)
            if used + cost2 > budget:
                break
            block = block2
        blocks.append(block)
        used += estimate_tokens(block)
    return "\n".join(blocks)


def _serialize(ev: "Evidence") -> str:
    cite = ";".join(
        f"{c.document_id}:p{c.page}" if c.page else c.document_id
        for c in ev.citations
    ) or "n/a"
    return f"{ev.text}\n[CITS] {cite}"


__all__ = ["estimate_tokens", "trim_to_budget"]
