'''
Answer, citation, table and hallucination accuracy metrics.
'''
from __future__ import annotations

import re


def answer_accuracy(answer: str, expected: str) -> float:
    '''Token-level F1 between answer and expected.'''
    ans_tokens = set(re.findall(r'\w+', answer.lower()))
    exp_tokens = set(re.findall(r'\w+', expected.lower()))
    if not exp_tokens:
        return 1.0 if not ans_tokens else 0.0
    if not ans_tokens:
        return 0.0
    common = ans_tokens & exp_tokens
    precision = len(common) / len(ans_tokens)
    recall = len(common) / len(exp_tokens)
    if precision + recall == 0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def citation_accuracy(
    answer: str, expected_pages: list[int], expected_citations: list[dict]
) -> float:
    '''Check that cited pages match expected.'''
    cited = set()
    for m in re.finditer(r'page\s+(\d+)|p\.?\s*(\d+)|\[p(\d+)', answer, re.IGNORECASE):
        for g in m.groups():
            if g:
                try:
                    cited.add(int(g))
                except ValueError:
                    pass
    if not expected_pages and not expected_citations:
        return 1.0 if not cited else 0.5
    expected = set(expected_pages)
    if not cited:
        return 0.0
    if not expected:
        return 0.0
    return len(cited & expected) / len(cited | expected)


def table_accuracy(answer: str, expected_values: list[float], tolerance: float = 0.05) -> float:
    '''Check numerical values in answer match expected.'''
    if not expected_values:
        return 1.0
    # Extract numbers from answer
    found = []
    for m in re.finditer(r'\$?[\d,]+(?:\.\d+)?', answer):
        try:
            v = float(m.group().replace('$', '').replace(',', ''))
            found.append(v)
        except ValueError:
            pass
    if not found:
        return 0.0
    correct = 0
    for exp in expected_values:
        for f in found:
            if abs(f - exp) <= abs(exp) * tolerance + 1e-6:
                correct += 1
                break
    return correct / len(expected_values)


def hallucination_rate(answer: str, ground_truth_context: str) -> float:
    '''Estimate hallucination rate via unsupported claims.'''
    ans_words = set(re.findall(r'\w+', answer.lower()))
    gt_words = set(re.findall(r'\w+', ground_truth_context.lower()))
    if not ans_words:
        return 0.0
    # Claims are content words not in ground truth
    stop = {'the', 'a', 'an', 'is', 'are', 'was', 'of', 'in', 'to', 'and', 'or', 'for', 'on', 'at', 'by'}
    content = ans_words - stop
    if not content:
        return 0.0
    unsupported = content - gt_words
    return len(unsupported) / len(content)


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)
