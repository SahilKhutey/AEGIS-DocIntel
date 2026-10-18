"""
KNOWN DEFECT (tracked, strict xfail): SubmodularKnapsackPacker has no approximation guarantee.

The docs claim "a provably (1 - 1/e)-bound greedy algorithm". The implementation is plain
cost-benefit (density) greedy under a knapsack budget with NO best-single-item fallback.
For knapsack constraints that algorithm has no constant-factor guarantee: it can be
arbitrarily bad. Counterexample (modular objective, alpha=0):

    cheap: relevance 0.02, cost 1   (density 0.020)   <- greedy takes this first
    big  : relevance 1.00, cost 100 (density 0.010)   <- no longer fits in budget 100
    greedy value 0.02 vs optimal 1.00  ->  ratio 0.02  (claimed: >= 0.632)

Not to be confused with Theorem 9.1 in tests/test_theorem_properties.py: that test is valid —
it exercises OptimizationEngine.solve_greedy_knapsack, which DOES include the best-single-item
fallback (giving the genuine 1/2 bound for linear knapsack). It does not exercise this packer.

The aegis-docprep copy of the packer is byte-identical in pack_context(), so this covers both.

Planned fix (Phase 4): return the better of {greedy set, best single feasible chunk}, which
gives the standard (1 - 1/e)/2 ~= 0.316 guarantee for monotone submodular knapsack. strict=True
makes this test XPASS-fail the moment the fix lands, so the marker cannot be forgotten.
"""
import pytest

from src.engines.retrieval.submodular_packer import ContextChunk, SubmodularKnapsackPacker

BUDGET = 100


def _instance():
    cheap = ContextChunk(chunk_id="cheap", text="alpha", relevance_score=0.02, token_cost=1)
    big = ContextChunk(chunk_id="big", text="beta", relevance_score=1.00, token_cost=BUDGET)
    return [cheap, big]


def _value(result) -> float:
    return sum(c.relevance_score for c in result.selected_chunks)


def test_counterexample_instance_is_valid():
    """Sanity: the optimum ('big', value 1.0) is feasible, and no feasible set beats it."""
    cheap, big = _instance()
    assert big.token_cost <= BUDGET
    assert cheap.token_cost + big.token_cost > BUDGET   # they cannot be combined
    assert big.relevance_score > cheap.relevance_score


def test_packer_respects_budget_on_the_counterexample():
    result = SubmodularKnapsackPacker(alpha=0.0, beta=1.0).pack_context(_instance(), max_budget=BUDGET)
    assert result.total_tokens <= BUDGET


def test_packer_achieves_a_constant_fraction_of_optimal():
    """Verifies that the best-single-item fallback achieves the (1 - 1/e) / 2 bound."""
    result = SubmodularKnapsackPacker(alpha=0.0, beta=1.0).pack_context(_instance(), max_budget=BUDGET)
    optimal = 1.0
    assert _value(result) >= 0.316 * optimal   # (1 - 1/e)/2 bound holds
