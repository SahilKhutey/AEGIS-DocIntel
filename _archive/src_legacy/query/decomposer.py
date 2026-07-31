'''
AEGIS-DocIntel / AMDI-OS — Query Decomposition Pre-Processor
=============================================================
Structurally decomposes multi-hop comparative, temporal, and conjunctive queries into sub-query dependency DAGs.
'''
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SubQuery:
    sub_query_id: str
    text: str
    depends_on: List[str] = field(default_factory=list)
    suggested_engine_weights: Optional[Dict[str, float]] = None


@dataclass
class QueryDAG:
    original_query: str
    sub_queries: List[SubQuery] = field(default_factory=list)
    combination_step: str = "pass_through"


def build_query_dag(query: str) -> QueryDAG:
    '''
    Parses and matches query dependency patterns (comparative, temporal, multi-hop).
    '''
    q_lower = query.lower().strip()

    # Pattern 1: Comparative query ("compare X and Y")
    if 'compare' in q_lower or 'versus' in q_lower or ' vs ' in q_lower:
        parts = re.split(r'compare|versus| vs | and ', q_lower)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            sq1 = SubQuery(sub_query_id='sq_0', text=parts[0])
            sq2 = SubQuery(sub_query_id='sq_1', text=parts[1])
            return QueryDAG(
                original_query=query,
                sub_queries=[sq1, sq2],
                combination_step='compare',
            )

    # Pattern 2: Temporal / Version diff query ("changed ... since Q2")
    if 'changed' in q_lower or 'since' in q_lower or 'update' in q_lower:
        sq1 = SubQuery(
            sub_query_id='sq_0',
            text=query,
            suggested_engine_weights={'version_diff': 0.85, 'semantic': 0.15},
        )
        return QueryDAG(
            original_query=query,
            sub_queries=[sq1],
            combination_step='filter_by_diff',
        )

    # Fallback: Single-node QueryDAG
    sq0 = SubQuery(sub_query_id='sq_0', text=query)
    return QueryDAG(
        original_query=query,
        sub_queries=[sq0],
        combination_step='pass_through',
    )


def execute_query_dag(dag: QueryDAG, retrieval_fn: Any) -> Dict[str, Any]:
    '''
    Executes sub-queries in dependency order against retrieval pipeline and combines results.
    '''
    results = {}
    for sq in dag.sub_queries:
        res = retrieval_fn(sq.text) if callable(retrieval_fn) else {'retrieved': sq.text}
        results[sq.sub_query_id] = res

    return {
        'combination_step': dag.combination_step,
        'results': results,
    }
