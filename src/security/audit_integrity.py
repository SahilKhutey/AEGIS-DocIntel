"""
AEGIS-DocIntel Audit Log Cryptographic Hash-Chain & Checkpoint Integrity Engine
Complies with PROT-04 WP-04.08 specifications.

Implements sequential cryptographic chain verification:
    H_i = SHA-256(H_{i-1} || Canonical(E_i))
Guarantees detection of historical event modification, deletion, reordering, and truncation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

GENESIS_HASH = "0" * 64
CHECKPOINT_SECRET = b"aegis-audit-external-checkpoint-root-key-2026"


def canonical_event_bytes(event_data: Dict[str, Any]) -> bytes:
    """
    Produces a deterministic, canonical JSON representation of event attributes.
    Sorts keys, uses minimal separators (no whitespace), and enforces UTF-8 encoding.
    Excludes hash envelope fields ('previous_hash', 'current_hash', 'entry_id').
    """
    clean_dict = {
        k: v for k, v in event_data.items()
        if k not in ("previous_hash", "current_hash", "entry_id")
    }

    # Normalize datetimes to ISO8601 strings
    def default_serializer(o):
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)

    return json.dumps(
        clean_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=default_serializer,
    ).encode("utf-8")


def calculate_event_hash(previous_hash: str, event_data: Dict[str, Any]) -> str:
    """
    Calculates the cryptographic digest for an event linked to its predecessor:
        H_i = SHA-256(H_{i-1} || Canonical(E_i))
    """
    prev_bytes = previous_hash.encode("ascii")
    canonical_bytes = canonical_event_bytes(event_data)
    payload = prev_bytes + canonical_bytes
    return hashlib.sha256(payload).hexdigest()


def verify_chain(events: List[Dict[str, Any]]) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Verifies the integrity of a sequence of chained audit event records.
    Returns: (is_valid, failure_index, failure_reason)
    """
    if not events:
        return True, None, "EMPTY_CHAIN"

    expected_prev = GENESIS_HASH

    for idx, ev in enumerate(events):
        curr_prev = ev.get("previous_hash")
        curr_hash = ev.get("current_hash")

        # 1. Verify link to predecessor
        if curr_prev != expected_prev:
            return False, idx, f"PREVIOUS_HASH_MISMATCH: expected '{expected_prev}', got '{curr_prev}'"

        # 2. Recompute hash over canonical content
        computed_hash = calculate_event_hash(curr_prev, ev)
        if curr_hash != computed_hash:
            return False, idx, f"CONTENT_TAMPERED: stored '{curr_hash}', computed '{computed_hash}'"

        expected_prev = curr_hash

    return True, None, "CHAIN_VALID"


def create_checkpoint(head_hash: str, event_count: int) -> Dict[str, Any]:
    """Generates an externally anchored signed checkpoint of the current audit chain head."""
    now = datetime.now(timezone.utc).isoformat()
    msg = f"AEGIS-AUDIT-CHECKPOINT-V1|{head_hash}|{event_count}|{now}".encode("utf-8")
    sig = hmac.new(CHECKPOINT_SECRET, msg, hashlib.sha256).hexdigest()
    return {
        "head_hash": head_hash,
        "event_count": event_count,
        "timestamp": now,
        "signature": sig,
    }


def verify_checkpoint(checkpoint: Dict[str, Any], current_head_hash: str, current_event_count: int) -> bool:
    """Verifies that an external checkpoint signature and head match."""
    head_hash = checkpoint.get("head_hash")
    count = checkpoint.get("event_count")
    timestamp = checkpoint.get("timestamp")
    sig = checkpoint.get("signature")

    if not (head_hash and count is not None and timestamp and sig):
        return False

    msg = f"AEGIS-AUDIT-CHECKPOINT-V1|{head_hash}|{count}|{timestamp}".encode("utf-8")
    expected_sig = hmac.new(CHECKPOINT_SECRET, msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return False

    return head_hash == current_head_hash and count == current_event_count
