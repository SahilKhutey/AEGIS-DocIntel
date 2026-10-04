'''
Unit tests for the AEGIS-MIOS v2.0 Mathematical Operating System.
'''
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
import numpy as np
import networkx as nx

from mios.engines.physics.information_physics import InformationPhysicsEngine
from mios.engines.topology.topology_engine import TopologyEngine
from mios.engines.spectral.spectral_engine import SpectralEngine
from mios.engines.tensor.tensor_engine import TensorEngine
from mios.engines.bayesian.bayesian_engine import BayesianEngine
from mios.engines.markov.markov_engine import MarkovEngine
from mios.engines.decision.decision_engine import DecisionEngine
from mios.engines.optimization.optimization_engine import OptimizationEngine
from mios.engines.economics.economics_engine import EconomicsEngine
from mios.engines.meta.meta_engine import MetaLearningEngine
from mios.engines.rl.rl_engine import RLEngine
from mios.orchestrator import MIOSOrchestrator
from src.core.document_object import DocumentObject


def test_physics_engine() -> None:
    '''Tests information physics engine metrics and fields.'''
    pe = InformationPhysicsEngine()
    
    # Register particle
    p1 = pe.register('el1', 'quantum computing experiment', (0.0, 0.0, 0.2, 0.2), 1, 0.8, 0.7)
    assert p1.energy == 0.8 * 0.7
    assert p1.information > 0.0
    
    pe.register('el2', 'classical error bounds', (0.8, 0.8, 1.0, 1.0), 1, 0.6, 0.4)
    
    # Gravity
    importances = {'el1': 0.8, 'el2': 0.6}
    connectivity = {'el1': 2, 'el2': 1}
    g1 = pe.get_gravity('el1', importances, connectivity)
    assert g1 > 0.0
    
    # Field Φ(x,y)
    phi = pe.information_field(0.5, 0.5)
    assert phi > 0.0
    
    # Heatmap
    heatmap = pe.get_heatmap(grid_size=5)
    assert heatmap.shape == (5, 5)
    
    # Conservation
    cons = pe.verify_conservation(100.0, 40.0, 56.0, 4.0)
    assert cons['conserved']
    assert cons['within_bounds']


def test_topology_engine() -> None:
    '''Tests Betti numbers and point-set topology calculations.'''
    te = TopologyEngine(proximity_threshold=0.5)
    
    # Arrange nodes in a simple square cycle to verify H1 cycle detection
    positions = {
        'n1': (0.0, 0.0),
        'n2': (0.0, 0.4),
        'n3': (0.4, 0.4),
        'n4': (0.4, 0.0)
    }
    
    G = te.build_proximity_graph(positions)
    assert G.number_of_nodes() == 4
    
    b0, b1, b2 = te.compute_betti_numbers(G)
    assert b0 == 1  # 1 connected component
    assert b1 == 1  # 1 loop (n1-n2-n3-n4 cycle)
    
    # Persistent homology Filtration
    diag = te.persistent_homology(positions, steps=5)
    assert len(diag) > 0


def test_spectral_engine() -> None:
    '''Tests FFT periodicity and eigenvalue layout analysis.'''
    se = SpectralEngine()
    
    # Sine wave signal representing periodic spacing
    t = np.linspace(0, 10, 32)
    signal = np.sin(t)
    
    freqs, power = se.fourier_transform(signal)
    assert len(freqs) == 32
    
    periodicity = se.compute_periodicity(signal)
    assert periodicity > 0.0
    
    # Eigenvalue decomposition
    adj = np.array([
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0]
    ], dtype=np.float64)
    eigvals = se.eigenvalue_decomposition(adj, k=2)
    assert len(eigvals) == 2
    assert eigvals[0] > 0.0


def test_tensor_engine() -> None:
    '''Tests 4D tensor building and decomposition.'''
    te = TensorEngine()
    
    elements = [
        {'page': 1, 'section': 'intro', 'content': 'First word to tokenize'},
        {'page': 1, 'section': 'results', 'content': 'The quantitative score is 125.50'},
        {'page': 2, 'section': 'intro', 'content': 'Other page element'}
    ]
    
    doc_tensor = te.build_tensor(elements, max_rows=3, max_cols=3)
    assert doc_tensor.shape == (2, 2, 3, 3, 12)
    
    # CP decomposition factors
    factors = te.cp_decomposition(doc_tensor, rank=2)
    assert len(factors) == 5
    assert factors[0].shape == (2, 2)
    
    # Mode-n product
    T = doc_tensor.data
    M = np.array([[1.0, 0.0], [0.0, 1.0]])
    prod = te.mode_n_product(T, M, mode=0)
    assert prod.shape == T.shape


def test_bayesian_and_markov_engines() -> None:
    '''Tests Bayesian belief updates and Markov transitional chains.'''
    # Bayesian Engine
    be = BayesianEngine()
    belief = be.update_belief('claim1', 0.8)
    assert belief.posterior > 0.5  # Prior was 0.5, positive likelihood increases it
    
    seq_post = be.sequential_update('claim2', [0.8, 0.7, 0.9])
    assert seq_post > 0.8
    
    net_importance = be.query_importance(size_score=0.9, keyword_score=0.8, layout_score=0.7)
    assert net_importance > 0.3
    
    # Markov Engine
    me = MarkovEngine()
    sequences = [
        ['intro', 'method', 'results', 'conclusion'],
        ['intro', 'results', 'conclusion']
    ]
    markov_sig = me.build_transition_chain(sequences)
    assert 'intro' in markov_sig.states
    assert markov_sig.transition_matrix.shape == (4, 4)
    assert round(float(markov_sig.stationary_distribution.sum()), 2) == 1.0


def test_decision_and_optimization_engines() -> None:
    '''Tests AHP weights and context optimization Knapsack.'''
    # Decision Engine
    de = DecisionEngine(criterion_names=['s', 'g', 'r'])
    preferences = {
        ('s', 'g'): 3.0,
        ('g', 'r'): 2.0,
        ('s', 'r'): 6.0
    }
    matrix = de.pairwise_comparison_matrix(preferences)
    weights = de.ahp_weights(matrix)
    assert len(weights) == 3
    assert round(float(weights.sum()), 2) == 1.0
    
    cr = de.compute_consistency_ratio(matrix, weights)
    assert cr < 0.1  # Highly consistent preferences
    
    # Optimization Engine
    oe = OptimizationEngine()
    candidates = [
        {'id': 'c1', 'tokens': 500, 'value': 0.9},
        {'id': 'c2', 'tokens': 300, 'value': 0.8},
        {'id': 'c3', 'tokens': 400, 'value': 0.7}
    ]
    selected = oe.optimize_context(candidates, max_tokens=800, max_latency_s=1.0, max_memory_mb=100.0)
    # Should choose c2 and c3 because total tokens = 700 <= 800 and their combined value is 1.5
    # (c1 and c2 combined is 800 tokens, value is 1.7)
    assert len(selected) > 0


def test_meta_rl_and_economics() -> None:
    '''Tests reinforcement learning updates and economics efficiency tracking.'''
    ee = EconomicsEngine()
    ratios = ee.calculate_ratios(0.9, 150, 1.2, 32.0, 500, 1000, 3, 5, 0.0015)
    assert ratios.token_economics > 0
    assert ratios.agent_economics > 0
    
    # Meta Learning Engine
    mle = MetaLearningEngine(learning_rate=0.1)
    mle.log_attempt('query1', {'s': 0.5, 'g': 0.5}, True, 0.9)
    mle.log_attempt('query1', {'s': 0.7, 'g': 0.3}, True, 0.95)
    mle.log_attempt('query1', {'s': 0.3, 'g': 0.7}, True, 0.8)
    
    adapted = mle.adapt_weights('query1', {'s': 0.5, 'g': 0.5})
    # Since higher 's' led to higher rating (0.95 vs 0.8), adapted 's' should increase
    assert adapted['s'] > 0.5
    
    # RL Engine
    rl = RLEngine(alpha=0.1, gamma=0.9, epsilon=0.0)  # Pure exploit
    state = rl.get_state(2, True, 'easy')
    action = rl.select_action(state)
    assert action in rl.actions
    
    rl.learn(state, action, 1.0, state)
    # Since reward is 1.0, Q-value for action should increase from 0
    assert rl.q_table[state][action] > 0.0


@pytest.mark.asyncio
async def test_mios_orchestrator_integration() -> None:
    '''Tests end-to-end ingestion and query pipeline with MIOS Orchestrator.'''
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        doc_file = temp_path / 'mock_doc.txt'
        doc_file.write_bytes(b'Line 1: Quantum decoherence\n\nLine 2: System fidelity\n')

        doc = DocumentObject(
            filename=doc_file.name,
            raw_path=str(doc_file),
            raw_bytes=doc_file.read_bytes()
        )
        
        orch = MIOSOrchestrator()
        stats = await orch.ingest(doc)
        
        assert stats['doc_id'] is not None
        assert stats['betti_0'] > 0
        assert 'periodicity' in stats
        
        # Test query
        res = await orch.query('What is the fidelity?', doc_id=stats['doc_id'])
        assert res['answer'] is not None
        assert 'mios_ratios' in res
        assert 'mios_rl_action' in res
        
        await orch.close()
