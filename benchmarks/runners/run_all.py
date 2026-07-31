"""Run every metric on the golden set + AEGIS pipeline + vanilla control."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.golden.schema import QARecord
from benchmarks.metrics import (
    citation_precision,
    deepeval_runner,
    engine_contributions,
    hallucination,
    latency,
    ragas_runner,
    retrieval_recall,
    token_reduction,
)
from benchmarks.pipelines.aegis_native import AegisPipeline
from benchmarks.pipelines.baseline_vanilla_rag import VanillaRagPipeline
from benchmarks.pipelines.stub_llm import StubLLM

logger = logging.getLogger("benchmarks.run_all")


def load_golden(path: Path) -> list[QARecord]:
    out: list[QARecord] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                d["gold_citations"] = [tuple(c) for c in d.get("gold_citations", [])]
                out.append(QARecord(**d))
    return out


async def main_async(args: argparse.Namespace) -> int:
    records = load_golden(args.questions)
    llm = StubLLM()

    # Run AEGIS
    aegis_rows: list[dict] = []
    t_total = time.perf_counter()
    async with AegisPipeline(llm=llm) as aegis:
        for r in records:
            run = await aegis.run(r.question)
            aegis_rows.append({
                "qid": r.qid,
                "question": r.question,
                "answer": run.answer,
                "citations": run.citations,
                "retrieved_unit_ids": run.retrieved_unit_ids,
                "raw_tokens": run.raw_tokens,
                "aegis_tokens": run.aegis_tokens,
                "timings_ms": run.timings_ms,
                "counters": {},
                "evidence_texts": [],
            })

    # Run vanilla
    vanilla_rows: list[dict] = []
    async with VanillaRagPipeline(llm=llm) as vanilla:
        for r in records:
            run = await vanilla.run(r.question)
            vanilla_rows.append({
                "qid": r.qid,
                "question": r.question,
                "answer": run.answer,
                "citations": run.citations,
                "retrieved_unit_ids": run.retrieved_unit_ids,
                "raw_tokens": run.raw_tokens,
                "aegis_tokens": run.aegis_tokens,
                "timings_ms": run.timings_ms,
                "counters": {},
            })

    out: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_questions": len(records),
        "aegis": {},
        "vanilla": {},
    }

    out["aegis"]["retrieval"] = retrieval_recall.evaluate(
        gold_unit_ids=[r.gold_unit_ids for r in records],
        retrieved_unit_ids=[row["retrieved_unit_ids"] for row in aegis_rows],
    )
    out["vanilla"]["retrieval"] = retrieval_recall.evaluate(
        gold_unit_ids=[r.gold_unit_ids for r in records],
        retrieved_unit_ids=[row["retrieved_unit_ids"] for row in vanilla_rows],
    )

    out["aegis"]["citations"] = citation_precision.evaluate(
        gold_citations=[r.gold_citations for r in records],
        predicted_citations=[row["citations"] for row in aegis_rows],
    )
    out["vanilla"]["citations"] = citation_precision.evaluate(
        gold_citations=[r.gold_citations for r in records],
        predicted_citations=[row["citations"] for row in vanilla_rows],
    )

    aegis_pairs = [(row["raw_tokens"], row["aegis_tokens"]) for row in aegis_rows]
    out["aegis"]["tokens"] = token_reduction.summarize(aegis_pairs)
    vanilla_pairs = [(row["raw_tokens"], row["aegis_tokens"]) for row in vanilla_rows]
    out["vanilla"]["tokens"] = token_reduction.summarize(vanilla_pairs)

    out["aegis"]["ragas"] = await ragas_runner.evaluate(
        questions=[r.question for r in records],
        answers=[row["answer"] for row in aegis_rows],
        contexts=[[] for _ in records],
        ground_truths=[r.expected_answer for r in records],
    )
    out["vanilla"]["ragas"] = await ragas_runner.evaluate(
        questions=[r.question for r in records],
        answers=[row["answer"] for row in vanilla_rows],
        contexts=[[] for _ in records],
        ground_truths=[r.expected_answer for r in records],
    )

    out["aegis"]["deepeval"] = await deepeval_runner.evaluate(
        questions=[r.question for r in records],
        answers=[row["answer"] for row in aegis_rows],
        ground_truths=[r.expected_answer for r in records],
    )
    out["vanilla"]["deepeval"] = await deepeval_runner.evaluate(
        questions=[r.question for r in records],
        answers=[row["answer"] for row in vanilla_rows],
        ground_truths=[r.expected_answer for r in records],
    )

    out["aegis"]["hallucination"] = hallucination.evaluate(
        answers=[row["answer"] for row in aegis_rows],
        retrieved_evidence=[row["evidence_texts"] for row in aegis_rows],
    )

    aegis_per_q = [
        row["timings_ms"].get("retrieval_ms", 0) + row["timings_ms"].get("generation_ms", 0)
        for row in aegis_rows
    ]
    out["aegis"]["latency"] = latency.evaluate(aegis_per_q).__dict__
    vanilla_per_q = [row["timings_ms"].get("retrieval_ms", 0) for row in vanilla_rows]
    out["vanilla"]["latency"] = latency.evaluate(vanilla_per_q).__dict__

    out["aegis"]["engines"] = engine_contributions.evaluate([
        {"counters": row["counters"], "timings_ms": row["timings_ms"]} for row in aegis_rows
    ])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    from benchmarks.runners.publish_report import render
    md = render(out)
    md_path = Path("benchmarks/docs/Benchmarks.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", required=True, type=Path)
    ap.add_argument("--out",       required=True, type=Path)
    ap.add_argument("--corpus",    type=Path, default=None)
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
