# v0.3.0 Launch — 15-minute demo script

> Use this when recording a screencast, running a webinar, or doing a
> booth demo at a conference. Each numbered step is 30–60 s.

## 0 — Setup (30 s)

> Terminal open, backend running, browser open to localhost:8000/docs.

```bash
cd AEGIS-DocIntel
python -m amdi serve &
sleep 2
curl http://localhost:8000/healthz
```

## 1 — Show the API (60 s)

Open browser -> `http://localhost:8000/docs`.
Show the 14 endpoints listed in `README.md`. Close with:

> *"That's the public surface. Everything else is internal."*

## 2 — Hybrid retrieval (90 s)

```bash
python scripts/demo_reel.py --show | head -100
```

Point at the manifest output:

> *"Single command... ingest through OCR... retrieval that fuses BM25, dense,
> frequency, geometry, graph, matrix, and template methods... capped to the
> model budget... exported in three formats... sent to every connector with
> one call."*

## 3 — Hard budget guarantee (45 s)

```bash
pytest tests/export/test_budget_hard_cap.py -v
```

Show the property test running across random inputs.

> *"This test proves the budget is never exceeded — by construction, not
> by hope."*

## 4 — Drift sweep (60 s)

```bash
python tools/sweep_drift.py --strict --json | python -m json.tool
```

> *"Every night, this bot inventories drift. If anyone imports a legacy
> name, it opens a PR. Try adding one and watch it fail."*

## 5 — Operate it (60 s)

Open Grafana -> AEGIS-DocIntel dashboard. Click:
* p95 latency by route (proves we hit SLA targets)
* in-flight jobs (the green/red gauge)
* rate-limit denials

> *"This is what your on-call sees at 3 AM."*

## 6 — Roadmap in 60 s (60 s)

Show `docs/ROADMAP.md`. End with:

> *"0.4.0 removes the legacy bridge; 1.0.0 freezes the API. Three more
> minors and we're at semantic stability."*

## 7 — Closing (30 s)

> *"Open source, MIT-style permissive license for evaluation, proprietary
> commercial license for use. The repo link is in the notes; the demo
> script is in the README. Thanks."*

## Common Q&A

| Q | A |
| - | - |
| "Why not just use LangChain?" | We *complement* LangChain; the LLMTokenOptimizedExporter is what you feed your chain |
| "Where's the benchmark?" | `docs/Benchmarks.md` — measured, not projected |
| "Do you support multi-tenancy?" | Roadmap item for v0.5.0 (research) |
| "Is there a managed cloud version?" | Roadmap item for v1.x |
| "Why are there 16 mathematical domains?" | See `docs/Mathematics.md` — each one improves a different failure mode |
