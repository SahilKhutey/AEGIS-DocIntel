"""Citation metrics: precision, recall, nDCG."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.metrics.citation_precision import evaluate




def test_perfect_overlap() -> None:
    out = evaluate(
        gold_citations=[[("d1.pdf", 2), ("d2.pdf", 4)]],
        predicted_citations=[[{"document_id": "d1.pdf", "page": 2},
                              {"document_id": "d2.pdf", "page": 4}]],
    )
    assert out["citation_precision"] == 1.0
    assert out["citation_recall"] == 1.0
    assert out["citation_ndcg"] == 1.0


def test_partial_overlap() -> None:
    out = evaluate(
        gold_citations=[[("d1.pdf", 2), ("d2.pdf", 4)]],
        predicted_citations=[[{"document_id": "d1.pdf", "page": 2}]],
    )
    assert out["citation_precision"] == 1.0
    assert out["citation_recall"] == 0.5


def test_no_overlap() -> None:
    out = evaluate(
        gold_citations=[[("d1.pdf", 2)]],
        predicted_citations=[[{"document_id": "dX.pdf", "page": 9}]],
    )
    assert out["citation_precision"] == 0.0
    assert out["citation_recall"] == 0.0
