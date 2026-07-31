"""Password hashing — argon2id with sane parameters."""

from __future__ import annotations

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
    _PH = PasswordHasher(
        time_cost=3,
        memory_cost=64 * 1024,
        parallelism=4,
        hash_len=32,
        salt_len=16,
    )
except ImportError:  # pragma: no cover — fallback if argon2-cffi not installed
    _PH = None  # type: ignore


def hash_password(plaintext: str) -> str:
    if not plaintext:
        raise ValueError("password is empty")
    if _PH is None:
        import hashlib
        return "sha256:" + hashlib.sha256(plaintext.encode()).hexdigest()
    return _PH.hash(plaintext)


def verify_password(stored_hash: str, plaintext: str) -> bool:
    if _PH is None or stored_hash.startswith("sha256:"):
        import hashlib
        return "sha256:" + hashlib.sha256(plaintext.encode()).hexdigest() == stored_hash
    try:
        return _PH.verify(stored_hash, plaintext)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


def needs_rehash(stored_hash: str) -> bool:
    if _PH is None or stored_hash.startswith("sha256:"):
        return True
    try:
        return _PH.check_needs_rehash(stored_hash)
    except Exception:  # noqa: BLE001
        return True


__all__ = ["hash_password", "verify_password", "needs_rehash"]
