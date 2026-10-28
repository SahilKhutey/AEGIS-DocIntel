"""
src/engines/intelligence/entity_resolution.py
=============================================
Deterministic entity normalization and conservative within-tenant entity resolution.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Set

# Legal entity corporate suffixes to strip during conservative canonical resolution
LEGAL_SUFFIXES = {
    "inc",
    "inc.",
    "incorporated",
    "llc",
    "l.l.c.",
    "corp",
    "corp.",
    "corporation",
    "ltd",
    "ltd.",
    "limited",
    "co",
    "co.",
    "company",
    "gmbh",
    "ag",
    "sa",
    "plc",
    "pvt ltd",
    "private limited",
}


def normalize_entity_label(label: str, strip_legal_suffixes: bool = True) -> str:
    """
    Deterministically normalize an entity name or label:
    1. NFKC Unicode normalization.
    2. Case folding.
    3. Collapse whitespace and strip punctuation.
    4. Optionally remove common legal entity suffixes (e.g., 'Acme Corp.' -> 'acme').
    """
    if not label or not isinstance(label, str):
        return ""

    # NFKC Unicode normalization
    text = unicodedata.normalize("NFKC", label).strip().lower()

    # Strip leading "the "
    if text.startswith("the "):
        text = text[4:].strip()

    # Replace hyphens, underscores, dots with spaces
    text = re.sub(r"[\-_\.]", " ", text)
    # Remove remaining punctuation except alphanumeric and space
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse multiple whitespaces
    tokens = [t for t in text.split() if t]

    if strip_legal_suffixes and tokens:
        # Check if the last 1 or 2 tokens form a known legal suffix
        if len(tokens) >= 2:
            two_word = f"{tokens[-2]} {tokens[-1]}"
            if two_word in LEGAL_SUFFIXES:
                tokens = tokens[:-2]
        if tokens and tokens[-1] in LEGAL_SUFFIXES:
            tokens = tokens[:-1]

    return " ".join(tokens)


def same_normalized_label(left: str, right: str) -> bool:
    """Check if two entity labels resolve to the same normalized entity name."""
    norm_left = normalize_entity_label(left)
    norm_right = normalize_entity_label(right)
    if not norm_left or not norm_right:
        return False
    return norm_left == norm_right


class EntityResolver:
    """
    Tenant-isolated entity resolution registry.
    Maintains custom aliases and resolves canonical entities within a single tenant.
    """

    def __init__(self) -> None:
        # Structure: tenant_id -> {alias_normalized: canonical_name}
        self._tenant_aliases: Dict[str, Dict[str, str]] = {}
        # Structure: tenant_id -> {canonical_normalized: set(aliases)}
        self._canonical_registry: Dict[str, Dict[str, Set[str]]] = {}

    def register_alias(self, tenant_id: str, canonical_name: str, alias: str) -> None:
        """Register an alias for a canonical entity within a specific tenant."""
        if not tenant_id or not canonical_name or not alias:
            return

        if tenant_id not in self._tenant_aliases:
            self._tenant_aliases[tenant_id] = {}
            self._canonical_registry[tenant_id] = {}

        norm_alias = normalize_entity_label(alias)
        norm_canonical = normalize_entity_label(canonical_name)

        if not norm_alias or not norm_canonical:
            return

        self._tenant_aliases[tenant_id][norm_alias] = canonical_name
        if norm_canonical not in self._canonical_registry[tenant_id]:
            self._canonical_registry[tenant_id][norm_canonical] = set()
        self._canonical_registry[tenant_id][norm_canonical].add(alias)

    def resolve(self, tenant_id: str, raw_entity: str) -> str:
        """
        Resolve a raw entity mention to its canonical label within the tenant.
        Returns the registered canonical entity if matched, or the normalized label.
        """
        if not raw_entity:
            return ""

        norm = normalize_entity_label(raw_entity)
        if not norm:
            return raw_entity.strip()

        # Check tenant-specific aliases
        if tenant_id in self._tenant_aliases:
            aliases = self._tenant_aliases[tenant_id]
            if norm in aliases:
                return aliases[norm]

        # Default: return normalized representation
        return norm

    def are_same_entity(self, tenant_id: str, entity_a: str, entity_b: str) -> bool:
        """Evaluate if two entity mentions refer to the same entity in tenant context."""
        res_a = self.resolve(tenant_id, entity_a)
        res_b = self.resolve(tenant_id, entity_b)
        if not res_a or not res_b:
            return False
        return res_a == res_b or same_normalized_label(res_a, res_b)

    def list_aliases(self, tenant_id: str, canonical_name: str) -> List[str]:
        """List all registered aliases for an entity in the given tenant."""
        norm_canonical = normalize_entity_label(canonical_name)
        if tenant_id in self._canonical_registry:
            return sorted(list(self._canonical_registry[tenant_id].get(norm_canonical, set())))
        return []
