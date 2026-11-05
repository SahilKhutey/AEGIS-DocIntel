"""
aegis.corpus.integrity.verifier
===============================
Verifies disk artifact integrity against committed SHA-256 manifests,
detecting tampering, missing files, and unregistered files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from .checksum import calculate_sha256
from .manifest import ChecksumManifest


class IntegrityVerificationResult(BaseModel):
    is_valid: bool
    total_manifest_artifacts: int
    verified_count: int
    missing_files: List[str] = Field(default_factory=list)
    tampered_files: List[Dict[str, str]] = Field(default_factory=list)
    unregistered_files: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ChecksumVerifier:
    """Rigorous verification engine for dataset integrity."""

    @classmethod
    def verify_directory(
        cls,
        manifest: ChecksumManifest,
        corpus_root: Path | str,
        detect_unregistered: bool = True,
    ) -> IntegrityVerificationResult:
        root = Path(corpus_root)
        missing: List[str] = []
        tampered: List[Dict[str, str]] = []
        verified_count = 0
        expected_paths: Set[str] = set()

        for art in manifest.artifacts:
            file_path = root / art.path
            # Also allow matching by filename directly in root or subdirs
            if not file_path.is_file():
                alt_path = root / art.filename
                if alt_path.is_file():
                    file_path = alt_path

            if not file_path.is_file():
                missing.append(art.path)
                continue

            expected_paths.add(file_path.resolve().as_posix())

            try:
                actual_hash = calculate_sha256(file_path)
                if actual_hash.lower() != art.sha256.lower():
                    tampered.append({
                        "document_id": art.document_id,
                        "path": art.path,
                        "expected_sha256": art.sha256,
                        "actual_sha256": actual_hash,
                    })
                else:
                    verified_count += 1
            except Exception as e:
                tampered.append({
                    "document_id": art.document_id,
                    "path": art.path,
                    "expected_sha256": art.sha256,
                    "actual_sha256": f"ERROR: {e}",
                })

        # Detect unregistered files if requested
        unregistered: List[str] = []
        if detect_unregistered and root.is_dir():
            for p in root.rglob("*"):
                if p.is_file() and not p.name.endswith((".json", ".sha256", ".csv", ".md")):
                    resolved_posix = p.resolve().as_posix()
                    if resolved_posix not in expected_paths:
                        unregistered.append(str(p.relative_to(root)))

        is_valid = len(missing) == 0 and len(tampered) == 0 and len(unregistered) == 0

        errors: List[str] = []
        if missing:
            errors.append(f"{len(missing)} manifest artifact(s) missing from disk")
        if tampered:
            errors.append(f"{len(tampered)} artifact(s) failed cryptographic checksum verification (tampered)")
        if unregistered:
            errors.append(f"{len(unregistered)} unregistered file(s) detected in corpus directory")

        return IntegrityVerificationResult(
            is_valid=is_valid,
            total_manifest_artifacts=len(manifest.artifacts),
            verified_count=verified_count,
            missing_files=missing,
            tampered_files=tampered,
            unregistered_files=unregistered,
            errors=errors,
        )
