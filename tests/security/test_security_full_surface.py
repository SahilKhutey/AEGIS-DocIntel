"""Every security module loads and exposes its public surface."""

from __future__ import annotations


def test_auth_roundtrip() -> None:
    from amdi.security.auth import JWTIssuer, JWTVerifier, Principal
    iss = JWTIssuer()
    tok = iss.issue(user_id="u1")
    out = JWTVerifier().verify(tok)
    assert isinstance(out, Principal)


def test_rate_limiter_importable() -> None:
    from amdi.security.rate_limit import RateLimiter, RateDecision
    assert RateDecision.__dataclass_fields__ is not None


def test_audit_chain_importable() -> None:
    from amdi.security.audit import AuditChain, AuditRecord
    assert hasattr(AuditChain, "append")


def test_rbac_and_abac_importable() -> None:
    from amdi.security.rbac import Permission, authorize
    from amdi.security.abac import owner_only


def test_crypto_roundtrip() -> None:
    from amdi.security.crypto import encrypt, decrypt
    blob = encrypt(b"hi")
    assert decrypt(blob) == b"hi"


def test_passwords_roundtrip() -> None:
    from amdi.security.passwords import hash_password, verify_password
    h = hash_password("hunter2hunter2")
    assert verify_password(h, "hunter2hunter2")
    assert not verify_password(h, "wrong")
