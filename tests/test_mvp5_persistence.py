"""
tests/test_mvp5_persistence.py
==============================
Unit tests for FactStore persistence, atomic replacement, and tenant isolation.
"""

from src.engines.intelligence.contracts import EvidenceSpan, ExtractedFact
from src.engines.intelligence.fact_store import FactStore


def test_fact_store_atomic_replacement_and_queries(tmp_path):
    db_file = str(tmp_path / "test_facts.db")
    store = FactStore(db_path=db_file)

    span = EvidenceSpan(
        document_id="doc-1",
        tenant_id="tenant-1",
        chunk_id="c1",
        quoted_text="liability $1M",
    )
    fact1 = ExtractedFact(
        fact_id="f1",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="liability_cap",
        value=1000000.0,
        raw_value="$1,000,000",
        value_type="decimal",
        unit="USD",
        evidence=(span,),
    )

    # 1. Store run 1
    run_id_1 = store.store_extraction_run(
        tenant_id="tenant-1",
        document_id="doc-1",
        schema_name="contract_terms",
        facts=[fact1],
        document_version=1,
    )
    assert run_id_1.startswith("run-")

    facts = store.get_facts_by_document("tenant-1", "doc-1")
    assert len(facts) == 1
    assert facts[0].fact_id == "f1"
    assert facts[0].value == 1000000.0
    assert len(facts[0].evidence) == 1
    assert facts[0].evidence[0].quoted_text == "liability $1M"

    # 2. Atomic replacement: store run 2 for same document and schema
    fact2 = ExtractedFact(
        fact_id="f2",
        tenant_id="tenant-1",
        document_id="doc-1",
        subject="contract",
        attribute="liability_cap",
        value=2000000.0,
        raw_value="$2,000,000",
        value_type="decimal",
        unit="USD",
        evidence=(span,),
    )
    store.store_extraction_run(
        tenant_id="tenant-1",
        document_id="doc-1",
        schema_name="contract_terms",
        facts=[fact2],
        document_version=2,
    )

    # Old fact f1 replaced by f2
    updated_facts = store.get_facts_by_document("tenant-1", "doc-1")
    assert len(updated_facts) == 1
    assert updated_facts[0].fact_id == "f2"
    assert updated_facts[0].value == 2000000.0


def test_fact_store_strict_tenant_isolation(tmp_path):
    db_file = str(tmp_path / "tenant_iso.db")
    store = FactStore(db_path=db_file)

    fact_a = ExtractedFact(
        fact_id="fa",
        tenant_id="tenant-A",
        document_id="doc-shared-id",
        subject="contract",
        attribute="secret_rate",
        value=500.0,
        raw_value="500",
        value_type="decimal",
    )
    fact_b = ExtractedFact(
        fact_id="fb",
        tenant_id="tenant-B",
        document_id="doc-shared-id",
        subject="contract",
        attribute="secret_rate",
        value=900.0,
        raw_value="900",
        value_type="decimal",
    )

    store.store_extraction_run("tenant-A", "doc-shared-id", "rate_schema", [fact_a])
    store.store_extraction_run("tenant-B", "doc-shared-id", "rate_schema", [fact_b])

    # Tenant-A sees only fact_a
    facts_a = store.get_facts_by_document("tenant-A", "doc-shared-id")
    assert len(facts_a) == 1
    assert facts_a[0].value == 500.0

    # Tenant-B sees only fact_b
    facts_b = store.get_facts_by_document("tenant-B", "doc-shared-id")
    assert len(facts_b) == 1
    assert facts_b[0].value == 900.0

    # Deleting in Tenant-A does not delete Tenant-B
    store.delete_document_facts("tenant-A", "doc-shared-id")
    assert store.get_facts_by_document("tenant-A", "doc-shared-id") == []
    assert len(store.get_facts_by_document("tenant-B", "doc-shared-id")) == 1
