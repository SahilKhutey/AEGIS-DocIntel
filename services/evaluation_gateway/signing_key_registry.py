"""
AEGIS-DocIntel Evaluation Gateway — Signing Key Registry
Implements PROT-04 WP-04.04 specifications:
- Server-side Ed25519 signing key lifecycle management
- States: ACTIVE_SIGNING, VERIFY_ONLY, RETIRED, COMPROMISED
- Key rotation and transition procedures
- Emergency compromise invalidation response (LIC-026)
- Public verification key registry (no private keys distributed to clients)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

DEFAULT_KEYS_DIR = Path(__file__).resolve().parent / "keys"
DEFAULT_KEY_ID = "aegis-license-ed25519-2026-01"
CANONICAL_ALGORITHM = "EdDSA"


@dataclass
class SigningKeyRecord:
    key_id: str
    algorithm: str
    private_key: Optional[ed25519.Ed25519PrivateKey]
    public_key: ed25519.Ed25519PublicKey
    public_key_pem: str
    status: str  # ACTIVE_SIGNING, VERIFY_ONLY, RETIRED, COMPROMISED
    created_at: float
    activated_at: float
    retired_at: Optional[float] = None
    compromised_at: Optional[float] = None


class SigningKeyRegistry:
    def __init__(self, keys_dir: Optional[Path] = None):
        self.keys_dir = keys_dir or DEFAULT_KEYS_DIR
        self._keys: Dict[str, SigningKeyRecord] = {}
        self._active_key_id: Optional[str] = None
        self._lock = threading.Lock()
        self._init_default_keys()

    def _init_default_keys(self) -> None:
        """Initializes default root signing key from secure directory or generates fallback."""
        priv_path = self.keys_dir / "private-key.pem"
        pub_path = self.keys_dir / "public-key.pem"

        now = time.time()
        if priv_path.exists() and pub_path.exists():
            try:
                priv = serialization.load_pem_private_key(priv_path.read_bytes(), password=None)
                pub = serialization.load_pem_public_key(pub_path.read_bytes())
                if isinstance(priv, ed25519.Ed25519PrivateKey) and isinstance(pub, ed25519.Ed25519PublicKey):
                    pub_pem = pub.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    ).decode("ascii")
                    record = SigningKeyRecord(
                        key_id=DEFAULT_KEY_ID,
                        algorithm=CANONICAL_ALGORITHM,
                        private_key=priv,
                        public_key=pub,
                        public_key_pem=pub_pem,
                        status="ACTIVE_SIGNING",
                        created_at=now,
                        activated_at=now,
                    )
                    self._keys[DEFAULT_KEY_ID] = record
                    self._active_key_id = DEFAULT_KEY_ID
                    # Also register key-ed25519-v1 alias for backward compatibility
                    self._keys["key-ed25519-v1"] = record
                    return
            except Exception:
                pass

        # Ephemeral fallback for test/isolated execution
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        pub_pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        record = SigningKeyRecord(
            key_id=DEFAULT_KEY_ID,
            algorithm=CANONICAL_ALGORITHM,
            private_key=priv,
            public_key=pub,
            public_key_pem=pub_pem,
            status="ACTIVE_SIGNING",
            created_at=now,
            activated_at=now,
        )
        self._keys[DEFAULT_KEY_ID] = record
        self._active_key_id = DEFAULT_KEY_ID
        self._keys["key-ed25519-v1"] = record

    def get_active_signing_key(self) -> SigningKeyRecord:
        """Returns the currently active key authorized for signing new licenses."""
        with self._lock:
            if not self._active_key_id or self._active_key_id not in self._keys:
                raise RuntimeError("No active signing key configured in key registry.")
            record = self._keys[self._active_key_id]
            if record.status != "ACTIVE_SIGNING":
                raise RuntimeError(f"Current active key '{record.key_id}' is in status '{record.status}', cannot sign.")
            return record

    def get_verification_key(self, key_id: str) -> Optional[SigningKeyRecord]:
        """Resolves key record for verification. Returns record if found."""
        with self._lock:
            return self._keys.get(key_id)

    def rotate_key(self, new_key_id: Optional[str] = None) -> SigningKeyRecord:
        """
        Executes key rotation:
        - Demotes current ACTIVE_SIGNING key to VERIFY_ONLY (allowing existing licenses to verify).
        - Generates and activates a new Ed25519 key pair for future signings.
        """
        with self._lock:
            now = time.time()
            # Demote old active key to VERIFY_ONLY
            if self._active_key_id and self._active_key_id in self._keys:
                old = self._keys[self._active_key_id]
                if old.status == "ACTIVE_SIGNING":
                    old.status = "VERIFY_ONLY"
                    old.retired_at = now

            # Generate new key pair
            kid = new_key_id or f"aegis-license-ed25519-{int(now)}"
            priv = ed25519.Ed25519PrivateKey.generate()
            pub = priv.public_key()
            pub_pem = pub.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("ascii")

            new_record = SigningKeyRecord(
                key_id=kid,
                algorithm=CANONICAL_ALGORITHM,
                private_key=priv,
                public_key=pub,
                public_key_pem=pub_pem,
                status="ACTIVE_SIGNING",
                created_at=now,
                activated_at=now,
            )
            self._keys[kid] = new_record
            self._active_key_id = kid
            return new_record

    def compromise_key(self, key_id: str) -> None:
        """
        Emergency response: Marks a signing key as COMPROMISED.
        Immediately denies any license verified with this key.
        """
        with self._lock:
            now = time.time()
            if key_id not in self._keys:
                raise KeyError(f"Key '{key_id}' not found in registry.")
            rec = self._keys[key_id]
            rec.status = "COMPROMISED"
            rec.compromised_at = now
            if self._active_key_id == key_id:
                self._active_key_id = None

    def retire_key(self, key_id: str) -> None:
        """Marks a key as RETIRED (no longer verified or signed)."""
        with self._lock:
            now = time.time()
            if key_id not in self._keys:
                raise KeyError(f"Key '{key_id}' not found in registry.")
            rec = self._keys[key_id]
            rec.status = "RETIRED"
            rec.retired_at = now

    def list_keys(self) -> List[Dict[str, Any]]:
        """Returns non-sensitive metadata for all registered keys."""
        with self._lock:
            return [
                {
                    "key_id": k.key_id,
                    "algorithm": k.algorithm,
                    "status": k.status,
                    "created_at": k.created_at,
                    "activated_at": k.activated_at,
                    "retired_at": k.retired_at,
                    "compromised_at": k.compromised_at,
                    "public_key_pem": k.public_key_pem,
                }
                for k in self._keys.values()
                if k.key_id != "key-ed25519-v1" or len(self._keys) == 1  # filter alias in list
            ]

    def reset(self) -> None:
        """Resets registry to baseline state (for test isolation)."""
        with self._lock:
            self._keys.clear()
            self._active_key_id = None
            self._init_default_keys()


# Global signing key registry instance
key_registry = SigningKeyRegistry()
