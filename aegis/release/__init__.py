"""
aegis.release
=============
Release management, metadata validation, and release gate verification.
"""
from .metadata_validator import ReleaseMetadataValidator
from .release_gate import ReleaseGateChecker

__all__ = ["ReleaseMetadataValidator", "ReleaseGateChecker"]
