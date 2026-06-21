"""

Memory Tracker

===============



Profiles memory usage during pipeline execution.



Tracks:

    - Current RSS / heap

    - Peak memory

    - Memory delta (before/after operation)

    - Per-process / GPU memory (if available)

"""



from __future__ import annotations



import os

import tracemalloc

from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional





@dataclass

class MemorySnapshot:

    """A single memory snapshot."""



    timestamp: float

    rss_mb: float

    vms_mb: float

    heap_mb: Optional[float] = None

    gpu_mb: Optional[float] = None



    def to_dict(self) -> dict:

        return {

            "timestamp": round(self.timestamp, 3),

            "rss_mb": round(self.rss_mb, 3),

            "vms_mb": round(self.vms_mb, 3),

            "heap_mb": round(self.heap_mb, 3) if self.heap_mb is not None else None,

            "gpu_mb": round(self.gpu_mb, 3) if self.gpu_mb is not None else None,

        }





@dataclass

class MemoryResult:

    """Memory profiling result."""



    operation: str

    initial_mb: float

    peak_mb: float

    final_mb: float

    delta_mb: float

    snapshots: List[MemorySnapshot] = field(default_factory=list)



    def to_dict(self) -> dict:

        return {

            "operation": self.operation,

            "initial_mb": round(self.initial_mb, 3),

            "peak_mb": round(self.peak_mb, 3),

            "final_mb": round(self.final_mb, 3),

            "delta_mb": round(self.delta_mb, 3),

            "num_snapshots": len(self.snapshots),

            "snapshots": [s.to_dict() for s in self.snapshots],

        }





class MemoryTracker:

    """Track memory usage during operations."""



    def __init__(self, track_gpu: bool = False) -> None:

        self.track_gpu = track_gpu

        self._tracemalloc_started = False



    def _get_memory_mb(self) -> tuple:

        """Return (rss_mb, vms_mb)."""

        try:

            import psutil

            process = psutil.Process(os.getpid())

            mem = process.memory_info()

            return mem.rss / (1024 * 1024), mem.vms / (1024 * 1024)

        except ImportError:

            try:

                import resource

                usage = resource.getrusage(resource.RUSAGE_SELF)

                return (

                    usage.ru_maxrss / 1024.0,  # KB on Linux

                    usage.ru_maxrss / 1024.0,

                )

            except Exception:

                return 0.0, 0.0



    def _get_heap_mb(self) -> Optional[float]:

        """Return Python heap usage in MB."""

        if not self._tracemalloc_started:

            return None

        current, peak = tracemalloc.get_traced_memory()

        return peak / (1024 * 1024)



    def _get_gpu_mb(self) -> Optional[float]:

        """Return GPU memory usage in MB (if pynvml available)."""

        if not self.track_gpu:

            return None

        try:

            import pynvml

            pynvml.nvmlInit()

            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            return info.used / (1024 * 1024)

        except Exception:

            return None



    def snapshot(self) -> MemorySnapshot:

        """Capture a memory snapshot."""

        import time as _time

        rss, vms = self._get_memory_mb()

        return MemorySnapshot(

            timestamp=_time.time(),

            rss_mb=rss,

            vms_mb=vms,

            heap_mb=self._get_heap_mb(),

            gpu_mb=self._get_gpu_mb(),

        )



    def track(

        self,

        operation: str,

        func: Any,

        *args,

        **kwargs,

    ) -> tuple:

        """

        Track memory of `func(*args, **kwargs)`.



        Returns (result, MemoryResult).

        """

        if not self._tracemalloc_started:

            tracemalloc.start()

            self._tracemalloc_started = True

        snapshots: List[MemorySnapshot] = []

        initial = self.snapshot()

        snapshots.append(initial)

        peak_rss = initial.rss_mb

        try:

            result = func(*args, **kwargs)

            peak_snapshot = self.snapshot()

            snapshots.append(peak_snapshot)

            peak_rss = max(peak_rss, peak_snapshot.rss_mb)

            final = peak_snapshot

        except Exception as exc:

            final = self.snapshot()

            snapshots.append(final)

            peak_rss = max(peak_rss, final.rss_mb)

            raise exc

        memory_result = MemoryResult(

            operation=operation,

            initial_mb=initial.rss_mb,

            peak_mb=peak_rss,

            final_mb=final.rss_mb,

            delta_mb=final.rss_mb - initial.rss_mb,

            snapshots=snapshots,

        )

        return result, memory_result



    def reset(self) -> None:

        if self._tracemalloc_started:

            tracemalloc.stop()

            self._tracemalloc_started = False
