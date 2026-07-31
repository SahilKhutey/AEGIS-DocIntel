"""pytest fixtures shared by all benchmark tests."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

root = str(Path(__file__).parents[1])
if root not in sys.path:
    sys.path.insert(0, root)

import pytest


from benchmarks.golden.schema import QARecord
from benchmarks.pipelines.aegis_native import AegisPipeline
from benchmarks.pipelines.baseline_vanilla_rag import VanillaRagPipeline
from benchmarks.pipelines.stub_llm import StubLLM


GOLDEN_DEFAULT = Path(__file__).parent / "golden" / "questions.jsonl"


@pytest.fixture(scope="session")
def golden_records() -> list[QARecord]:
    if not GOLDEN_DEFAULT.exists():
        from benchmarks.golden.build_golden import main as build
        build()
    out: list[QARecord] = []
    with GOLDEN_DEFAULT.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                d["gold_citations"] = [tuple(c) for c in d.get("gold_citations", [])]
                out.append(QARecord(**d))
    return out


@pytest.fixture
def stub_llm() -> StubLLM:
    return StubLLM(answers={
        "Einstein": "Albert Einstein proposed general relativity in 1915.",
        "general relativity": "Albert Einstein proposed general relativity in 1915.",
        "Milan": "Milan is the financial capital of Italy.",
        "ACID": "Atomicity, Consistency, Isolation, Durability.",
        "BASE": "Basically Available, Soft state, Eventual consistency.",
        "sharding": "Splitting data across many commodity nodes.",
        "vertical": "Single-machine scaling; hits a ceiling and is expensive.",
        "PageRank": "Query-independent, random-surfer model, single global score.",
        "HITS": "Query-dependent hub/authority scores.",
        "persistent homology": "Tracks topological features across scales.",
        "Betti numbers": "Count connected components, loops, voids.",
        "Tarawa": "Tarawa is the capital of Kiribati.",
        "cable": "The first transatlantic telegraph cable was completed in 1858.",
    })


@pytest.fixture
def aegis_pipeline(stub_llm) -> AegisPipeline:
    return AegisPipeline(llm=stub_llm)


@pytest.fixture
def vanilla_pipeline(stub_llm) -> VanillaRagPipeline:
    return VanillaRagPipeline(llm=stub_llm)


@pytest.fixture
def tmp_results_dir(tmp_path: Path) -> Iterator[Path]:
    d = tmp_path / "results"
    d.mkdir(parents=True, exist_ok=True)
    yield d
