# AMDI-OS Benchmarking Framework

A comprehensive benchmarking suite for AMDI-OS to evaluate correctness, speed, resource footprint, and cost efficiency.

## Metrics Covered

1. **Accuracy** (`accuracy.py`): Cosine semantic similarity, token overlap F1, exact matching, and hybrid evaluation.
2. **Precision, Recall, F1** (`precision_recall.py`): Standard classification and information retrieval metrics.
3. **Latency** (`latency.py`): Statistical distribution of response times over multiple runs.
4. **Memory Footprint** (`memory_tracker.py`): Peak RAM, process virtual memory, and GPU VRAM profiling.
5. **Token Consumption** (`token_usage.py`): Track input/output LLM tokens used per section/engine.
6. **Operating Cost** (`cost.py`): Token cost based on provider pricing (OpenAI, Gemini, Claude, DeepSeek, local).
7. **Baselines** (`baseline.py`): RAG baseline comparison statistics.
8. **Statistical Significance** (`statistical_tests.py`): Wilcoxon and paired t-test significance calculators.
