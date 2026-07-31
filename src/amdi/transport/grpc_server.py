"""gRPC server, generated stubs, and the FastAPI-bridge interop point."""

from __future__ import annotations

import logging
from concurrent import futures
from typing import Any

import grpc

from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger
from amdi.jobs.progress import ProgressBus
from amdi.transport.grpc_interceptors import (
    AuthServerInterceptor,
    LoggingServerInterceptor,
    MetricsServerInterceptor,
)
from amdi.transport.proto_stub_loader import amdi_pb2, amdi_pb2_grpc

logger = logging.getLogger("amdi.transport.server")

# Per-call authenticated principal attached by AuthServerInterceptor.
_AUTH_CTX: dict[int, dict[str, Any]] = {}


def _set_auth(context, claims: dict[str, Any]) -> None:
    _AUTH_CTX[id(context)] = claims


def _get_auth(context) -> dict[str, Any] | None:
    return _AUTH_CTX.get(id(context))


class DocumentIntelligenceServicer(amdi_pb2_grpc.DocumentIntelligenceServicer):
    """Server-side implementation of every RPC in proto/amdi.proto."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._ledger = make_ledger()
        self._bus = ProgressBus()

    def Health(self, request, context):  # noqa: N802
        from amdi.version import __version__
        return amdi_pb2.HealthResponse(
            serving_state=amdi_pb2.HealthResponse.SERVING,
            version=__version__,
            queue_ready=True,
            ledger_ready=True,
        )

    def Upload(self, request_iterator, context):  # noqa: N802
        first = next(request_iterator)
        meta = first.metadata
        buf = bytearray()
        if first.chunk:
            buf.extend(first.chunk)
        for msg in request_iterator:
            buf.extend(msg.chunk)

        import asyncio
        from amdi.jobs.schemas import JobEnvelope, JobState
        env = JobEnvelope(
            state=JobState.PENDING,
            metadata={"filename": meta.filename, "mime": meta.mime_type, "bytes": len(buf)},
            user_id=meta.user_id or None,
        )
        asyncio.run(self._ledger.put(env))
        return amdi_pb2.UploadResponse(job=self._to_pb_job(env))

    def GetJob(self, request, context):  # noqa: N802
        import asyncio
        env = asyncio.run(self._ledger.get(request.job_id))
        if env is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "job not found")
        return self._to_pb_job(env)

    def CancelJob(self, request, context):  # noqa: N802
        import asyncio
        import time
        env = asyncio.run(self._ledger.update(
            request.job_id, state="cancelled", finished_at=time.time(),
        ))
        return self._to_pb_job(env)

    def ListJobs(self, request, context):  # noqa: N802
        import json
        from pathlib import Path
        from amdi.jobs.schemas import JobEnvelope

        jobs = []
        root = Path(self._settings.storage_root) / "jobs"
        if root.exists():
            for p in root.glob("*.json"):
                data = json.loads(p.read_text(encoding="utf-8"))
                env = JobEnvelope(**data)
                if request.state_filter and env.state.value != request.state_filter:
                    continue
                jobs.append(self._to_pb_job(env))
                if len(jobs) >= (request.limit or 50):
                    break

        return amdi_pb2.ListJobsResponse(jobs=jobs)

    def StreamJobEvents(self, request, context):  # noqa: N802
        import asyncio
        import json
        from pathlib import Path

        path = Path(self._settings.storage_root) / "jobs" / f"{request.job_id}.events.ndjson"
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    d = json.loads(line)
                    yield amdi_pb2.JobEvent(
                        job_id=d["job_id"], ts=d["ts"], kind=d["kind"],
                        pct=float(d.get("pct") or 0.0),
                        message=d.get("message", ""),
                    )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async def _listen():
                events = []
                async with self._bus.subscribe(request.job_id) as q:
                    ev = await q.get()
                    events.append(ev)
                return events

            evs = loop.run_until_complete(_listen())
            for ev in evs:
                yield amdi_pb2.JobEvent(
                    job_id=ev.job_id, ts=ev.ts, kind=ev.kind,
                    pct=float(ev.pct or 0.0), message=ev.message,
                )
        finally:
            loop.close()


    def Query(self, request, context):  # noqa: N802
        import asyncio
        from amdi.retrieval.backends.inmemory import InMemoryIndexStore
        from amdi.retrieval.hybrid import HybridRetriever
        from amdi.retrieval.schemas import (
            Query as QMsg,
            QueryExpansion as QEM,
            RetrievalConfig,
        )

        store = InMemoryIndexStore()
        cfg = RetrievalConfig(
            enable_reranker=request.enable_reranker,
            fusion=request.fusion or "rrf",
        )
        retriever = HybridRetriever(store, config=cfg)
        q = QMsg(
            raw=request.query.raw,
            expanded=QEM(original=request.query.raw),
            top_k=request.query.top_k or 10,
        )
        result = asyncio.run(retriever.search(q))
        return self._to_pb_result(result)

    def ExportTokenOptimized(self, request, context):  # noqa: N802
        from amdi.export.llm_optimized import LLMTokenOptimizedExporter
        from amdi.retrieval.schemas import Evidence
        evs = [
            Evidence(text=e.text, score_fused=e.score_fused)
            for e in request.result.evidence
        ]
        body = LLMTokenOptimizedExporter().render(
            evs, format=request.format or "markdown",
            budget=request.token_budget or 4000,
        )
        return amdi_pb2.TokenOptimizedExport(
            format=request.format or "markdown",
            body=body,
            token_count=len(body.split()),
        )

    def PiiScan(self, request, context):  # noqa: N802
        from amdi.compliance.pii import PiiEngine
        engine = PiiEngine(request.policy)
        findings = engine.scan([d.text if hasattr(d, "text") else "" for d in request.documents])
        return amdi_pb2.PiiScanResponse(
            redacted=request.documents,
            findings=[
                amdi_pb2.PiiFinding(
                    document_id=f.document_id, category=f.category,
                    original=f.original, replacement=f.replacement,
                )
                for f in findings
            ],
        )

    @staticmethod
    def _to_pb_job(env) -> amdi_pb2.Job:
        state_map = {
            "pending":   amdi_pb2.JOB_STATE_PENDING,
            "running":   amdi_pb2.JOB_STATE_RUNNING,
            "succeeded": amdi_pb2.JOB_STATE_SUCCEEDED,
            "failed":    amdi_pb2.JOB_STATE_FAILED,
            "cancelled": amdi_pb2.JOB_STATE_CANCELLED,
            "retrying":  amdi_pb2.JOB_STATE_RETRYING,
        }
        return amdi_pb2.Job(
            job_id=env.job_id, document_id=env.document_id or "",
            state=state_map.get(env.state.value, amdi_pb2.JOB_STATE_UNSPECIFIED),
            submitted_at=env.submitted_at,
            started_at=env.started_at or 0.0,
            finished_at=env.finished_at or 0.0,
            attempts=env.attempts,
            progress_pct=env.progress_pct,
            progress_message=env.progress_message,
            error_code=env.error_code or "",
            error_detail=env.error_detail or "",
        )

    @staticmethod
    def _to_pb_result(result) -> amdi_pb2.RetrievalResult:
        ev_pb = []
        for ev in result.evidence:
            citations = []
            for c in ev.citations:
                citations.append(amdi_pb2.Citation(
                    document_id=c.document_id,
                    page=c.page or 0,
                    bbox=amdi_pb2.BBox(
                        x=(c.bbox[0] if c.bbox else 0.0),
                        y=(c.bbox[1] if c.bbox else 0.0),
                        w=(c.bbox[2] if c.bbox else 0.0),
                        h=(c.bbox[3] if c.bbox else 0.0),
                    ),
                ))
            ev_pb.append(amdi_pb2.Evidence(
                evidence_id=ev.evidence_id, text=ev.text,
                score_fused=ev.score_fused,
                score_dense=ev.score_dense,
                score_bm25=ev.score_bm25,
                citations=citations,
            ))
        return amdi_pb2.RetrievalResult(
            query=amdi_pb2.Query(raw=result.query.raw),
            evidence=ev_pb,
            timings_ms=result.timings_ms,
            counters=result.counters,
            generated_at=result.generated_at,
        )


def make_server(*,
                max_workers: int | None = None,
                interceptors: list[grpc.ServerInterceptor] | None = None,
                port: int | None = None) -> grpc.Server:
    settings = get_settings()
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers or settings.api_workers),
        interceptors=interceptors if interceptors is not None else [
            AuthServerInterceptor(),
            LoggingServerInterceptor(),
            MetricsServerInterceptor(),
        ],
        options=[
            ("grpc.max_receive_message_length", 256 * 1024 * 1024),
            ("grpc.max_send_message_length",    256 * 1024 * 1024),
        ],
    )
    amdi_pb2_grpc.add_DocumentIntelligenceServicer_to_server(
        DocumentIntelligenceServicer(), server
    )
    server.add_insecure_port(f"[::]:{port or 50051}")
    return server


def serve_forever() -> None:
    server = make_server()
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve_forever()
