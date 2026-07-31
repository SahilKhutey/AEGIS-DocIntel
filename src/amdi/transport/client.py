"""Sync + async gRPC clients (for SDKs that prefer to speak proto directly)."""

from __future__ import annotations

import os
from typing import AsyncIterator, Iterable

import grpc

from amdi.transport.proto_stub_loader import amdi_pb2, amdi_pb2_grpc

DEFAULT_TARGET = os.environ.get("AMDI_GRPC_TARGET", "localhost:50051")


class AmdiClient:
    """Synchronous client. Construct one per thread; reuse it."""

    def __init__(self, target: str = DEFAULT_TARGET,
                 *, api_key: str | None = None) -> None:
        self._channel = grpc.insecure_channel(target)
        self._stub = amdi_pb2_grpc.DocumentIntelligenceStub(self._channel)
        self._meta = (("authorization", f"Bearer {api_key}"),) if api_key else ()

    def health(self) -> amdi_pb2.HealthResponse:
        return self._stub.Health(amdi_pb2.HealthRequest(), metadata=self._meta)

    def upload(self, *, filename: str, mime_type: str,
               data: bytes, user_id: str | None = None) -> amdi_pb2.UploadResponse:
        def _gen() -> Iterable[amdi_pb2.UploadRequest]:
            yield amdi_pb2.UploadRequest(metadata=amdi_pb2.UploadMetadata(
                filename=filename, mime_type=mime_type,
                user_id=user_id or "",
                expected_size_bytes=len(data),
            ))
            chunk_size = 1024 * 1024
            for i in range(0, len(data), chunk_size):
                yield amdi_pb2.UploadRequest(chunk=data[i:i + chunk_size])
        return self._stub.Upload(_gen(), metadata=self._meta)

    def get_job(self, job_id: str) -> amdi_pb2.Job:
        return self._stub.GetJob(
            amdi_pb2.GetJobRequest(job_id=job_id), metadata=self._meta,
        )

    def cancel_job(self, job_id: str) -> amdi_pb2.Job:
        return self._stub.CancelJob(
            amdi_pb2.CancelJobRequest(job_id=job_id), metadata=self._meta,
        )

    def query(self, raw: str, *, top_k: int = 10) -> amdi_pb2.RetrievalResult:
        return self._stub.Query(
            amdi_pb2.QueryRequest(
                query=amdi_pb2.Query(raw=raw, top_k=top_k),
            ),
            metadata=self._meta,
        )

    def stream_events(self, job_id: str) -> Iterable[amdi_pb2.JobEvent]:
        return self._stub.StreamJobEvents(
            amdi_pb2.GetJobRequest(job_id=job_id), metadata=self._meta,
        )

    def close(self) -> None:
        self._channel.close()


class AsyncAmdiClient:
    def __init__(self, target: str = DEFAULT_TARGET,
                 *, api_key: str | None = None) -> None:
        self._channel = grpc.aio.insecure_channel(target)
        self._stub = amdi_pb2_grpc.DocumentIntelligenceStub(self._channel)
        self._meta = (("authorization", f"Bearer {api_key}"),) if api_key else ()

    async def health(self) -> amdi_pb2.HealthResponse:
        return await self._stub.Health(amdi_pb2.HealthRequest(), metadata=self._meta)

    async def upload(self, *, filename: str, mime_type: str,
                     data: bytes, user_id: str | None = None) -> amdi_pb2.UploadResponse:
        async def _gen():
            yield amdi_pb2.UploadRequest(metadata=amdi_pb2.UploadMetadata(
                filename=filename, mime_type=mime_type,
                user_id=user_id or "", expected_size_bytes=len(data),
            ))
            chunk_size = 1024 * 1024
            for i in range(0, len(data), chunk_size):
                yield amdi_pb2.UploadRequest(chunk=data[i:i + chunk_size])
        return await self._stub.Upload(_gen(), metadata=self._meta)

    async def query(self, raw: str, *, top_k: int = 10) -> amdi_pb2.RetrievalResult:
        return await self._stub.Query(
            amdi_pb2.QueryRequest(query=amdi_pb2.Query(raw=raw, top_k=top_k)),
            metadata=self._meta,
        )

    async def stream_events(self, job_id: str) -> AsyncIterator[amdi_pb2.JobEvent]:
        async for ev in self._stub.StreamJobEvents(
            amdi_pb2.GetJobRequest(job_id=job_id), metadata=self._meta,
        ):
            yield ev

    async def close(self) -> None:
        await self._channel.close()


__all__ = ["AmdiClient", "AsyncAmdiClient"]
