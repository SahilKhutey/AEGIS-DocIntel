"""
AMDI-OS Optimization Framework
================================

Optimizes AMDI-OS pipeline across 4 dimensions:
    - Token Optimization      : reduce LLM tokens
    - Memory Optimization      : minimize RAM usage
    - Latency Optimization     : speed up operations
    - Retrieval Optimization   : speed up retrieval

Mathematical Foundation:
    Token reduction:
        R_token = 1 - tokens_optimized / tokens_baseline

    Memory reduction:
        R_memory = 1 - memory_optimized / memory_baseline

    Latency reduction:
        R_latency = 1 - latency_optimized / latency_baseline

    Retrieval speedup:
        S = latency_baseline / latency_optimized

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .optimization_engine import (
    OptimizationEngine,
    OptimizationResult,
    OptimizationSuite,
)
from .token_optimizer import (
    TokenOptimizer,
    TokenOptimizationResult,
    TokenStrategy,
)
from .memory_optimizer import (
    MemoryOptimizer,
    MemoryOptimizationResult,
    MemoryStrategy,
)
from .latency_optimizer import (
    LatencyOptimizer,
    LatencyOptimizationResult,
    LatencyStrategy,
)
from .retrieval_optimizer import (
    RetrievalOptimizer,
    RetrievalOptimizationResult,
    RetrievalStrategy,
)
from .cache_optimizer import (
    CacheOptimizer,
    CacheOptimizationResult,
)
from .batching_optimizer import (
    BatchingOptimizer,
    BatchResult,
)
from .profiling import (
    Profiler,
    ProfileResult,
    profile,
)
from .optimization_report import (
    OptimizationReport,
    OptimizationMetrics,
)
from .exceptions import (
    OptimizationError,
    OptimizationTargetError,
)

__all__ = [
    "OptimizationEngine",
    "OptimizationResult",
    "OptimizationSuite",
    "TokenOptimizer",
    "TokenOptimizationResult",
    "TokenStrategy",
    "MemoryOptimizer",
    "MemoryOptimizationResult",
    "MemoryStrategy",
    "LatencyOptimizer",
    "LatencyOptimizationResult",
    "LatencyStrategy",
    "RetrievalOptimizer",
    "RetrievalOptimizationResult",
    "RetrievalStrategy",
    "CacheOptimizer",
    "CacheOptimizationResult",
    "BatchingOptimizer",
    "BatchResult",
    "Profiler",
    "ProfileResult",
    "profile",
    "OptimizationReport",
    "OptimizationMetrics",
    "OptimizationError",
    "OptimizationTargetError",
]

__version__ = "1.0.0"
