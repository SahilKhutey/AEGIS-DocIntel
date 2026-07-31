"""arq client and worker lifecycle management.

Why arq?
- Native asyncio (matches the rest of the stack)
- Simple Redis backend, no broker-specific knowledge needed
- Built-in retries, cron, and result TTL
- Lower cognitive load than Celery for a brand-new codebase

If you outgrow arq, the only file you replace is this one.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import arq
from arq.connections import ArqRedis, RedisSettings, create_pool

from amdi.config import get_settings

if TYPE_CHECKING:
    from amdi.jobs.worker import WorkerSettings

logger = logging.getLogger("amdi.services.queue")


def _redis_settings() -> RedisSettings:
    s = get_settings()
    # arq parses URL itself; prefer URL form for clarity
    return RedisSettings.from_dsn(s.redis_url)


class QueueClient:
    """Thin wrapper around arq.create_pool with reconnect + health probe."""

    def __init__(self) -> None:
        self._pool: ArqRedis | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._pool is not None:
            return
        async with self._lock:
            if self._pool is None:
                self._pool = await create_pool(_redis_settings())
                logger.info("queue.connected")

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.aclose()  # type: ignore[attr-defined]
            self._pool = None
            logger.info("queue.disconnected")

    @property
    def pool(self) -> ArqRedis:
        if self._pool is None:
            raise RuntimeError("QueueClient not connected; call await connect() first")
        return self._pool

    async def healthcheck(self) -> bool:
        if self._pool is None:
            return False
        try:
            pong = await self._pool.ping()
            return bool(pong)
        except Exception as exc:  # noqa: BLE001
            logger.warning("queue.healthcheck_failed", error=str(exc))
            return False

    async def enqueue_ingest(
        self,
        *,
        job_id: str,
        document_id: str,
        user_id: str | None,
        file_path: str,
        mime_type: str,
        max_retries: int,
    ) -> None:
        """Enqueue an ingestion job.

        Returns immediately. Worker will pick it up.
        """
        await self.pool.enqueue_job(
            "amdi.jobs.tasks.run_ingest",
            job_id=job_id,
            document_id=document_id,
            user_id=user_id,
            file_path=file_path,
            mime_type=mime_type,
            _job_id=job_id,            # arq internal job id
            _queue_name="amdi-ingest",
            _max_tries=max_retries,
        )


__all__ = ["QueueClient", "WorkerSettings"]
