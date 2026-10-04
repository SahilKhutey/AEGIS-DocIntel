'''
Compression metrics.
'''
from __future__ import annotations

from typing import Sequence


def compression_ratio(compressed: int, original: int) -> float:
    '''CR = compressed / original.'''
    if original == 0:
        return 1.0
    return compressed / original


def compression_percentage(compressed: int, original: int) -> float:
    '''CP = 1 - compressed/original.'''
    if original == 0:
        return 0.0
    return (1.0 - compressed / original) * 100.0


def information_retention(retained: int, original: int) -> float:
    '''IR = retained / original. Goal: > 0.95.'''
    if original == 0:
        return 1.0
    return min(1.0, retained / original)


def token_reduction(baseline_tokens: int, amdi_tokens: int) -> float:
    '''TR = 1 - amdi/baseline. Goal: 20-70%.'''
    if baseline_tokens == 0:
        return 0.0
    return max(0.0, 1.0 - amdi_tokens / baseline_tokens) * 100.0
