"""
aegis.corpus.partition.leakage
==============================
Leakage detection engine verifying partition independence across exact IDs,
content hashes, document families, and text similarity.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from aegis.corpus.partition.grouping import DocumentGrouper, GroupableDocument
from aegis.corpus.partition.splitter import PartitionManifest


class LeakageReport(BaseModel):
    status: str = Field(..., pattern=r"^(PASSED|FAILED)$")
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == "PASSED"


def _tokenize_3grams(text: str) -> Set[str]:
    """Generate word 3-grams for fast near-duplicate text similarity estimation."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < 3:
        return set(words)
    return {f"{words[i]}_{words[i+1]}_{words[i+2]}" for i in range(len(words) - 2)}


def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


class LeakageDetector:
    """Verifies that partitions maintain strict boundaries and contain zero data leakage."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def audit_partitions(
        self,
        manifest: PartitionManifest,
        documents: List[GroupableDocument],
        check_near_duplicates: bool = True
    ) -> LeakageReport:
        """Run all leakage detection checks on a partitioned corpus."""
        violations: List[str] = []
        warnings: List[str] = []

        dev_ids = set(manifest.partitions.development)
        val_ids = set(manifest.partitions.validation)
        holdout_ids = set(manifest.partitions.holdout)

        doc_by_id = {d.document_id: d for d in documents}

        # 1. Exact ID Overlap Check
        dev_val_overlap = dev_ids.intersection(val_ids)
        if dev_val_overlap:
            violations.append(f"Exact ID overlap between dev and val: {sorted(list(dev_val_overlap))}")

        dev_holdout_overlap = dev_ids.intersection(holdout_ids)
        if dev_holdout_overlap:
            violations.append(f"Exact ID overlap between dev and holdout: {sorted(list(dev_holdout_overlap))}")

        val_holdout_overlap = val_ids.intersection(holdout_ids)
        if val_holdout_overlap:
            violations.append(f"Exact ID overlap between val and holdout: {sorted(list(val_holdout_overlap))}")

        # 2. SHA-256 Hash Duplicate Check
        dev_hashes = {doc_by_id[did].sha256: did for did in dev_ids if did in doc_by_id and doc_by_id[did].sha256}
        val_hashes = {doc_by_id[did].sha256: did for did in val_ids if did in doc_by_id and doc_by_id[did].sha256}
        holdout_hashes = {doc_by_id[did].sha256: did for did in holdout_ids if did in doc_by_id and doc_by_id[did].sha256}

        dev_val_hash_overlap = set(dev_hashes.keys()).intersection(set(val_hashes.keys()))
        if dev_val_hash_overlap:
            violations.append(f"Content hash collision between dev and val ({len(dev_val_hash_overlap)} hashes)")

        dev_holdout_hash_overlap = set(dev_hashes.keys()).intersection(set(holdout_hashes.keys()))
        if dev_holdout_hash_overlap:
            violations.append(f"CRITICAL: Content hash collision between dev and holdout ({len(dev_holdout_hash_overlap)} hashes)")

        val_holdout_hash_overlap = set(val_hashes.keys()).intersection(set(holdout_hashes.keys()))
        if val_holdout_hash_overlap:
            violations.append(f"Content hash collision between val and holdout ({len(val_holdout_hash_overlap)} hashes)")

        # 3. Family Contamination Check
        if manifest.grouping_key == "family":
            dev_families = {
                (doc_by_id[did].family or DocumentGrouper.infer_family(did, doc_by_id[did].title))
                for did in dev_ids if did in doc_by_id
            }
            holdout_families = {
                (doc_by_id[did].family or DocumentGrouper.infer_family(did, doc_by_id[did].title))
                for did in holdout_ids if did in doc_by_id
            }
            family_overlap = dev_families.intersection(holdout_families)
            if family_overlap:
                violations.append(f"Document family contamination between dev and holdout: {sorted(list(family_overlap))}")

        # 4. Text Near-Duplicate Check
        if check_near_duplicates:
            holdout_tokens = {
                did: _tokenize_3grams(doc_by_id[did].text_content or doc_by_id[did].title or "")
                for did in holdout_ids if did in doc_by_id
            }
            dev_tokens = {
                did: _tokenize_3grams(doc_by_id[did].text_content or doc_by_id[did].title or "")
                for did in dev_ids if did in doc_by_id
            }

            for h_id, h_set in holdout_tokens.items():
                if len(h_set) < 5:
                    continue
                for d_id, d_set in dev_tokens.items():
                    if len(d_set) < 5:
                        continue
                    sim = _jaccard_similarity(h_set, d_set)
                    if sim > self.similarity_threshold:
                        msg = f"Near-duplicate text detected between holdout ({h_id}) and dev ({d_id}): similarity={sim:.3f}"
                        warnings.append(msg)

        status = "FAILED" if violations else "PASSED"

        # Update manifest status if passed
        if status == "PASSED":
            manifest.leakage_check_status = "PASSED"
        else:
            manifest.leakage_check_status = "FAILED"

        return LeakageReport(
            status=status,
            violations=violations,
            warnings=warnings,
            metrics={
                "total_documents": len(documents),
                "development_count": len(dev_ids),
                "validation_count": len(val_ids),
                "holdout_count": len(holdout_ids),
                "violations_count": len(violations),
                "warnings_count": len(warnings),
            }
        )
