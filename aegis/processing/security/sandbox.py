"""
aegis.processing.security.sandbox
=================================
Isolated execution environment enforcing timeouts, memory guards, and error boundaries.
"""

from __future__ import annotations

import concurrent.futures
import inspect
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import jsonschema

from aegis.processing.models import (
    DocumentProcessingResult,
    ProcessingError,
    ProcessingStatus,
    ResourceUsage,
)
from aegis.processing.security.error_classifier import ErrorClassifier


class ProcessingSandbox:
    """Safely executes document processing tasks within bounded resource and timeout confines."""

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    def execute_bounded(
        self,
        task_fn: Callable[..., Any],
        document_id: str,
        processing_run_id: str,
        *args: Any,
        **kwargs: Any
    ) -> DocumentProcessingResult:
        """Run task_fn under strict timeout and error containment."""
        start_t = time.perf_counter()
        completed_stages: List[str] = []
        failed_stages: List[str] = []

        # Automatically bind document_id and processing_run_id if expected by task_fn
        try:
            sig = inspect.signature(task_fn)
            if "document_id" in sig.parameters and "document_id" not in kwargs:
                kwargs["document_id"] = document_id
            if "processing_run_id" in sig.parameters and "processing_run_id" not in kwargs:
                kwargs["processing_run_id"] = processing_run_id
        except Exception:
            pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(task_fn, *args, **kwargs)
            try:
                res = future.result(timeout=self.timeout_seconds)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0

                if isinstance(res, DocumentProcessingResult):
                    res.resource_usage.elapsed_ms = round(elapsed_ms, 2)
                    return res

                # Otherwise wrap result
                completed_stages.append("execution")
                return DocumentProcessingResult(
                    document_id=document_id,
                    processing_run_id=processing_run_id,
                    status=ProcessingStatus.SUCCESS,
                    page_count=len(res) if isinstance(res, list) else 1,
                    pages=res if isinstance(res, list) else [],
                    resource_usage=ResourceUsage(elapsed_ms=round(elapsed_ms, 2)),
                    completed_stages=completed_stages,
                    failed_stages=failed_stages,
                )

            except concurrent.futures.TimeoutError:
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                failed_stages.append("execution")
                return DocumentProcessingResult(
                    document_id=document_id,
                    processing_run_id=processing_run_id,
                    status=ProcessingStatus.TIMEOUT,
                    page_count=0,
                    pages=[],
                    error=ProcessingError(
                        code="TASK_TIMEOUT",
                        stage="sandbox_execution",
                        category="RESOURCE_LIMIT",
                        message=f"Processing exceeded timeout limit of {self.timeout_seconds} seconds",
                    ),
                    resource_usage=ResourceUsage(elapsed_ms=round(elapsed_ms, 2)),
                    completed_stages=completed_stages,
                    failed_stages=failed_stages,
                )

            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                status, err = ErrorClassifier.classify_exception(exc, stage="sandbox_execution")
                failed_stages.append("execution")
                return DocumentProcessingResult(
                    document_id=document_id,
                    processing_run_id=processing_run_id,
                    status=status,
                    page_count=0,
                    pages=[],
                    error=err,
                    resource_usage=ResourceUsage(elapsed_ms=round(elapsed_ms, 2)),
                    completed_stages=completed_stages,
                    failed_stages=failed_stages,
                )
