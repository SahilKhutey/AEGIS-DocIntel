"""arq WorkerSettings. Wire this to a Redis-backed worker via:

    arq amdi.jobs.worker.WorkerSettings

"""

from __future__ import annotations

from arq.connections import RedisSettings

from amdi.config import get_settings
from amdi.jobs.tasks import on_shutdown, on_startup, run_ingest


class WorkerSettings:
    """arq discovers this via its `arq <module>.WorkerSettings` convention."""

    functions = [run_ingest]
    on_startup = on_startup
    on_shutdown = on_shutdown
    keep_result = get_settings().job_keep_results_s
    max_tries = get_settings().job_max_retries
    job_timeout = get_settings().job_default_timeout_s
    queue_name = "amdi-ingest"
    redis_settings: RedisSettings = RedisSettings.from_dsn(get_settings().redis_url)


__all__ = ["WorkerSettings"]
