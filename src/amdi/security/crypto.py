"""AES-256-GCM with key-id tagging for forward rotation."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

CURRENT_KEY_ID = "k-current"


@dataclass
class Key:
    key_id: str
    raw: bytes

    def __post_init__(self) -> None:
        if len(self.raw) != 32:
            raise ValueError(f"key {self.key_id} must be 32 bytes (AES-256)")


def _load_keys() -> dict[str, bytes]:
    raw = os.environ.get("AMDI_DATA_KEYS_JSON")
    if raw:
        d = json.loads(raw)
        return {kid: base64.b64decode(v) for kid, v in d.items()}
    seed = os.environ.get("AMDI_JWT_SECRET", "INSECURE-DEV-SECRET-CHANGE-ME")
    import hashlib
    return {CURRENT_KEY_ID: hashlib.sha256(seed.encode()).digest()}


KEYS = _load_keys()


def encrypt(plaintext: bytes, *, key_id: str | None = None) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    kid = key_id or CURRENT_KEY_ID
    if kid not in KEYS:
        raise KeyError(f"unknown key_id: {kid}")
    nonce = os.urandom(12)
    aes = AESGCM(KEYS[kid])
    ct = aes.encrypt(nonce, plaintext, associated_data=kid.encode())
    b64_kid = base64.b64encode(kid.encode()).decode()
    b64_nonce = base64.b64encode(nonce).decode()
    b64_ct = base64.b64encode(ct).decode()
    return f"{b64_kid}.{b64_nonce}.{b64_ct}"


def decrypt(envelope: str) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    parts = envelope.split(".")
    if len(parts) != 3:
        raise ValueError("invalid envelope format")
    kid = base64.b64decode(parts[0]).decode()
    nonce = base64.b64decode(parts[1])
    ct = base64.b64decode(parts[2])
    if kid not in KEYS:
        raise KeyError(f"unknown key_id on envelope: {kid}")
    aes = AESGCM(KEYS[kid])
    return aes.decrypt(nonce, ct, associated_data=kid.encode())


def rotate(new_key_b64: str, *, new_key_id: str = "k-next") -> str:
    KEYS[new_key_id] = base64.b64decode(new_key_b64)
    return new_key_id


__all__ = ["encrypt", "decrypt", "rotate", "CURRENT_KEY_ID"]
