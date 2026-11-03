"""
tests.intelligence.facts.test_facts_and_conflicts
=================================================
Unit and regression tests for WP-06.05 Fact Extraction and Cross-Document Conflict Detection.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.conflicts import ConflictComparator
from aegis.intelligence.facts import FactExtractor
from aegis.intelligence.models import (
    ConflictClassification,
    EntityRef,
    FactEvidence,
    FactItem,
    FactObject,
    FactQualifiers,
)


@pytest.fixture
def fact_schema():
    return json.loads(Path("schemas/intelligence/fact.schema.json").read_text(encoding="utf-8"))


@pytest.fixture
def conflict_schema():
    return json.loads(Path("schemas/intelligence/conflict.schema.json").read_text(encoding="utf-8"))


def test_fact_001_fact_extraction_and_raw_preservation():
    """FACT-001: Extract typed facts while preserving verbatim raw strings."""
    text = "Global Infrastructure Bank reported revenue was $450 million in FY2024."
    facts = FactExtractor.extract_from_passage("DOC-001", text, page_number=1, reporting_period="FY2024")
    assert len(facts) >= 1
    f = facts[0]
    assert f.predicate == "reported_budget"
    assert f.object.raw_value == "$450 million"
    assert f.object.unit == "USD"
    assert f.object.value == 450


def test_fact_002_evidence_grounding():
    """FACT-002: Extracted facts retain exact source document and evidence quote."""
    text = "Total workforce headcount reached 4,250 personnel as of December 2024."
    facts = FactExtractor.extract_from_passage("DOC-002", text, page_number=3)
    assert len(facts) >= 1
    f = facts[0]
    assert f.evidence[0].document_id == "DOC-002"
    assert f.evidence[0].page_number == 3
    assert "4,250" in f.evidence[0].quoted_text


def test_fact_003_conflict_identical_values_no_conflict():
    """FACT-003: Corroborating identical values across documents classify as NO_CONFLICT."""
    f1 = FactItem(
        fact_id="F1",
        subject=EntityRef(entity_id="E1", name="Project Orion", type="project"),
        predicate="budget",
        object=FactObject(value=650, raw_value="650 lakh", unit="INR", data_type="currency"),
        qualifiers=FactQualifiers(reporting_period="2024"),
        evidence=[FactEvidence(document_id="DOC-A", page_number=1)],
    )
    f2 = f1.model_copy(update={"fact_id": "F2", "evidence": [FactEvidence(document_id="DOC-B", page_number=2)]})

    conf = ConflictComparator.compare_facts(f1, f2)
    assert conf is not None
    assert conf.classification == ConflictClassification.NO_CONFLICT


def test_fact_004_conflict_temporal_difference():
    """FACT-004: Values differing across periods classify as TEMPORAL_DIFFERENCE, not contradiction."""
    f1 = FactItem(
        fact_id="F1",
        subject=EntityRef(entity_id="E1", name="Project Orion", type="project"),
        predicate="budget",
        object=FactObject(value=650, raw_value="650 lakh", unit="INR"),
        qualifiers=FactQualifiers(reporting_period="2023"),
    )
    f2 = f1.model_copy(update={"fact_id": "F2", "object": FactObject(value=700, raw_value="700 lakh", unit="INR"), "qualifiers": FactQualifiers(reporting_period="2024")})

    conf = ConflictComparator.compare_facts(f1, f2)
    assert conf is not None
    assert conf.classification == ConflictClassification.TEMPORAL_DIFFERENCE


def test_fact_005_conflict_scope_difference():
    """FACT-005: Geographic divergence classifies as SCOPE_DIFFERENCE."""
    f1 = FactItem(
        fact_id="F1",
        subject=EntityRef(entity_id="E1", name="Transit", type="transit"),
        predicate="ridership",
        object=FactObject(value=10000, raw_value="10,000", data_type="quantity"),
        qualifiers=FactQualifiers(geographic_scope="North"),
    )
    f2 = f1.model_copy(update={"fact_id": "F2", "object": FactObject(value=15000, raw_value="15,000", data_type="quantity"), "qualifiers": FactQualifiers(geographic_scope="South")})

    conf = ConflictComparator.compare_facts(f1, f2)
    assert conf is not None
    assert conf.classification == ConflictClassification.SCOPE_DIFFERENCE


def test_fact_006_conflict_unit_difference():
    """FACT-006: Incompatible currencies classify as UNIT_DIFFERENCE."""
    f1 = FactItem(
        fact_id="F1",
        subject=EntityRef(entity_id="E1", name="Project", type="project"),
        predicate="cost",
        object=FactObject(value=500, raw_value="500 USD", unit="USD"),
    )
    f2 = f1.model_copy(update={"fact_id": "F2", "object": FactObject(value=500, raw_value="500 EUR", unit="EUR")})

    conf = ConflictComparator.compare_facts(f1, f2)
    assert conf is not None
    assert conf.classification == ConflictClassification.UNIT_DIFFERENCE


def test_fact_007_conflict_direct_contradiction():
    """FACT-007: Incompatible reported values in same scope/period classify as DIRECT_CONFLICT."""
    f1 = FactItem(
        fact_id="F1",
        subject=EntityRef(entity_id="E1", name="Project Orion", type="project"),
        predicate="budget",
        object=FactObject(value=650, raw_value="650 lakh", unit="INR"),
        qualifiers=FactQualifiers(reporting_period="2024", geographic_scope="Central"),
    )
    f2 = f1.model_copy(update={"fact_id": "F2", "object": FactObject(value=900, raw_value="900 lakh", unit="INR")})

    conf = ConflictComparator.compare_facts(f1, f2)
    assert conf is not None
    assert conf.classification == ConflictClassification.DIRECT_CONFLICT
    assert conf.resolution_status == "UNRESOLVED"


def test_fact_008_schema_conformance(fact_schema, conflict_schema):
    """FACT-008: Verify fact and conflict models match JSON Draft-07 schemas."""
    text = "Global Infrastructure Bank reported revenue was $450 million in FY2024."
    facts = FactExtractor.extract_from_passage("DOC-001", text, page_number=1)
    for f in facts:
        jsonschema.validate(f.model_dump(), fact_schema)

    conf = ConflictComparator.compare_facts(facts[0], facts[0])
    assert conf is not None
    jsonschema.validate(conf.model_dump(), conflict_schema)
