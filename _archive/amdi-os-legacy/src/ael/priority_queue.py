'''
AEGIS-AEL — Export Priority Queue
====================================
P = w_1·I + w_2·C + w_3·Q

Where:
    I = importance (from frequency/relevance)
    C = confidence (from retrieval scoring)
    Q = query relevance (from semantic similarity)
'''
from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np

logger = logging.getLogger('amdi.ael.priority_queue')


@dataclass(order=True)
class PrioritizedItem:
    priority: float
    counter: int = field(compare=True)
    item: Any = field(compare=False)
    metadata: dict = field(default_factory=dict, compare=False)


class ExportPriorityQueue:
    '''
    Maintains a max-heap of export candidates ranked by:
        P = w_1·I + w_2·C + w_3·Q
    '''

    def __init__(self, w_importance: float = 0.4, w_confidence: float = 0.3, w_query: float = 0.3):
        self.w_i = w_importance
        self.w_c = w_confidence
        self.w_q = w_query
        self._heap: list[PrioritizedItem] = []
        self._counter = 0
        self._items: set = set()  # dedup

    def add(
        self,
        item: Any,
        importance: float,
        confidence: float,
        query_relevance: float,
        token_cost: int = 0,
        dedup_key: str = '',
        metadata: dict | None = None,
    ) -> None:
        '''Add item with computed priority.'''
        raw_p = self._compute_priority(importance, confidence, query_relevance)
        if token_cost > 0:
            raw_p = raw_p / np.log(2 + token_cost / 100)
        priority = -raw_p
        key = dedup_key or str(id(item))
        if key in self._items:
            return
        self._items.add(key)
        self._counter += 1
        self._heap.append(PrioritizedItem(
            priority=priority, counter=self._counter, item=item,
            metadata={'tokens': token_cost, **(metadata or {})},
        ))
        heapq.heapify(self._heap)

    def _compute_priority(self, importance: float, confidence: float, query_relevance: float) -> float:
        return self.w_i * importance + self.w_c * confidence + self.w_q * query_relevance

    def pop_top(self, n: int = 1) -> list[PrioritizedItem]:
        out: list[PrioritizedItem] = []
        for _ in range(min(n, len(self._heap))):
            if self._heap:
                p_item = heapq.heappop(self._heap)
                p_item.priority = -p_item.priority
                out.append(p_item)
        return out

    def peek(self, n: int = 5) -> list[PrioritizedItem]:
        sorted_items = sorted(self._heap, key=lambda x: x.priority)
        out = []
        for x in sorted_items[:n]:
            item_copy = PrioritizedItem(priority=-x.priority, counter=x.counter, item=x.item, metadata=x.metadata)
            out.append(item_copy)
        return out

    def __len__(self) -> int:
        return len(self._heap)

    def statistics(self) -> dict:
        if not self._heap:
            return {'size': 0}
        priorities = [-item.priority for item in self._heap]
        return {
            'size': len(self._heap),
            'max_priority': max(priorities),
            'min_priority': min(priorities),
            'mean_priority': float(np.mean(priorities)),
        }
