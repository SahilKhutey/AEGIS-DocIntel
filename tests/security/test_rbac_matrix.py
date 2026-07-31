"""RBAC matrix smoke."""

from __future__ import annotations

from amdi.security.auth import Principal
from amdi.security.rbac import (
    Permission,
    authorize,
    permissions_for,
)


def _p(*roles: str) -> Principal:
    return Principal(user_id="u", roles=roles, scopes=(), raw={})


def test_author_can_upload() -> None:
    assert authorize(_p("author"), Permission.DOC_UPLOAD)


def test_reader_cannot_upload() -> None:
    assert not authorize(_p("reader"), Permission.DOC_UPLOAD)


def test_admin_has_full_set() -> None:
    ps = permissions_for(("admin",))
    assert Permission.DOC_UPLOAD in ps
    assert Permission.ADMIN_USERS in ps
