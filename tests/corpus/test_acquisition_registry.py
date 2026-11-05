"""
tests/corpus/test_acquisition_registry.py
========================================
Tests verifying acquisition approval rules, usage limitation enforcement,
and rejection of unapproved / pending sources.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from aegis.corpus.models import ReviewStatus
from aegis.corpus.registry.acquisition_registry import AcquisitionRegistry
from aegis.corpus.registry.source_registry import SourceRegistry

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_CONFIG = REPO_ROOT / "configs" / "corpus" / "sources.yaml"
ACQ_CONFIG = REPO_ROOT / "configs" / "corpus" / "acquisition_decisions.yaml"


@pytest.fixture
def acq_registry():
    src_reg = SourceRegistry(SOURCES_CONFIG)
    return AcquisitionRegistry(ACQ_CONFIG, source_registry=src_reg)


def test_acq_001_load_decisions(acq_registry):
    """ACQ-001: Acquisition registry loads all formal decisions."""
    decisions = acq_registry.list_all()
    assert len(decisions) >= 10
    assert acq_registry.get_by_source("SRC-DOCLAYNET-001") is not None
    assert acq_registry.get_by_source("SRC-WORLDBANK-001") is not None


def test_acq_002_approved_source_evaluation_permitted(acq_registry):
    """ACQ-002: Approved source is permitted for evaluation."""
    permitted, msg = acq_registry.is_acquisition_permitted("SRC-DOCLAYNET-001", "evaluate")
    assert permitted is True
    assert msg == "APPROVED"


def test_acq_003_rejected_source_blocked(acq_registry):
    """ACQ-003: Rejected source is strictly blocked from acquisition and evaluation."""
    permitted, msg = acq_registry.is_acquisition_permitted("SRC-UNREVIEWED-001", "evaluate")
    assert permitted is False
    assert "REJECTED" in msg


def test_acq_004_conditional_source_prohibited_use(acq_registry):
    """ACQ-004: Conditional source blocks prohibited activities (e.g. standalone redistribution)."""
    # FUNSD permits evaluation
    perm_eval, _ = acq_registry.is_acquisition_permitted("SRC-FUNSD-001", "evaluate")
    assert perm_eval is True

    # FUNSD prohibits standalone commercial redistribution
    perm_redis, msg = acq_registry.is_acquisition_permitted("SRC-FUNSD-001", "standalone_commercial_redistribution")
    assert perm_redis is False
    assert "PROHIBITED" in msg


def test_acq_005_unknown_source_blocked(acq_registry):
    """ACQ-005: Source without a recorded acquisition decision is blocked."""
    permitted, msg = acq_registry.is_acquisition_permitted("SRC-GHOST-999", "evaluate")
    assert permitted is False
    assert "no recorded acquisition decision" in msg
