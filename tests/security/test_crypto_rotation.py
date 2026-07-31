"""AES-GCM round-trip + key rotation."""

from __future__ import annotations

import base64
import os

from amdi.security.crypto import decrypt, encrypt, rotate


def json_dumps(d) -> str:
    import json
    return json.dumps({k: base64.b64encode(v).decode() for k, v in d.items()})


def test_round_trip() -> None:
    pt = b"hello secret"
    env = encrypt(pt)
    assert decrypt(env) == pt


def test_rotation_keeps_old_ciphertext_decryptable(monkeypatch) -> None:
    monkeypatch.setenv("AMDI_DATA_KEYS_JSON", json_dumps({"k1": os.urandom(32)}))
    import importlib
    import amdi.security.crypto as c
    importlib.reload(c)
    try:
        old = c.encrypt(b"previous text", key_id="k1")
        c.rotate(base64.b64encode(os.urandom(32)).decode(), new_key_id="k2")
        new = c.encrypt(b"new text", key_id="k2")
        assert c.decrypt(old) == b"previous text"
        assert c.decrypt(new) == b"new text"
    finally:
        monkeypatch.delenv("AMDI_DATA_KEYS_JSON", raising=False)
        importlib.reload(c)
