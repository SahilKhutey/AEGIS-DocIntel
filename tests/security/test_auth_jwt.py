"""JWT issuance + verification + revocation."""

from __future__ import annotations

import time

import jwt
import pytest

from amdi.config import get_settings
from amdi.security.auth import (
    AuthError,
    JWTIssuer,
    JWTVerifier,
    Principal,
    VerificationFailure,
)


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    monkeypatch.setenv("AMDI_JWT_SECRET", "test-secret-with-enough-entropy-1234")
    get_settings.cache_clear()


def test_issue_then_verify_roundtrip() -> None:
    iss = JWTIssuer()
    tok = iss.issue(user_id="u1", roles=("author",), scopes=("doc:upload",))
    out = JWTVerifier().verify(tok)
    assert isinstance(out, Principal)
    assert out.user_id == "u1"
    assert "author" in out.roles


def test_expired_token_yields_expired_error() -> None:
    iss = JWTIssuer()
    tok = iss.issue(user_id="u1", ttl_seconds=-1)
    out = JWTVerifier().verify(tok)
    assert isinstance(out, VerificationFailure)
    assert out.error is AuthError.EXPIRED


def test_wrong_signature_yields_bad_signature() -> None:
    iss = JWTIssuer()
    tok = iss.issue(user_id="u1")
    forged = jwt.decode(tok, options={"verify_signature": False})
    forged["sub"] = "u2"
    tampered = jwt.encode(forged, "different-key-also-very-long-secret-32bytes!", algorithm="HS256")
    out = JWTVerifier().verify(tampered)
    assert isinstance(out, VerificationFailure)
    assert out.error is AuthError.BAD_SIGNATURE


def test_revocation_check_runs() -> None:
    iss = JWTIssuer()
    tok = iss.issue(user_id="u1")
    claims = jwt.decode(tok, "test-secret-with-enough-entropy-1234", algorithms=["HS256"], audience="amdi-cli")

    rev = lambda jti: jti == claims["jti"]
    out = JWTVerifier(revocation_check=rev).verify(tok)
    assert isinstance(out, VerificationFailure)
    assert out.error is AuthError.REVOKED



def test_missing_required_claim_rejected() -> None:
    raw = {"sub": "u1", "exp": int(time.time()) + 60}
    tok = jwt.encode(raw, "test-secret-with-enough-entropy-1234", algorithm="HS256")
    out = JWTVerifier().verify(tok)
    assert isinstance(out, VerificationFailure)
