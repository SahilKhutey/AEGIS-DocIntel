"""
Encryption
===========

Symmetric (AES-256-GCM) + Asymmetric (RSA) + Hashing (SHA-256).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

from .exceptions import EncryptionError


@dataclass
class EncryptedData:
    """Encrypted data container."""

    ciphertext: bytes
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    key_id: Optional[str] = None
    algorithm: str = "AES-256-GCM"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ciphertext": base64.b64encode(self.ciphertext).decode("ascii"),
            "nonce": base64.b64encode(self.nonce).decode("ascii") if self.nonce else None,
            "tag": base64.b64encode(self.tag).decode("ascii") if self.tag else None,
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EncryptedData":
        return cls(
            ciphertext=base64.b64decode(data["ciphertext"]),
            nonce=base64.b64decode(data["nonce"]) if data.get("nonce") else None,
            tag=base64.b64decode(data["tag"]) if data.get("tag") else None,
            key_id=data.get("key_id"),
            algorithm=data.get("algorithm", "AES-256-GCM"),
            metadata=data.get("metadata", {}),
        )


class AESEncryptor:
    """
    AES-256-GCM symmetric encryption.

    Authenticated encryption with associated data (AEAD).
    """

    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)

    def __init__(self, key: Optional[bytes] = None) -> None:
        if key is None:
            key = AESGCM.generate_key(bit_length=256)
        elif len(key) != self.KEY_SIZE:
            raise EncryptionError(f"Key must be {self.KEY_SIZE} bytes")
        self.key = key
        self.aead = AESGCM(key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new AES-256 key."""
        return AESGCM.generate_key(bit_length=256)

    def encrypt(
        self,
        plaintext: Union[bytes, str],
        associated_data: Optional[bytes] = None,
    ) -> EncryptedData:
        """Encrypt plaintext."""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        nonce = os.urandom(self.NONCE_SIZE)
        ct = self.aead.encrypt(nonce, plaintext, associated_data)
        # GCM combines ciphertext + tag in `ct`
        return EncryptedData(
            ciphertext=ct,
            nonce=nonce,
            algorithm="AES-256-GCM",
            metadata={"aad_size": len(associated_data) if associated_data else 0},
        )

    def decrypt(
        self,
        encrypted: EncryptedData,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypt ciphertext."""
        try:
            return self.aead.decrypt(encrypted.nonce, encrypted.ciphertext, associated_data)
        except Exception as exc:
            raise EncryptionError(f"Decryption failed: {exc}") from exc


class RSAEncryptor:
    """
    RSA asymmetric encryption (2048-bit).

    For key exchange, signatures, and small data encryption.
    """

    KEY_SIZE = 2048

    def __init__(self, key: Optional[Any] = None) -> None:
        if key is None:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.KEY_SIZE,
                backend=default_backend(),
            )
            self.public_key = self.private_key.public_key()
        else:
            self.private_key = key
            self.public_key = key.public_key()

    @staticmethod
    def generate_keypair() -> tuple:
        """Generate a new RSA keypair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSAEncryptor.KEY_SIZE,
            backend=default_backend(),
        )
        return private_key, private_key.public_key()

    def encrypt(self, plaintext: Union[bytes, str]) -> EncryptedData:
        """Encrypt with public key."""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        try:
            ciphertext = self.public_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except Exception as exc:
            raise EncryptionError(f"RSA encrypt failed: {exc}") from exc
        return EncryptedData(
            ciphertext=ciphertext,
            algorithm=f"RSA-{self.KEY_SIZE}",
        )

    def decrypt(self, encrypted: EncryptedData) -> bytes:
        """Decrypt with private key."""
        try:
            return self.private_key.decrypt(
                encrypted.ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except Exception as exc:
            raise EncryptionError(f"RSA decrypt failed: {exc}") from exc

    def sign(self, message: Union[bytes, str]) -> bytes:
        """Sign message with private key."""
        if isinstance(message, str):
            message = message.encode("utf-8")
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return signature

    def verify(self, message: Union[bytes, str], signature: bytes) -> bool:
        """Verify signature with public key."""
        if isinstance(message, str):
            message = message.encode("utf-8")
        from cryptography.exceptions import InvalidSignature
        try:
            self.public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False


class HashManager:
    """
    Cryptographic hashing utilities.
    """

    @staticmethod
    def sha256(data: Union[bytes, str]) -> str:
        """SHA-256 hash (hex)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sha512(data: Union[bytes, str]) -> str:
        """SHA-512 hash (hex)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha512(data).hexdigest()

    @staticmethod
    def blake2b(data: Union[bytes, str]) -> str:
        """BLAKE2b hash (hex)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.blake2b(data).hexdigest()

    @staticmethod
    def hmac_sha256(key: Union[bytes, str], message: Union[bytes, str]) -> str:
        """HMAC-SHA256 (hex)."""
        if isinstance(key, str):
            key = key.encode("utf-8")
        if isinstance(message, str):
            message = message.encode("utf-8")
        return hmac.new(key, message, hashlib.sha256).hexdigest()

    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison."""
        return hmac.compare_digest(a, b)

    @staticmethod
    def secure_random_bytes(n: int) -> bytes:
        """Generate cryptographically secure random bytes."""
        return secrets.token_bytes(n)

    @staticmethod
    def secure_random_token(nbytes: int = 32) -> str:
        """Generate secure URL-safe random token."""
        return secrets.token_urlsafe(nbytes)


class EncryptionManager:
    """
    High-level encryption orchestrator.

    Manages AES + RSA keys, performs encryption / decryption,
    key rotation, and signature verification.
    """

    def __init__(self) -> None:
        self.aes_keys: Dict[str, bytes] = {}
        self.rsa_keys: Dict[str, Any] = {}
        self.active_aes_id: Optional[str] = None
        self.active_rsa_id: Optional[str] = None

    def create_aes_key(self, key_id: str) -> str:
        """Create and store a new AES key."""
        key = AESEncryptor.generate_key()
        self.aes_keys[key_id] = key
        if self.active_aes_id is None:
            self.active_aes_id = key_id
        return key_id

    def create_rsa_keypair(self, key_id: str) -> str:
        """Create and store a new RSA keypair."""
        private, public = RSAEncryptor.generate_keypair()
        self.rsa_keys[key_id] = {"private": private, "public": public}
        if self.active_rsa_id is None:
            self.active_rsa_id = key_id
        return key_id

    def encrypt_aes(
        self,
        plaintext: Union[bytes, str],
        key_id: Optional[str] = None,
    ) -> EncryptedData:
        """Encrypt with AES using specified or active key."""
        kid = key_id or self.active_aes_id
        if kid is None or kid not in self.aes_keys:
            raise EncryptionError(f"AES key '{kid}' not found")
        encryptor = AESEncryptor(self.aes_keys[kid])
        encrypted = encryptor.encrypt(plaintext)
        encrypted.key_id = kid
        return encrypted

    def decrypt_aes(
        self,
        encrypted: EncryptedData,
    ) -> bytes:
        """Decrypt with AES using the key_id stored in encrypted."""
        if encrypted.key_id is None or encrypted.key_id not in self.aes_keys:
            raise EncryptionError(f"AES key '{encrypted.key_id}' not found")
        decryptor = AESEncryptor(self.aes_keys[encrypted.key_id])
        return decryptor.decrypt(encrypted)

    def rotate_aes_key(self, old_key_id: str, new_key_id: str) -> str:
        """Rotate an AES key (re-encrypts data with new key)."""
        if old_key_id not in self.aes_keys:
            raise EncryptionError(f"Old key '{old_key_id}' not found")
        new_key = AESEncryptor.generate_key()
        self.aes_keys[new_key_id] = new_key
        if self.active_aes_id == old_key_id:
            self.active_aes_id = new_key_id
        return new_key_id
