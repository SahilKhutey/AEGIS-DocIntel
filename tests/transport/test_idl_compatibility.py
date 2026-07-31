"""Round-trip protobuf messages to confirm the contract is well-formed."""

from __future__ import annotations

import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
if root not in sys.path:
    sys.path.insert(0, root)
sdk_proto = str(Path(__file__).resolve().parents[2] / "sdks" / "python" / "src")
if sdk_proto not in sys.path:
    sys.path.insert(0, sdk_proto)

from amdi_sdk.proto import amdi_pb2


def test_job_round_trip() -> None:
    job = amdi_pb2.Job(
        job_id="j-1", document_id="d-1",
        state=amdi_pb2.JOB_STATE_RUNNING,
        submitted_at=1.0, started_at=2.0,
        progress_pct=42.0, progress_message="ok",
    )
    blob = job.SerializeToString()
    job2 = amdi_pb2.Job()
    job2.ParseFromString(blob)
    assert job2 == job


def test_evidence_round_trip_with_citations() -> None:
    ev = amdi_pb2.Evidence(
        evidence_id="e-1", text="the cat sat on the mat",
        score_fused=0.9, score_dense=0.88,
        citations=[amdi_pb2.Citation(
            document_id="d-1", page=3,
            bbox=amdi_pb2.BBox(x=0.1, y=0.2, w=0.8, h=0.05),
        )],
    )
    ev2 = amdi_pb2.Evidence()
    ev2.ParseFromString(ev.SerializeToString())
    assert ev2.text == ev.text
    assert ev2.citations[0].page == 3
