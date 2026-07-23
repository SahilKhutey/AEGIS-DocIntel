"""
Unit tests for the Information Physics Engine.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.engines.info_physics import (
    InformationPhysicsEngine,
    EnergyCalculator,
    GravityCalculator,
    PotentialCalculator,
    FieldCalculator,
    FlowCalculator,
    ConservationLaw,
    ConservationChecker,
    Thermodynamics,
    PhysicsMetricsCalculator,
    PhysicsEngineError,
    InvalidDocumentError,
    ConservationViolationError,
)


def test_energy_calculator() -> None:
    # Test shape mismatch
    calc = EnergyCalculator()
    with pytest.raises(InvalidDocumentError):
        calc.compute(np.array([0.5]), np.array([0.5, 0.6]))

    # Test empty input
    with pytest.raises(InvalidDocumentError):
        calc.compute(np.array([]), np.array([]))

    # Test weights sum validation
    with pytest.raises(ValueError):
        EnergyCalculator(entropy_weight=-0.5, relevance_weight=0.5)

    # Test correct computation
    entropy = np.array([0.8, 0.4])
    relevance = np.array([0.9, 0.2])
    field = calc.compute(entropy, relevance)
    
    assert field.total_energy > 0
    assert field.mean_energy > 0
    assert field.max_energy_element == 0
    assert isinstance(field.energies, dict)
    assert len(field.energies) == 2

    # Test from frequencies
    freqs = {"term1": 10, "term2": 2}
    rel = {"term1": 0.9, "term2": 0.1}
    field_f = calc.compute_from_frequencies(freqs, rel)
    assert field_f.total_energy > 0
    assert field_f.max_energy_element in [0, 1]

    # Test from frequencies empty validation
    with pytest.raises(InvalidDocumentError):
        calc.compute_from_frequencies({})


def test_gravity_calculator() -> None:
    calc = GravityCalculator()
    
    importance = np.array([0.9, 0.5])
    connectivity = np.array([0.8, 0.2])
    distances = np.array([[0.0, 2.0], [2.0, 0.0]])
    
    # Test shape mismatch
    with pytest.raises(InvalidDocumentError):
        calc.compute(importance, connectivity, np.array([[0.0]]))

    field = calc.compute(importance, connectivity, distances)
    assert field.total_gravity > 0
    assert field.mean_gravity > 0
    assert field.strongest_attractor in [0, 1]
    assert field.gravity.shape == (2,)
    assert field.gravity_matrix.shape == (2, 2)

    attractors = calc.top_attractors(field, k=1)
    assert len(attractors) == 1
    assert attractors[0][0] in [0, 1]


def test_potential_calculator() -> None:
    calc = PotentialCalculator()
    
    importance = np.array([0.9, 0.5])
    y_coords = np.array([10.0, 50.0]) # top of page = 10.0, bottom = 50.0
    
    # Test empty input
    with pytest.raises(InvalidDocumentError):
        calc.compute(np.array([]))

    field = calc.compute_from_layout(importance, y_coords)
    assert field.total_potential > 0
    assert field.mean_potential > 0
    assert field.max_element == 0  # y=10 should have higher potential score (1.0 vs 0.0)
    assert field.max_potential > 0.0


def test_field_calculator() -> None:
    calc = FieldCalculator()
    
    positions = np.array([[0.0, 0.0], [1.0, 1.0]])
    weights = np.array([1.0, 0.5])
    
    # Test validation
    with pytest.raises(InvalidDocumentError):
        calc.compute(np.array([0.0, 0.0]), weights)
        
    info_field = calc.compute(positions, weights, grid_size=(10, 10))
    assert info_field.total_field_energy > 0
    assert info_field.mean_field_strength > 0
    assert info_field.max_density_location == (3, 3) # grid index mapping to source at [0.0, 0.0]
    
    # Gradients & Laplacians
    dy, dx = info_field.field_map.gradient()
    assert dy.shape == (10, 10)
    assert dx.shape == (10, 10)
    
    laplacian = info_field.field_map.laplacian()
    assert laplacian.shape == (10, 10)

    # Heatmaps
    att = calc.attention_map(positions, weights, grid_size=(10, 10))
    assert att.shape == (10, 10)
    assert np.max(att) <= 1.0
    
    pri = calc.priority_map(positions, weights, threshold=0.5, grid_size=(10, 10))
    assert pri.shape == (10, 10)
    assert set(np.unique(pri)).issubset({0.0, 1.0})


def test_flow_calculator() -> None:
    calc = FlowCalculator()
    
    t0 = np.array([0.5, 0.6])
    t1 = np.array([0.7, 0.4])
    
    # Delta
    delta = calc.compute_delta(t0, t1)
    assert np.allclose(delta, np.array([0.2, -0.2]))
    
    # Flow
    flow = calc.compute_flow(t0, t1, adjacency=np.ones((2, 2)))
    assert flow.total_inflow > 0
    assert flow.total_outflow > 0
    assert flow.most_dynamic_element in [0, 1]
    
    # Flow vector
    vec = calc.flow_vector(0, 1, 0.5, 0.7)
    assert vec.source_id == 0
    assert vec.target_id == 1
    assert vec.is_inflow()
    assert not vec.is_outflow()


def test_thermodynamics() -> None:
    thermo = Thermodynamics()
    
    importance = np.array([0.9, 0.1])
    state = thermo.compute_state(importance)
    
    assert state.entropy > 0
    assert state.effective_temperature > 0
    assert state.internal_energy == 1.0
    assert isinstance(state.to_dict(), dict)


def test_conservation_law() -> None:
    law = ConservationLaw(max_discarded_fraction=0.05)
    
    # Test correct conservation
    rep = law.check(100.0, 40.0, 56.0, 4.0)
    assert rep.is_conserved
    assert rep.conservation_error == 0.0
    assert rep.discarded_fraction == 0.04
    
    # Test strict violation
    with pytest.raises(ConservationViolationError):
        law.check(100.0, 40.0, 50.0, 4.0, strict=True)
        
    # Vector checker
    checker = ConservationChecker()
    v_in = np.array([10.0, 0.0])
    v_out = np.array([8.0, 0.0])
    v_comp = np.array([2.0, 0.0])
    v_disc = np.array([0.0, 0.0])
    
    rep_v = checker.check_from_arrays(v_in, v_out, v_comp, v_disc)
    assert rep_v.is_conserved


def test_orchestrator_pipeline() -> None:
    engine = InformationPhysicsEngine()
    
    importance = np.array([0.8, 0.7])
    connectivity = np.array([0.5, 0.4])
    distances = np.array([[0.0, 1.5], [1.5, 0.0]])
    coordinates = np.array([[0.1, 0.1, 0.3, 0.3], [0.7, 0.7, 0.9, 0.9]])
    entropy = np.array([0.8, 0.6])
    relevance = np.array([0.9, 0.7])
    
    report = engine.analyze(
        importance=importance,
        connectivity=connectivity,
        distances=distances,
        coordinates=coordinates,
        entropy_scores=entropy,
        relevance_scores=relevance,
        importance_t1=np.array([0.85, 0.65]),
    )
    
    assert report.energy is not None
    assert report.gravity is not None
    assert report.potential is not None
    assert report.field is not None
    assert report.flow is not None
    assert report.thermodynamics is not None
    assert report.conservation is not None
    assert report.metrics is not None
    
    d = report.to_dict()
    assert "energy" in d
    assert "gravity" in d
    assert "potential" in d
    assert "field" in d
    assert "flow" in d
    assert "thermodynamics" in d
    assert "conservation" in d
    assert "metrics" in d
    assert "metadata" in d
