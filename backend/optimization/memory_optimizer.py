"""
Memory Optimizer
==================

Strategies to reduce memory consumption:

    - LAZY_LOAD: defer loading until needed
    - CHUNK: process in chunks
    - COMPRESS: use lower precision (fp16, int8)
    - STREAMING: process data as stream
    - POOLING: reuse memory pools
    - GC: aggressive garbage collection
    - DISK_OFFLOAD: spill to disk
    - QUANTIZE: reduce tensor precision

Mathematical Foundation:
    R_memory = 1 - peak_optimized / peak_baseline

    Compression ratio:
        C = bytes_original / bytes_compressed
"""

from __future__ import annotations

import gc
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np


class MemoryStrategy(Enum):
    """Memory optimization strategies."""

    LAZY_LOAD = "lazy_load"
    CHUNK = "chunk"
    COMPRESS = "compress"
    STREAMING = "streaming"
    POOLING = "pooling"
    GC = "gc"
    DISK_OFFLOAD = "disk_offload"
    QUANTIZE = "quantize"


@dataclass
class MemoryOptimizationResult:
    """Result of memory optimization."""

    strategy: str
    original_bytes: int
    optimized_bytes: int
    bytes_saved: int
    reduction_pct: float
    peak_before_mb: float = 0.0
    peak_after_mb: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "original_bytes": self.original_bytes,
            "optimized_bytes": self.optimized_bytes,
            "bytes_saved": self.bytes_saved,
            "reduction_pct": round(self.reduction_pct, 4),
            "peak_before_mb": round(self.peak_before_mb, 2),
            "peak_after_mb": round(self.peak_after_mb, 2),
        }


class MemoryOptimizer:
    """
    Apply memory optimization strategies.
    """

    def __init__(self, target_reduction_pct: float = 0.30) -> None:
        self.target_reduction_pct = target_reduction_pct

    def get_memory_usage(self) -> float:
        """Return current process memory in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

    def force_gc(self) -> MemoryOptimizationResult:
        """Force garbage collection."""
        before = self.get_memory_usage()
        collected = gc.collect()
        after = self.get_memory_usage()
        saved_mb = max(0.0, before - after)
        return MemoryOptimizationResult(
            strategy="gc",
            original_bytes=int(before * 1024 * 1024),
            optimized_bytes=int(after * 1024 * 1024),
            bytes_saved=int(saved_mb * 1024 * 1024),
            reduction_pct=saved_mb / max(before, 1e-9),
            peak_before_mb=before,
            peak_after_mb=after,
            metadata={"objects_collected": collected},
        )

    def quantize_array(
        self,
        arr: np.ndarray,
        target_dtype: str = "float16",
    ) -> tuple:
        """
        Quantize array to lower precision.

        Returns (quantized_array, MemoryOptimizationResult).
        """
        original_bytes = arr.nbytes
        dtype_map = {
            "float64": np.float64,
            "float32": np.float32,
            "float16": np.float16,
            "int64": np.int64,
            "int32": np.int32,
            "int16": np.int16,
            "int8": np.int8,
        }
        if target_dtype not in dtype_map:
            raise ValueError(f"Unsupported dtype: {target_dtype}")
        target_dt = dtype_map[target_dtype]
        # scale to fit in target range
        if np.issubdtype(arr.dtype, np.floating):
            arr_min = arr.min()
            arr_max = arr.max()
            if arr_max > arr_min:
                if target_dt == np.float16 or target_dt == np.float32:
                    quantized = arr.astype(target_dt)
                else:  # integer
                    target_info = np.iinfo(target_dt)
                    scale = (arr_max - arr_min) / (target_info.max - target_info.min)
                    quantized = ((arr - arr_min) / scale + target_info.min).astype(target_dt)
            else:
                quantized = arr.astype(target_dt)
        else:
            quantized = arr.astype(target_dt)
        new_bytes = quantized.nbytes
        saved = original_bytes - new_bytes
        result = MemoryOptimizationResult(
            strategy="quantize",
            original_bytes=original_bytes,
            optimized_bytes=new_bytes,
            bytes_saved=saved,
            reduction_pct=saved / max(original_bytes, 1),
            metadata={
                "original_dtype": str(arr.dtype),
                "target_dtype": target_dtype,
            },
        )
        return quantized, result

    def chunk_process(
        self,
        data: np.ndarray,
        chunk_size: int,
        process_fn: Any,
    ) -> tuple:
        """
        Process array in chunks to limit peak memory.

        Returns (results_list, MemoryOptimizationResult).
        """
        original_bytes = data.nbytes
        # estimate peak: one chunk at a time
        n_chunks = max(1, (len(data) + chunk_size - 1) // chunk_size)
        chunk_bytes = original_bytes // n_chunks
        results: List[Any] = []
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            results.append(process_fn(chunk))
        new_peak_bytes = chunk_bytes
        result = MemoryOptimizationResult(
            strategy="chunk",
            original_bytes=original_bytes,
            optimized_bytes=new_peak_bytes,
            bytes_saved=original_bytes - new_peak_bytes,
            reduction_pct=(original_bytes - new_peak_bytes) / max(original_bytes, 1),
            peak_after_mb=new_peak_bytes / (1024 * 1024),
            metadata={"n_chunks": n_chunks, "chunk_size": chunk_size},
        )
        return results, result

    def compress_array(
        self,
        arr: np.ndarray,
    ) -> tuple:
        """
        Compress array using sparse representation if applicable.

        Returns (compressed, MemoryOptimizationResult).
        """
        original_bytes = arr.nbytes
        # check sparsity
        non_zero_ratio = float(np.count_nonzero(arr)) / max(arr.size, 1)
        if non_zero_ratio < 0.3:
            from scipy.sparse import csr_matrix
            compressed = csr_matrix(arr.reshape(-1) if arr.ndim == 1 else arr)
            compressed_back = compressed.toarray().reshape(arr.shape)
            new_bytes = (
                compressed.data.nbytes
                + compressed.indices.nbytes
                + compressed.indptr.nbytes
            )
            result = MemoryOptimizationResult(
                strategy="compress",
                original_bytes=original_bytes,
                optimized_bytes=new_bytes,
                bytes_saved=original_bytes - new_bytes,
                reduction_pct=(original_bytes - new_bytes) / max(original_bytes, 1),
                metadata={"sparsity": 1 - non_zero_ratio, "format": "csr"},
            )
            return compressed_back, result
        return arr, MemoryOptimizationResult(
            strategy="compress",
            original_bytes=original_bytes,
            optimized_bytes=original_bytes,
            bytes_saved=0,
            reduction_pct=0.0,
            metadata={"reason": "not_sparse_enough"},
        )

    def stream_iterate(
        self,
        data: List[Any],
        process_fn: Any,
        batch_size: int = 100,
    ) -> tuple:
        """Stream process large lists in batches."""
        original_bytes = sum(
            sys.getsizeof(item) if not isinstance(item, np.ndarray)
            else item.nbytes
            for item in data
        )
        peak_bytes = 0
        results: List[Any] = []
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            batch_results = process_fn(batch)
            results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
            # estimate peak
            batch_bytes = sum(
                sys.getsizeof(item) if not isinstance(item, np.ndarray)
                else item.nbytes
                for item in batch
            )
            peak_bytes = max(peak_bytes, batch_bytes)
            # cleanup
            del batch
        result = MemoryOptimizationResult(
            strategy="streaming",
            original_bytes=original_bytes,
            optimized_bytes=peak_bytes,
            bytes_saved=original_bytes - peak_bytes,
            reduction_pct=(original_bytes - peak_bytes) / max(original_bytes, 1),
            metadata={"batch_size": batch_size, "num_batches": (len(data) + batch_size - 1) // batch_size},
        )
        return results, result

    def apply_all(
        self,
        data: np.ndarray,
    ) -> tuple:
        """Apply all safe optimizations in sequence."""
        results: List[MemoryOptimizationResult] = []
        # 1. force GC
        gc_result = self.force_gc()
        results.append(gc_result)
        # 2. quantize
        try:
            quantized, q_result = self.quantize_array(data, "float16")
            results.append(q_result)
        except Exception:
            quantized = data
        # 3. compress (sparse)
        try:
            compressed, c_result = self.compress_array(quantized)
            results.append(c_result)
        except Exception:
            compressed = quantized
        total_original = sum(r.original_bytes for r in results)
        total_optimized = max(
            (r.optimized_bytes for r in results),
            default=0,
        )
        # aggregate
        agg = MemoryOptimizationResult(
            strategy="combined",
            original_bytes=total_original,
            optimized_bytes=total_optimized,
            bytes_saved=total_original - total_optimized,
            reduction_pct=(total_original - total_optimized) / max(total_original, 1),
            metadata={"steps": [r.strategy for r in results]},
        )
        return compressed, agg
