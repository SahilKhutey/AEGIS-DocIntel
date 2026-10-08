"""
Example: using the submodular context packer as a LlamaIndex node
post-processor, replacing naive top-k truncation with relevance-aware
budget-constrained packing.
"""

from __future__ import annotations

from typing import List
from llama_index.core.schema import NodeWithScore, TextNode

from aegis_docprep.context_packer import ContextChunk, SubmodularKnapsackPacker


class SubmodularPackingPostprocessor:
    """LlamaIndex Node Post-processor for diversity and relevance knapsack packing."""

    def __init__(self, token_budget: int = 2000):
        self.packer = SubmodularKnapsackPacker()
        self.token_budget = token_budget

    def postprocess_nodes(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        chunks = [
            ContextChunk(
                chunk_id=n.node.node_id,
                text=n.node.text,
                relevance_score=n.score or 0.0,
                token_cost=len(n.node.text.split()),
            )
            for n in nodes
        ]
        result = self.packer.pack_context(chunks, max_budget=self.token_budget)
        selected_ids = {c.chunk_id for c in result.selected_chunks}
        return [n for n in nodes if n.node.node_id in selected_ids]


if __name__ == "__main__":
    nodes = [
        NodeWithScore(
            node=TextNode(text="Q3 enterprise software revenue jumped 28% to $450M.", id_="n1"),
            score=0.92,
        ),
        NodeWithScore(
            node=TextNode(text="The cafeteria serves sandwiches on Thursdays.", id_="n2"),
            score=0.15,
        ),
        NodeWithScore(
            node=TextNode(text="Operating cash flow reached record highs of $120M.", id_="n3"),
            score=0.88,
        ),
        NodeWithScore(
            node=TextNode(text="Employee badges must be scanned at gate 4.", id_="n4"),
            score=0.20,
        ),
    ]

    postprocessor = SubmodularPackingPostprocessor(token_budget=16)
    selected_nodes = postprocessor.postprocess_nodes(nodes)

    print(f"Selected {len(selected_nodes)} nodes within budget:")
    for sn in selected_nodes:
        print(f"[{sn.node.node_id}] (score={sn.score}): {sn.node.text}")
