"""
AMDI-OS Advanced Analytics: Cost Optimizer
==========================================

Analyzes query paths, token usage, storage costs, and identifies redundancy.
Generates structured recommendations for caching, model quantization, or model routing.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import time


@dataclass
class QueryCostRecord:
    query_text: str
    model_name: str
    tokens_input: int
    tokens_output: int
    estimated_cost_usd: float
    latency_sec: float
    timestamp: float


class CostOptimizer:
    """
    Evaluates resource consumption profiles and issues actionable optimization recommendations.
    """
    def __init__(self):
        self.query_logs: List[QueryCostRecord] = []
        # Pricing sheet per 1K tokens
        self.model_pricing: Dict[str, Dict[str, float]] = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "custom-slm-dense": {"input": 0.0005, "output": 0.001},
            "custom-slm-quantized": {"input": 0.0001, "output": 0.0002},
        }
        # Storage cost per doc chunk (vector dimension + text storage)
        self.storage_cost_per_chunk = 0.00005  # USD per chunk per month

    def log_query_execution(self, query_text: str, model_name: str, tokens_input: int, tokens_output: int, latency_sec: float) -> QueryCostRecord:
        """
        Logs a query execution record and automatically computes costs based on pricing.
        """
        rates = self.model_pricing.get(model_name, {"input": 0.001, "output": 0.002})
        input_cost = (tokens_input / 1000.0) * rates["input"]
        output_cost = (tokens_output / 1000.0) * rates["output"]
        total_cost = input_cost + output_cost

        record = QueryCostRecord(
            query_text=query_text.strip(),
            model_name=model_name,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            estimated_cost_usd=total_cost,
            latency_sec=latency_sec,
            timestamp=time.time()
        )
        self.query_logs.append(record)
        return record

    def recommend_caching(self, repetition_threshold: int = 3) -> List[Dict[str, Any]]:
        """
        Scans logs for repeated queries and recommends caching if repetitions exceed threshold.
        """
        counts: Dict[str, List[QueryCostRecord]] = {}
        for log in self.query_logs:
            counts.setdefault(log.query_text, []).append(log)

        recommendations = []
        for text, logs in counts.items():
            rep_count = len(logs)
            if rep_count >= repetition_threshold:
                total_cost = sum(l.estimated_cost_usd for l in logs)
                # Potential savings is cost of all but the first call
                potential_savings = total_cost - logs[0].estimated_cost_usd
                avg_latency = sum(l.latency_sec for l in logs) / rep_count
                
                recommendations.append({
                    "type": "CACHE_QUERY",
                    "target": f"Query: '{text[:40]}...'",
                    "repetition_count": rep_count,
                    "estimated_monthly_savings_usd": potential_savings * 30,  # Extrapolated to month (assuming logs represent 1 day)
                    "reason": f"Query repeated {rep_count} times, consuming ${total_cost:.4f} USD and averaging {avg_latency:.2f}s latency.",
                    "action": "Enable semantic caching on this query pattern."
                })
        
        # Sort by savings descending
        recommendations.sort(key=lambda x: x["estimated_monthly_savings_usd"], reverse=True)
        return recommendations

    def recommend_model_routing(self) -> List[Dict[str, Any]]:
        """
        Recommends downscaling to smaller SLMs or quantized models for simple queries.
        If queries are short and use large expensive models, recommend routing to smaller model.
        """
        recommendations = []
        expensive_logs = [l for l in self.query_logs if l.model_name in ("gpt-4", "large-llm")]
        if not expensive_logs:
            return recommendations

        simple_queries_count = 0
        total_simple_cost = 0.0
        
        for log in expensive_logs:
            # Heuristic: Simple queries have <= 15 input tokens and <= 30 output tokens
            if log.tokens_input <= 15 and log.tokens_output <= 30:
                simple_queries_count += 1
                total_simple_cost += log.estimated_cost_usd

        if simple_queries_count > 0:
            # Routing to custom-slm-dense would reduce input cost to 1/60th and output to 1/60th roughly.
            # Assume 80% cost savings
            potential_savings = total_simple_cost * 0.8
            recommendations.append({
                "type": "MODEL_ROUTING",
                "target": "Router Configuration",
                "estimated_monthly_savings_usd": potential_savings * 30,  # Monthly projection
                "reason": f"Found {simple_queries_count} simple, short queries routed to expensive model '{expensive_logs[0].model_name}'.",
                "action": "Route short, simple queries to custom-slm-dense or custom-slm-quantized model."
            })

        return recommendations

    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        """
        Aggregates all cost optimization recommendations.
        """
        recs = []
        recs.extend(self.recommend_caching())
        recs.extend(self.recommend_model_routing())
        return recs
