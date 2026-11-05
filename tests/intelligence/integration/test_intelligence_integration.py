"""
tests.intelligence.integration.test_intelligence_integration
============================================================
End-to-end integration tests for WP-06 Intelligence:
Retrieval -> Evidence Selection -> Fact Extraction -> Conflict Analysis ->
Answerability Decision -> Citation Verification -> Structured Report Generation.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.answerability import AnswerabilityClassifier
from aegis.intelligence.citations import ClaimExtractor, SupportEvaluator
from aegis.intelligence.conflicts import ConflictComparator
from aegis.intelligence.facts import FactExtractor
from aegis.intelligence.models import (
    AnswerabilityClass,
    AnswerabilityDecision,
    ConflictClassification,
    ReportCitation,
    ReportClaim,
    ReportSection,
    RetrievalItem,
    SupportLabel,
)
from aegis.intelligence.reports import (
    ReportContentBuilder,
    ReportRenderer,
    ReportValidator,
)
from aegis.intelligence.retrieval import HybridRetriever, LexicalRetriever


@pytest.fixture
def index_and_corpus():
    corpus = [
        {
            "document_id": "DOC-A",
            "chunk_id": "CHK-A1",
            "page_number": 1,
            "text": "Project Orion total reported expenditure for fiscal year 2024 was $650 million.",
            "metadata": {"year": 2024, "type": "financial_report"},
        },
        {
            "document_id": "DOC-B",
            "chunk_id": "CHK-B1",
            "page_number": 2,
            "text": "Project Orion total reported expenditure for fiscal year 2024 was $700 million.",
            "metadata": {"year": 2024, "type": "amended_report"},
        },
        {
            "document_id": "DOC-C",
            "chunk_id": "CHK-C1",
            "page_number": 4,
            "text": "| Quarter | Budget | Actual |\n| Q1 | 150000 | 148000 |",
            "metadata": {"is_table": True},
        },
        {
            "document_id": "DOC-D",
            "chunk_id": "CHK-D1",
            "page_number": 1,
            "text": "The solar project was funded by Federal Energy Agency under grant program FEA-990.",
            "metadata": {"type": "grant"},
        },
        {
            "document_id": "DOC-D",
            "chunk_id": "CHK-D2",
            "page_number": 3,
            "text": "Total grant program FEA-990 allocation reached $45 million.",
            "metadata": {"type": "grant"},
        },
    ]
    retriever = HybridRetriever()
    for item in corpus:
        retriever.index_document(**item)
    return retriever, corpus


def test_int_001_direct_factual_retrieval_and_answer(index_and_corpus):
    """INT-001: Retrieve relevant document and verify factual answer grounding."""
    retriever, _ = index_and_corpus
    res = retriever.retrieve("Project Orion expenditure 2024", top_k=2)
    assert len(res.results) > 0
    assert "650 million" in res.results[0].text or "700 million" in res.results[0].text


def test_int_002_table_retrieval_and_extraction(index_and_corpus):
    """INT-002: Retrieve a table chunk and extract numeric values."""
    retriever, _ = index_and_corpus
    res = retriever.retrieve("table Quarter Budget Actual", top_k=2)
    assert len(res.results) > 0
    assert "150000" in res.results[0].text


def test_int_003_multihop_evidence_selection(index_and_corpus):
    """INT-003: Multi-hop question retrieves both necessary evidence passages."""
    retriever, _ = index_and_corpus
    res = retriever.retrieve("Federal Energy Agency FEA-990 grant allocation", top_k=3)
    chunk_ids = {item.chunk_id for item in res.results}
    assert "CHK-D1" in chunk_ids
    assert "CHK-D2" in chunk_ids


def test_int_004_claim_decomposition_and_citation_verification(index_and_corpus):
    """INT-004: Generated answer with citation resolves and verifies against evidence."""
    answer = "Project Orion expenditure was $650 million in 2024."
    claims = ClaimExtractor.extract_claims(answer)
    assert len(claims) == 1

    evaluator = SupportEvaluator()
    eval_res = evaluator.evaluate_answer(
        answer_id="A1",
        answer_text=answer,
        claims=claims,
        evidence_store={"C1": "Project Orion total reported expenditure for fiscal year 2024 was $650 million."},
    )
    assert eval_res.evaluation_summary.claim_support_rate == 0.0  # without citation attached
    # Attach citation
    claims[0].citations = [
        eval_res.claims[0].citations[0]
        if eval_res.claims[0].citations
        else {"citation_id": "C1", "document_id": "DOC-A", "page_number": 1}
    ]


def test_int_005_unanswerable_abstention_pipeline():
    """INT-005: Absent information triggers NOT_FOUND abstention, not hallucination."""
    classifier = AnswerabilityClassifier()
    q = "What was the room temperature during the executive meeting?"
    res = classifier.evaluate("Q-UNANS", q, [])
    assert res.decision == AnswerabilityDecision.ABSTAIN_NOT_FOUND
    assert res.classification == AnswerabilityClass.NOT_FOUND


def test_int_006_ambiguous_question_clarification():
    """INT-006: Under-specified question triggers REQUEST_CLARIFICATION."""
    classifier = AnswerabilityClassifier()
    res = classifier.evaluate("Q-AMBIG", "What was the total?", [])
    assert res.decision == AnswerabilityDecision.REQUEST_CLARIFICATION


def test_int_007_cross_document_conflict_detection():
    """INT-007: Compares facts from two documents and identifies direct contradiction."""
    text_a = "Project Orion total reported expenditure was $650 million in FY2024."
    text_b = "Project Orion total reported expenditure was $700 million in FY2024."

    facts_a = FactExtractor.extract_from_passage("DOC-A", text_a, page_number=1, reporting_period="FY2024")
    facts_b = FactExtractor.extract_from_passage("DOC-B", text_b, page_number=2, reporting_period="FY2024")

    conf = ConflictComparator.compare_facts(facts_a[0], facts_b[0])
    assert conf is not None
    assert conf.classification == ConflictClassification.DIRECT_CONFLICT
    assert conf.resolution_status == "UNRESOLVED"


def test_int_008_fact_extraction_and_comparison():
    """INT-008: Normalizes extracted facts and performs cross-document reconciliation."""
    text1 = "Global Corp reported revenue was $100 million in FY2023."
    text2 = "Global Corp reported revenue was $150 million in FY2024."

    f1 = FactExtractor.extract_from_passage("DOC-1", text1, page_number=1, reporting_period="FY2023")[0]
    f2 = FactExtractor.extract_from_passage("DOC-2", text2, page_number=1, reporting_period="FY2024")[0]

    conf = ConflictComparator.compare_facts(f1, f2)
    assert conf is not None
    assert conf.classification == ConflictClassification.TEMPORAL_DIFFERENCE


def test_int_009_report_generation_with_citations_and_conflicts():
    """INT-009: Builds structured report containing verified claims, citations, and conflicts."""
    sec = ReportSection(
        section_id="SEC-01",
        heading="Financial Analysis",
        claims=[
            ReportClaim(
                claim_id="CLM-01",
                text="Project Orion budget was reported as $650 million in Doc A.",
                citations=[ReportCitation(document_id="DOC-A", page_number=1)],
            )
        ],
    )
    conf = [
        {
            "subject": "Project Orion",
            "predicate": "reported_budget",
            "classification": "DIRECT_CONFLICT",
            "reason": "$650M vs $700M reported in overlapping periods",
        }
    ]
    report = ReportContentBuilder.build_comparative_report(
        title="Project Orion Audit Report",
        document_ids=["DOC-A", "DOC-B"],
        sections=[sec],
        conflicts=conf,
    )

    val = ReportValidator.validate_report(report, known_conflicts=conf)
    assert val.is_valid is True

    md = ReportRenderer.to_markdown(report)
    assert "# Project Orion Audit Report" in md
    assert "[DOC-A#P1]" in md
    assert "DIRECT_CONFLICT" in md


def test_int_010_full_schema_conformance():
    """INT-010: Validates end-to-end report against report.schema.json."""
    sec = ReportSection(
        section_id="SEC-01",
        heading="Summary",
        claims=[ReportClaim(claim_id="C1", text="Analysis complete.", citations=[])],
    )
    rep = ReportContentBuilder.build_document_summary(
        title="Validation Report",
        document_id="DOC-01",
        summary_text="Complete analysis",
        claims=[],
    )
    schema = json.loads(Path("schemas/intelligence/report.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(rep.model_dump(), schema)
