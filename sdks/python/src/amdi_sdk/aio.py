"""Async wrapper over the same generated stubs."""

from __future__ import annotations

import os
from typing import AsyncIterator

import grpc

from amdi_sdk.proto import amdi_pb2, amdi_pb2_grpc

TARGET = os.environ.get("AMDI_GRPC_TARGET", "localhost:50051")


class AsyncAmdiClient:
    def __init__(self, target: str = TARGET, *, api_key: str | None = None) -> None:
        self._channel = grpc.aio.insecure_channel(target)
        self._stub = amdi_pb2_grpc.DocumentIntelligenceStub(self._channel)
        self._md = (("authorization", f"Bearer {api_key}"),) if api_key else ()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    async def health(self) -> amdi_pb2.HealthResponse:
        return await self._stub.Health(amdi_pb2.HealthRequest(), metadata=self._md)

    async def upload(self, *, filename: str, mime_type: str,
                     data: bytes, user_id: str | None = None) -> amdi_pb2.UploadResponse:
        async def _gen():
            yield amdi_pb2.UploadRequest(metadata=amdi_pb2.UploadMetadata(
                filename=filename, mime_type=mime_type,
                user_id=user_id or "", expected_size_bytes=len(data),
            ))
            step = 1024 * 1024
            for i in range(0, len(data), step):
                yield amdi_pb2.UploadRequest(chunk=data[i:i + step])
        return await self._stub.Upload(_gen(), metadata=self._md)

    async def query(self, raw: str, *, top_k: int = 10) -> amdi_pb2.RetrievalResult:
        return await self._stub.Query(
            amdi_pb2.QueryRequest(query=amdi_pb2.Query(raw=raw, top_k=top_k)),
            metadata=self._md,
        )

    async def stream_events(self, job_id: str) -> AsyncIterator[amdi_pb2.JobEvent]:
        async for ev in self._stub.StreamJobEvents(
            amdi_pb2.GetJobRequest(job_id=job_id), metadata=self._md,
        ):
            yield ev

    async def close(self) -> None:
        await self._channel.close()


__all__ = ["AsyncAmdiClient"]
