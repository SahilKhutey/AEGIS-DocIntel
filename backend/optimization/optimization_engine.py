"""
Optimization Engine
====================

Main orchestrator class running the Optimization Framework across all 4 levels.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .exceptions import OptimizationError, OptimizationTargetError
from .token_optimizer import TokenOptimizer, TokenOptimizationResult, TokenStrategy
from .memory_optimizer import MemoryOptimizer, MemoryOptimizationResult, MemoryStrategy
from .latency_optimizer import LatencyOptimizer, LatencyOptimizationResult, LatencyStrategy
from .retrieval_optimizer import RetrievalOptimizer, RetrievalOptimizationResult, RetrievalStrategy
from .optimization_report import OptimizationReport, OptimizationMetrics


@dataclass
class OptimizationResult:
    """Consolidated result of an Optimization Engine run."""

    suite_name: str
    passed: bool
    metrics: OptimizationMetrics
    report: OptimizationReport
    report_json_path: Optional[str] = None
    report_markdown_path: Optional[str] = None


class OptimizationSuite:
    """A suite defining optimizations to execute across levels."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.token_optimizations: List[Dict[str, Any]] = []
        self.memory_optimizations: List[Dict[str, Any]] = []
        self.latency_optimizations: List[Dict[str, Any]] = []
        self.retrieval_optimizations: List[Dict[str, Any]] = []

    def add_token_optimization(
        self,
        strategy: TokenStrategy,
        text: str,
        target_tokens: int = 100,
        **kwargs,
    ) -> None:
        self.token_optimizations.append({
            "strategy": strategy,
            "text": text,
            "target_tokens": target_tokens,
            "kwargs": kwargs,
        })

    def add_memory_optimization(
        self,
        strategy: MemoryStrategy,
        data: Any,
        **kwargs,
    ) -> None:
        self.memory_optimizations.append({
            "strategy": strategy,
            "data": data,
            "kwargs": kwargs,
        })

    def add_latency_optimization(
        self,
        strategy: LatencyStrategy,
        operations: List[Callable],
        **kwargs,
    ) -> None:
        self.latency_optimizations.append({
            "strategy": strategy,
            "operations": operations,
            "kwargs": kwargs,
        })

    def add_retrieval_optimization(
        self,
        strategy: RetrievalStrategy,
        embeddings: Any,
        query: Any,
        **kwargs,
    ) -> None:
        self.retrieval_optimizations.append({
            "strategy": strategy,
            "embeddings": embeddings,
            "query": query,
            "kwargs": kwargs,
        })


class OptimizationEngine:
    """Orchestrates optimizations across the AMDI-OS pipeline."""

    def __init__(
        self,
        target_token_reduction: float = 0.20,
        target_memory_reduction: float = 0.20,
        target_latency_reduction: float = 0.20,
        target_retrieval_speedup: float = 1.30,
    ) -> None:
        self.target_token_reduction = target_token_reduction
        self.target_memory_reduction = target_memory_reduction
        self.target_latency_reduction = target_latency_reduction
        self.target_retrieval_speedup = target_retrieval_speedup

        self.token_opt = TokenOptimizer(target_reduction_pct=target_token_reduction)
        self.memory_opt = MemoryOptimizer(target_reduction_pct=target_memory_reduction)
        self.latency_opt = LatencyOptimizer()
        self.retrieval_opt = RetrievalOptimizer(target_speedup=target_retrieval_speedup)

    def run_suite(
        self,
        suite: OptimizationSuite,
        output_dir: Optional[str] = None,
    ) -> OptimizationResult:
        """Run the registered optimization suite across all channels."""
        report = OptimizationReport(suite.name)

        # 1. Run Token Optimizations
        for item in suite.token_optimizations:
            strategy = item["strategy"]
            text = item["text"]
            target = item["target_tokens"]
            kwargs = item["kwargs"]
            
            if strategy == TokenStrategy.TRUNCATE:
                res = self.token_opt.truncate(text, target)
            elif strategy == TokenStrategy.SUMMARIZE:
                res = self.token_opt.summarize(text, target, kwargs.get("summarizer"))
            elif strategy == TokenStrategy.COMPRESS:
                res = self.token_opt.compress(text, kwargs.get("target_reduction", 0.3))
            elif strategy == TokenStrategy.SELECT:
                res = self.token_opt.select(
                    kwargs.get("texts", [text]),
                    kwargs.get("top_k", 2),
                    kwargs.get("relevance_scores"),
                )
            elif strategy == TokenStrategy.DEDUPLICATE:
                res = self.token_opt.deduplicate(kwargs.get("texts", [text]))
            elif strategy == TokenStrategy.MMR_DIVERSITY:
                res = self.token_opt.mmr_select(
                    kwargs.get("texts", [text]),
                    kwargs.get("embeddings", np.zeros((1, 1))),
                    kwargs.get("top_k", 1),
                    kwargs.get("lambda_param", 0.7),
                )
            else:
                raise OptimizationError(f"Unsupported token strategy: {strategy}")
            report.add_token_result(res)

        # 2. Run Memory Optimizations
        for item in suite.memory_optimizations:
            strategy = item["strategy"]
            data = item["data"]
            kwargs = item["kwargs"]

            if strategy == MemoryStrategy.GC:
                res = self.memory_opt.force_gc()
            elif strategy == MemoryStrategy.QUANTIZE:
                _, res = self.memory_opt.quantize_array(data, kwargs.get("target_dtype", "float16"))
            elif strategy == MemoryStrategy.CHUNK:
                _, res = self.memory_opt.chunk_process(data, kwargs.get("chunk_size", 10), kwargs.get("process_fn"))
            elif strategy == MemoryStrategy.COMPRESS:
                _, res = self.memory_opt.compress_array(data)
            elif strategy == MemoryStrategy.STREAMING:
                _, res = self.memory_opt.stream_iterate(data, kwargs.get("process_fn"), kwargs.get("batch_size", 10))
            else:
                raise OptimizationError(f"Unsupported memory strategy: {strategy}")
            report.add_memory_result(res)

        # 3. Run Latency Optimizations
        for item in suite.latency_optimizations:
            strategy = item["strategy"]
            ops = item["operations"]
            kwargs = item["kwargs"]

            if strategy == LatencyStrategy.PARALLELIZE:
                _, res = self.latency_opt.parallelize(ops, kwargs.get("max_workers", 4))
            elif strategy == LatencyStrategy.CACHE:
                _, res = self.latency_opt.cached_call(kwargs.get("key", "op"), ops[0])
            elif strategy == LatencyStrategy.BATCH:
                _, res = self.latency_opt.batch_operations(
                    kwargs.get("items", []),
                    kwargs.get("batch_fn"),
                    kwargs.get("batch_size", 32),
                )
            else:
                raise OptimizationError(f"Unsupported latency strategy: {strategy}")
            report.add_latency_result(res)

        # 4. Run Retrieval Optimizations
        for item in suite.retrieval_optimizations:
            strategy = item["strategy"]
            embs = item["embeddings"]
            query = item["query"]
            kwargs = item["kwargs"]

            if strategy == RetrievalStrategy.INDEX:
                _, res = self.retrieval_opt.optimize_index(embs, query, kwargs.get("top_k", 5), kwargs.get("n_centroids", 4))
            elif strategy == RetrievalStrategy.PRUNE:
                _, res = self.retrieval_opt.prune_search_space(
                    kwargs.get("candidates", []),
                    kwargs.get("filter_fn"),
                    kwargs.get("search_fn"),
                )
            elif strategy == RetrievalStrategy.HYBRID:
                _, res = self.retrieval_opt.hybrid_retrieval(
                    kwargs.get("dense_results", []),
                    kwargs.get("sparse_results", []),
                    kwargs.get("weight_dense", 0.5),
                )
            elif strategy == RetrievalStrategy.QUANTIZE:
                _, res = self.retrieval_opt.quantize_embeddings(embs)
            elif strategy == RetrievalStrategy.RERANK:
                _, res = self.retrieval_opt.rerank(
                    kwargs.get("candidates", []),
                    kwargs.get("rerank_fn"),
                    kwargs.get("top_n", 10),
                )
            else:
                raise OptimizationError(f"Unsupported retrieval strategy: {strategy}")
            report.add_retrieval_result(res)

        # Compute metrics & compare with targets
        metrics = report.compute_metrics()
        
        # Verify if targets are met or if there is general improvement
        passed = True
        if metrics.token_reduction_pct < self.target_token_reduction and len(suite.token_optimizations) > 0:
            passed = False
        if metrics.memory_reduction_pct < self.target_memory_reduction and len(suite.memory_optimizations) > 0:
            passed = False
        if metrics.latency_reduction_pct < self.target_latency_reduction and len(suite.latency_optimizations) > 0:
            passed = False
        if metrics.retrieval_speedup < self.target_retrieval_speedup and len(suite.retrieval_optimizations) > 0:
            passed = False

        # Output reports to disk if directory provided
        json_path = None
        md_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            json_path = os.path.join(output_dir, "optimization_report.json")
            md_path = os.path.join(output_dir, "optimization_report.md")
            
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())

        return OptimizationResult(
            suite_name=suite.name,
            passed=passed,
            metrics=metrics,
            report=report,
            report_json_path=json_path,
            report_markdown_path=md_path,
        )
