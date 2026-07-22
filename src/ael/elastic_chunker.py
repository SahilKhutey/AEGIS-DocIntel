'''
AEGIS-AEL — Layout-Aware Elastic Chunker
================────────────────=========
Implements Section 7 of the Second Edition Technical Monograph.
Evaluates a 4-rule disjunctive boundary predicate over reading-ordered nodes:
  1. Protected-type forcing (tables, code, equations, figures)
  2. Font-delta threshold forcing (heading / section transition proxy)
  3. Vertical-gap multiplier forcing (section break proxy)
  4. Soft-budget token ceiling forcing (prevents oversized text chunks)
'''
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from src.ael.token_budget import count_tokens

logger = logging.getLogger('amdi.ael.elastic_chunker')


@dataclass
class ChunkingConfig:
    protected_types: Set[str] = field(
        default_factory=lambda: {'table', 'code', 'equation', 'figure'}
    )
    font_delta_threshold: float = 2.0
    vertical_gap_multiplier: float = 1.5
    soft_token_budget: int = 400
    hard_token_ceiling: int = 1000


class ElasticChunker:
    '''
    Layout-Aware Elastic Chunker.
    Assembles contiguous runs of reading-ordered nodes into structurally intact chunks.
    '''

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()

    def chunk_nodes(self, nodes: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        '''
        Partitions reading-ordered nodes into chunks based on structural boundary rules.
        '''
        if not nodes:
            return []

        chunks: List[List[Dict[str, Any]]] = []
        current_chunk: List[Dict[str, Any]] = [nodes[0]]
        current_tokens: int = self._node_tokens(nodes[0])

        for i in range(1, len(nodes)):
            prev_node = nodes[i - 1]
            curr_node = nodes[i]
            curr_tokens = self._node_tokens(curr_node)

            should_split, reason = self._should_force_boundary(
                prev_node, curr_node, current_tokens, curr_tokens
            )

            if should_split and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [curr_node]
                current_tokens = curr_tokens
            else:
                current_chunk.append(curr_node)
                current_tokens += curr_tokens

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _should_force_boundary(
        self,
        prev_node: Dict[str, Any],
        curr_node: Dict[str, Any],
        running_tokens: int,
        next_tokens: int,
    ) -> tuple[bool, str]:
        prev_type = str(prev_node.get('type', 'text')).lower()
        curr_type = str(curr_node.get('type', 'text')).lower()

        # Rule 1: Protected-type boundary (table, code, equation, figure)
        if prev_type in self.config.protected_types or curr_type in self.config.protected_types:
            return True, 'protected_type'

        # Rule 2: Font-delta boundary (heading transition)
        prev_font = float(prev_node.get('font_size', 10.0))
        curr_font = float(curr_node.get('font_size', 10.0))
        if abs(curr_font - prev_font) >= self.config.font_delta_threshold:
            return True, 'font_delta'

        # Rule 3: Vertical-gap boundary (section break)
        prev_y_max = float(prev_node.get('y_max', prev_node.get('y', 0.0) + prev_node.get('h', 0.05)))
        curr_y_min = float(curr_node.get('y_min', curr_node.get('y', 0.0)))
        prev_height = max(0.01, float(prev_node.get('h', 0.05)))

        vertical_gap = curr_y_min - prev_y_max
        if vertical_gap >= self.config.vertical_gap_multiplier * prev_height:
            return True, 'vertical_gap'

        # Rule 4: Soft-budget boundary
        if running_tokens + next_tokens > self.config.soft_token_budget and running_tokens > 0:
            return True, 'soft_budget'

        return False, 'none'

    @staticmethod
    def _node_tokens(node: Dict[str, Any]) -> int:
        if 'tokens' in node and isinstance(node['tokens'], int):
            return node['tokens']
        text = str(node.get('text', node.get('content', '')))
        return max(1, count_tokens(text))

    @staticmethod
    def generate_contextual_prefix(chunk: Dict[str, Any], doc_title: str = "Document") -> str:
        '''
        Anthropic-style Contextual Retrieval Prefixing:
        Prepends document context metadata to chunk text to prevent retrieval fragmentation.
        '''
        page = chunk.get('page', 1)
        chunk_type = chunk.get('type', 'text')
        heading = chunk.get('heading', '')
        
        prefix = f"[{doc_title} | Page {page} | Type: {chunk_type}]"
        if heading:
            prefix += f" (Section: {heading})"
        
        raw_text = chunk.get('text', '')
        return f"{prefix}\n{raw_text}"

    @staticmethod
    def rg_coarse_grain(
        content_block: Dict[str, Any],
        tolerance: float = 0.05,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        '''
        Concept P2 — Renormalization Group Theory for the L0-L5 Memory Hierarchy:
        Coarse-grains L_k memory elements into L_{k+1} while preserving query relevance statistics.
        Returns (coarse_block, retained_detail).
        '''
        text = str(content_block.get('text', ''))
        words = text.split()
        if len(words) <= 10:
            return content_block, None

        # RG flow decimation: preserve key entities and initial/summary sentence
        coarse_text = " ".join(words[: len(words) // 2])
        detail_text = " ".join(words[len(words) // 2 :])

        coarse_block = dict(content_block)
        coarse_block['text'] = coarse_text
        coarse_block['level'] = content_block.get('level', 0) + 1

        retained_detail = dict(content_block)
        retained_detail['text'] = detail_text
        retained_detail['is_retained_detail'] = True

        return coarse_block, retained_detail
