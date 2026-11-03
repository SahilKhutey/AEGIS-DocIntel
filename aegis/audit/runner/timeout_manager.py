"""
aegis/audit/runner/timeout_manager.py
=====================================
Cross-platform execution timeout manager.
"""

from __future__ import annotations

import concurrent.futures
import time
from typing import Any, Callable, Dict, Optional, Tuple
from aegis.audit.runner.exceptions import TimeoutException


class TimeoutManager:
    """Manages synchronous function execution with a strict wall-clock timeout ceiling."""

    @staticmethod
    def execute(
        func: Callable[..., Any],
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[float] = None,
    ) -> Any:
        if kwargs is None:
            kwargs = {}

        if timeout_seconds is None or timeout_seconds <= 0:
            return func(*args, **kwargs)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise TimeoutException(
                    f"Execution exceeded configured timeout ceiling of {timeout_seconds}s"
                )
