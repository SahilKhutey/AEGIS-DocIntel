# AMDI-OS Optimization Framework

Comprehensive, pipeline-wide optimization suite across four core channels.

## Directory Structure

```
backend/optimization/
├── __init__.py
├── optimization_engine.py       # Main orchestrator
├── token_optimizer.py           # Token reduction strategies
├── memory_optimizer.py           # Memory management
├── latency_optimizer.py          # Latency reduction
├── retrieval_optimizer.py        # Retrieval speedup
├── cache_optimizer.py            # Cache tuning
├── batching_optimizer.py         # Batch processing
├── profiling.py                  # Profiling utilities
├── optimization_report.py        # Report generation
├── exceptions.py                 # Custom exceptions
└── README.md
```

## Mathematical Foundation

### 1. Token Reduction
$$R_{\text{token}} = 1 - \frac{\text{tokens}_{\text{optimized}}}{\text{tokens}_{\text{baseline}}}$$
Where:
- $R_{\text{token}}$ is the token reduction rate.
- $\text{tokens}_{\text{baseline}}$ is the input token count prior to optimization.
- $\text{tokens}_{\text{optimized}}$ is the input token count after deduplication/MMR selection.

### 2. Memory Reduction
$$R_{\text{memory}} = 1 - \frac{\text{memory}_{\text{optimized}}}{\text{memory}_{\text{baseline}}}$$
Where:
- $R_{\text{memory}}$ is the memory reduction rate.
- $\text{memory}_{\text{baseline}}$ is the peak RAM footprint prior to optimization.
- $\text{memory}_{\text{optimized}}$ is the peak RAM footprint after quantization/chunk-based processing.

### 3. Latency Reduction
$$R_{\text{latency}} = 1 - \frac{\text{latency}_{\text{optimized}}}{\text{latency}_{\text{baseline}}}$$
Where:
- $R_{\text{latency}}$ is the latency reduction rate.
- $\text{latency}_{\text{baseline}}$ is the runtime prior to optimization.
- $\text{latency}_{\text{optimized}}$ is the runtime after parallelization/caching.

### 4. Retrieval Speedup
$$S = \frac{\text{latency}_{\text{baseline}}}{\text{latency}_{\text{optimized}}}$$
Where:
- $S$ is the retrieval speedup ratio.
- $\text{latency}_{\text{baseline}}$ is the exact flat vector lookup time.
- $\text{latency}_{\text{optimized}}$ is the approximate IVF partitioned vector search time.

## Usage

Create an `OptimizationSuite`, add the configurations, and execute with `OptimizationEngine`:

```python
from backend.optimization import (
    OptimizationEngine,
    OptimizationSuite,
    TokenStrategy,
    MemoryStrategy,
    LatencyStrategy,
    RetrievalStrategy
)

# 1. Initialize Suite
suite = OptimizationSuite("Production Pipeline Tuning")

# 2. Add Token Chunking
suite.add_token_optimization(
    strategy=TokenStrategy.MMR_DIVERSITY,
    text="",
    texts=["chunk 1", "chunk 2", "chunk 3"],
    embeddings=my_embeddings,
    top_k=2
)

# 3. Add Memory Quantization
suite.add_memory_optimization(
    strategy=MemoryStrategy.QUANTIZE,
    data=my_float32_array,
    target_dtype="float16"
)

# 4. Run Optimization Engine
engine = OptimizationEngine()
result = engine.run_suite(suite, output_dir="./optimized_reports")

print(f"Status: {result.metrics.status}")
print(f"Token Saved: {result.metrics.token_reduction_pct:.2%}")
print(f"Memory Saved: {result.metrics.memory_reduction_pct:.2%}")
```
