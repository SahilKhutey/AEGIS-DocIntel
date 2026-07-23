"""
Information Physics Engine — Main Orchestrator
==============================================

End-to-end pipeline:

    Document Elements
         ↓
    ┌──────────────┬──────────────┬──────────────┬─────────────┬─────────────┐
    │ Energy       │ Gravity      │ Potential    │ Fields      │ Flow        │
    └──────────────┴──────────────┴──────────────┴─────────────┴─────────────┘
         ↓
    Conservation + Thermodynamics
         ↓
    PhysicsReport → Export Object

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .conservation import (
    ConservationChecker,
    ConservationLaw,
    ConservationReport,
)
from .energy import EnergyCalculator, EnergyField
from .exceptions import (
    FieldComputationError,
    InvalidDocumentError,
    PhysicsEngineError,
)
from .fields import FieldCalculator, FieldMap, InformationField
from .flow import FlowCalculator, FlowVector, InformationFlow
from .gravity import GravityCalculator, GravityField
from .metrics import PhysicsMetrics, PhysicsMetricsCalculator
from .potential import PotentialCalculator, PotentialField
from .thermodynamics import Thermodynamics, ThermodynamicState


@dataclass
class PhysicsReport:
    """
    Complete information-physics report.

    Attributes
    ----------
    energy : EnergyField
    gravity : GravityField
    potential : PotentialField
    field : InformationField
    flow : Optional[InformationFlow]
    thermodynamics : ThermodynamicState
    conservation : ConservationReport
    metrics : PhysicsMetrics
    metadata : Dict[str, Any]
    """

    energy: Optional[EnergyField] = None
    gravity: Optional[GravityField] = None
    potential: Optional[PotentialField] = None
    field: Optional[InformationField] = None
    flow: Optional[InformationFlow] = None
    thermodynamics: Optional[ThermodynamicState] = None
    conservation: Optional[ConservationReport] = None
    metrics: Optional[PhysicsMetrics] = None
    metadata: Dict[str, Any] = dc_field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"metadata": self.metadata}
        if self.energy is not None:
            d["energy"] = {
                "total": round(self.energy.total_energy, 6),
                "mean": round(self.energy.mean_energy, 6),
                "max_element": self.energy.max_energy_element,
            }
        if self.gravity is not None:
            d["gravity"] = {
                "total": round(self.gravity.total_gravity, 6),
                "mean": round(self.gravity.mean_gravity, 6),
                "strongest_attractor": self.gravity.strongest_attractor,
            }
        if self.potential is not None:
            d["potential"] = {
                "total": round(self.potential.total_potential, 6),
                "mean": round(self.potential.mean_potential, 6),
                "max_element": self.potential.max_element,
            }
        if self.field is not None:
            d["field"] = {
                "total_energy": round(self.field.total_field_energy, 6),
                "mean_strength": round(self.field.mean_field_strength, 6),
                "max_density_location": list(self.field.max_density_location),
            }
        if self.flow is not None:
            d["flow"] = {
                "total_inflow": round(self.flow.total_inflow, 6),
                "total_outflow": round(self.flow.total_outflow, 6),
                "most_dynamic_element": self.flow.most_dynamic_element,
            }
        if self.thermodynamics is not None:
            d["thermodynamics"] = self.thermodynamics.to_dict()
        if self.conservation is not None:
            d["conservation"] = self.conservation.to_dict()
        if self.metrics is not None:
            d["metrics"] = self.metrics.to_dict()
        return d


class InformationPhysicsEngine:
    """
    Main orchestrator for the Information Physics Engine.
    Executes calculations for Information Energy, Gravity, Potential, Fields,
    Flow, Conservation, and Thermodynamics.
    """

    def __init__(self, conservation_threshold: float = 0.05, epsilon: float = 1e-6) -> None:
        self.conservation_threshold = conservation_threshold
        self.epsilon = epsilon
        self.energy_calc = EnergyCalculator()
        self.gravity_calc = GravityCalculator(epsilon=epsilon)
        self.potential_calc = PotentialCalculator()
        self.field_calc = FieldCalculator(epsilon=epsilon)
        self.flow_calc = FlowCalculator()
        self.conservation_law = ConservationLaw(max_discarded_fraction=conservation_threshold)
        self.thermodynamics = Thermodynamics()

    def analyze(
        self,
        importance: np.ndarray,
        connectivity: np.ndarray,
        distances: np.ndarray,
        coordinates: np.ndarray,
        entropy_scores: np.ndarray,
        relevance_scores: np.ndarray,
        importance_t1: Optional[np.ndarray] = None,
        adjacency: Optional[np.ndarray] = None,
        input_info: float = 100.0,
        output_info: float = 40.0,
        compressed_info: float = 56.0,
        discarded_info: float = 4.0,
        grid_size: Tuple[int, int] = (50, 50),
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> PhysicsReport:
        """
        Runs the end-to-end document physics analysis pipeline.
        """
        # Calculate components
        energy_field = self.energy_calc.compute(entropy_scores, relevance_scores)
        
        gravity_field = self.gravity_calc.compute(importance, connectivity, distances)
        
        potential_field = self.potential_calc.compute(importance, coordinates=coordinates)
        
        # Prepare positions for field (requires shape (n, 2))
        pos = coordinates
        if pos.ndim == 2 and pos.shape[1] == 4:
            # Bounding box centers: (x_center, y_center)
            x_center = (pos[:, 0] + pos[:, 2]) / 2.0
            y_center = (pos[:, 1] + pos[:, 3]) / 2.0
            pos = np.column_stack([x_center, y_center])
        elif pos.ndim == 2 and pos.shape[1] == 2:
            pass
        else:
            raise InvalidDocumentError("coordinates must be of shape (n, 2) or (n, 4).")
            
        field_res = self.field_calc.compute(pos, importance, grid_size=grid_size, bbox=bbox)
        
        flow_res = None
        if importance_t1 is not None:
            flow_res = self.flow_calc.compute_flow(importance, importance_t1, adjacency)
            
        thermo_state = self.thermodynamics.compute_state(importance, entropy=entropy_scores)
        
        conservation_rep = self.conservation_law.check(
            input_info=input_info,
            output_info=output_info,
            compressed_info=compressed_info,
            discarded_info=discarded_info,
        )
        
        metrics = PhysicsMetricsCalculator.aggregate(
            energy=energy_field,
            gravity=gravity_field,
            potential=potential_field,
            field=field_res,
            flow=flow_res,
            thermo=thermo_state,
            conservation=conservation_rep,
        )
        
        if field_res is not None:
            metrics.field_max = field_res.field_map.max_value

        return PhysicsReport(
            energy=energy_field,
            gravity=gravity_field,
            potential=potential_field,
            field=field_res,
            flow=flow_res,
            thermodynamics=thermo_state,
            conservation=conservation_rep,
            metrics=metrics,
        )
