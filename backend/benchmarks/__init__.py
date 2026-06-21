"""

AMDI-OS Benchmarking Framework

===============================



Comprehensive benchmarking suite for AMDI-OS.



Metrics:

    - Accuracy    : correct / total

    - Precision   : TP / (TP + FP)

    - Recall      : TP / (TP + FN)

    - F1          : 2·P·R / (P + R)

    - Latency     : response time (ms)

    - Memory      : peak RSS / GPU (MB)

    - Token Usage : tokens consumed

    - Cost        : USD per query



Datasets:

    - Scientific Papers

    - Invoices

    - Reports

    - Manuals

    - Books

    - Engineering Drawings



Baselines:

    - PDF → OCR → Chunk → Embed → Vector DB → LLM (vanilla RAG)

    - Direct LLM

    - AMDI-OS (full pipeline)



Statistical Tests:

    - Paired t-test

    - Wilcoxon signed-rank

    - Confidence intervals (95%)



Author : AMDI-OS Development Team

Version: 1.0.0

"""



from .benchmark_engine import (

    BenchmarkEngine,

    BenchmarkResult,

    BenchmarkSuite,

)

from .accuracy import AccuracyBenchmark, AccuracyResult

from .precision_recall import (

    PrecisionRecallBenchmark,

    PrecisionRecallResult,

    F1Result,

)

from .latency import LatencyBenchmark, LatencyResult, LatencyStats

from .memory_tracker import MemoryTracker, MemoryResult

from .token_usage import TokenUsageBenchmark, TokenResult

from .cost import CostBenchmark, CostResult, CostModel

from .ground_truth import GroundTruth, GroundTruthEntry

from .dataset_loader import DatasetLoader, BenchmarkDataset

from .metrics_aggregator import MetricsAggregator, AggregatedMetrics

from .report_generator import ReportGenerator, BenchmarkReport

from .baseline import BaselineComparator, BaselineResult

from .statistical_tests import StatisticalTests, SignificanceResult

from .exceptions import (

    BenchmarkError,

    DatasetMissingError,

    MetricComputationError,

)



__all__ = [

    "BenchmarkEngine",

    "BenchmarkResult",

    "BenchmarkSuite",

    "AccuracyBenchmark",

    "AccuracyResult",

    "PrecisionRecallBenchmark",

    "PrecisionRecallResult",

    "F1Result",

    "LatencyBenchmark",

    "LatencyResult",

    "LatencyStats",

    "MemoryTracker",

    "MemoryResult",

    "TokenUsageBenchmark",

    "TokenResult",

    "CostBenchmark",

    "CostResult",

    "CostModel",

    "GroundTruth",

    "GroundTruthEntry",

    "DatasetLoader",

    "BenchmarkDataset",

    "MetricsAggregator",

    "AggregatedMetrics",

    "ReportGenerator",

    "BenchmarkReport",

    "BaselineComparator",

    "BaselineResult",

    "StatisticalTests",

    "SignificanceResult",

    "BenchmarkError",

    "DatasetMissingError",

    "MetricComputationError",

]



__version__ = "1.0.0"
