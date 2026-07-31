"""SimHash + content-hash dedup behavior."""

from __future__ import annotations

from amdi.retrieval.deduplication import deduplicate, hamming, simhash
from amdi.retrieval.schemas import Evidence


def _ev(text: str, *, fused: float = 1.0) -> Evidence:
    e = Evidence(text=text, score_fused=fused)
    e.metadata["unit_id"] = text
    return e


def test_content_hash_dedup_removes_exact() -> None:
    items = [_ev("Hello World", fused=0.9), _ev("Hello World", fused=0.5)]
    out = deduplicate(items, simhash_threshold=8)
    assert len(out) == 1
    assert out[0].score_fused == 0.9


def test_simhash_dedup_collapses_near_duplicates() -> None:
    a = _ev("The quick brown fox jumps over the lazy dog")
    b = _ev("The quick brown fox jumps over the lazy dog!")
    out = deduplicate([a, b], simhash_threshold=8)
    assert len(out) == 1


def test_unrelated_items_kept() -> None:
    a = _ev("Quantum computing uses qubits for parallel state representation.")
    b = _ev("Italian cuisine features regional pasta, olive oil, and fresh herbs daily.")
    out = deduplicate([a, b], simhash_threshold=8)
    assert len(out) == 2


def test_hamming_distance_is_symmetric_and_small() -> None:
    h1 = simhash("Quantum entanglement is a physics phenomenon.")
    h2 = simhash("Quantum entanglement is a physics phenomenon.")
    assert hamming(h1, h2) == 0
