"""
aegis.corpus.integrity
======================
Cryptographic SHA-256 hashing, manifest generation, and tamper verification.
"""
from .checksum import calculate_sha256, hash_bytes
from .manifest import ChecksumManifestGenerator
from .verifier import ChecksumVerifier, IntegrityVerificationResult

__all__ = [
    "calculate_sha256",
    "hash_bytes",
    "ChecksumManifestGenerator",
    "ChecksumVerifier",
    "IntegrityVerificationResult",
]
