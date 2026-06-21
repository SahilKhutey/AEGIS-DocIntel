"""

Cost Benchmark

==============



Calculates total cost of running the AMDI-OS pipeline

based on token usage, compute, and storage.



Mathematical Foundation:

    Cost = (input_tokens / 1000) · in_rate

        + (output_tokens / 1000) · out_rate

        + compute_cost

        + storage_cost

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional





@dataclass

class CostModel:

    """Cost model configuration."""



    input_price_per_1k: float = 0.005

    output_price_per_1k: float = 0.015

    compute_price_per_hour: float = 0.10

    storage_price_per_gb_month: float = 0.023

    name: str = "default"



    def to_dict(self) -> dict:

        return {

            "name": self.name,

            "input_price_per_1k": self.input_price_per_1k,

            "output_price_per_1k": self.output_price_per_1k,

            "compute_price_per_hour": self.compute_price_per_hour,

            "storage_price_per_gb_month": self.storage_price_per_gb_month,

        }





@dataclass

class CostResult:

    """Cost benchmark result."""



    total_cost_usd: float

    token_cost_usd: float

    compute_cost_usd: float

    storage_cost_usd: float

    cost_per_query_usd: float

    num_queries: int

    total_input_tokens: int

    total_output_tokens: int

    model_name: str

    cost_breakdown: Dict[str, float] = field(default_factory=dict)



    def to_dict(self) -> dict:

        return {

            "total_cost_usd": round(self.total_cost_usd, 6),

            "token_cost_usd": round(self.token_cost_usd, 6),

            "compute_cost_usd": round(self.compute_cost_usd, 6),

            "storage_cost_usd": round(self.storage_cost_usd, 6),

            "cost_per_query_usd": round(self.cost_per_query_usd, 6),

            "num_queries": self.num_queries,

            "total_input_tokens": self.total_input_tokens,

            "total_output_tokens": self.total_output_tokens,

            "model_name": self.model_name,

            "cost_breakdown": {k: round(v, 6) for k, v in self.cost_breakdown.items()},

        }





class CostBenchmark:

    """Compute total cost of pipeline execution."""



    def __init__(self, cost_model: Optional[CostModel] = None) -> None:

        self.cost_model = cost_model or CostModel()

        self.total_input_tokens = 0

        self.total_output_tokens = 0

        self.compute_seconds = 0.0

        self.storage_gb = 0.0

        self.queries = 0



    def record_query(

        self,

        input_tokens: int,

        output_tokens: int,

        compute_seconds: float = 0.0,

    ) -> None:

        self.total_input_tokens += input_tokens

        self.total_output_tokens += output_tokens

        self.compute_seconds += compute_seconds

        self.queries += 1



    def set_storage(self, gb: float) -> None:

        self.storage_gb = gb



    def compute(self) -> CostResult:

        """Compute final cost breakdown."""

        token_cost = (

            (self.total_input_tokens / 1000) * self.cost_model.input_price_per_1k

            + (self.total_output_tokens / 1000) * self.cost_model.output_price_per_1k

        )

        compute_cost = (

            (self.compute_seconds / 3600.0) * self.cost_model.compute_price_per_hour

        )

        storage_cost = (

            self.storage_gb * self.cost_model.storage_price_per_gb_month

        )

        total_cost = token_cost + compute_cost + storage_cost

        cost_per_query = total_cost / max(self.queries, 1)

        return CostResult(

            total_cost_usd=total_cost,

            token_cost_usd=token_cost,

            compute_cost_usd=compute_cost,

            storage_cost_usd=storage_cost,

            cost_per_query_usd=cost_per_query,

            num_queries=self.queries,

            total_input_tokens=self.total_input_tokens,

            total_output_tokens=self.total_output_tokens,

            model_name=self.cost_model.name,

            cost_breakdown={

                "input_tokens": (

                    self.total_input_tokens / 1000 * self.cost_model.input_price_per_1k

                ),

                "output_tokens": (

                    self.total_output_tokens / 1000 * self.cost_model.output_price_per_1k

                ),

                "compute": compute_cost,

                "storage": storage_cost,

            },

        )



    def reset(self) -> None:

        self.total_input_tokens = 0

        self.total_output_tokens = 0

        self.compute_seconds = 0.0

        self.storage_gb = 0.0

        self.queries = 0
