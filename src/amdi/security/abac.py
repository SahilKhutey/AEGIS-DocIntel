"""Attribute-Based Access Control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from amdi.security.auth import Principal


@dataclass(slots=True)
class ResourceAttrs:
    document_id: str | None = None
    owner_id: str | None = None
    classification: str = "internal"


Rule = Callable[[Principal, ResourceAttrs], bool]


def owner_only(principal: Principal, res: ResourceAttrs) -> bool:
    return res.owner_id is not None and res.owner_id == principal.user_id


def admin_only(principal: Principal, res: ResourceAttrs) -> bool:
    return "admin" in principal.roles


def classification_at_most(max_class: str) -> Rule:
    order = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
    cap = order[max_class]

    def _rule(p: Principal, res: ResourceAttrs) -> bool:
        return order.get(res.classification, 99) <= cap
    return _rule


def all_of(rules: Iterable[Rule]) -> Rule:
    rules_list = list(rules)
    def _rule(p: Principal, res: ResourceAttrs) -> bool:
        return all(r(p, res) for r in rules_list)
    return _rule


def any_of(rules: Iterable[Rule]) -> Rule:
    rules_list = list(rules)
    def _rule(p: Principal, res: ResourceAttrs) -> bool:
        return any(r(p, res) for r in rules_list)
    return _rule


__all__ = [
    "ResourceAttrs", "Rule",
    "owner_only", "admin_only", "classification_at_most",
    "all_of", "any_of",
]
