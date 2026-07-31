"""Cross-method deduplication via SimHash + content-hash."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Iterable

from amdi.retrieval.schemas import Evidence


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def simhash(text: str, n_features: int = 64) -> int:
    """Classic Charikar SimHash over token n-grams."""

    toks = re.findall(r"\w+", text.lower())
    if len(toks) < 3:
        grams = [text.lower()]
    else:
        grams = [" ".join(toks[i:i+3]) for i in range(len(toks) - 2)]

    vec = [0] * n_features
    for g in grams:
        h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16)
        for i in range(n_features):
            bit = (h >> i) & 1
            vec[i] += 1 if bit else -1
    out = 0
    for i, v in enumerate(vec):
        if v > 0:
            out |= (1 << i)
    return out


def hamming(a: int, b: int) -> int:
    x = a ^ b
    return x.bit_count()


def deduplicate(
    items: Iterable[Evidence],
    *,
    simhash_threshold: int = 8,
    keep: str = "highest_fused",
) -> list[Evidence]:
    """Drop near-duplicate evidence."""

    items_list = list(items)

    # Step 1 — exact content-hash dedup
    seen_hash: dict[str, Evidence] = {}
    pre: list[Evidence] = []
    for ev in items_list:
        ch = content_hash(ev.text)
        if ch in seen_hash:
            existing = seen_hash[ch]
            if keep == "highest_fused" and ev.score_fused > existing.score_fused:
                seen_hash[ch] = ev
            continue
        seen_hash[ch] = ev
        pre.append(ev)

    # Step 2 — SimHash clustering
    bucket: dict[int, list[Evidence]] = defaultdict(list)
    h: dict[int, int] = {}
    for ev in pre:
        sh = simhash(ev.text)
        h[id(ev)] = sh
        bucket[sh].append(ev)

    kept: list[Evidence] = []
    emitted: set[int] = set()

    for _, bucket_items in sorted(bucket.items(), key=lambda x: -len(x[1])):
        for ev in bucket_items:
            if id(ev) in emitted:
                continue
            sh = h[id(ev)]
            is_dup = False
            for kept_ev in kept:
                if hamming(sh, h[id(kept_ev)]) <= simhash_threshold:
                    is_dup = True
                    break
            if is_dup:
                continue
            kept.append(ev)
            emitted.add(id(ev))
    return kept


__all__ = ["deduplicate", "simhash", "hamming", "content_hash", "normalize"]
