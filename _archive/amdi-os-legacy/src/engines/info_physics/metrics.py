"""
Physics Metrics Aggregation
===========================

Aggregated metrics for the Information Physics Engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from .conservation import ConservationReport
from .energy import EnergyField
from .fields import InformationField
from .flow import InformationFlow
from .gravity import GravityField
from .potential import PotentialField
from .thermodynamics import ThermodynamicState


@dataclass
class PhysicsMetrics:
    """
    Aggregated information-physics metrics.

    Attributes
    ----------
    total_energy : float
    mean_energy : float
    max_gravity : float
    total_gravity : float
    total_potential : float
    mean_potential : float
    field_max : float
    field_mean : float
    field_energy : float
    flow_total_inflow : float
    flow_total_outflow : float
    thermodynamic_entropy : float
    normalized_entropy : float
    free_energy : float
    conservation_error : float
    is_conserved : bool
    discarded_fraction : float
    """

    total_energy: float
    mean_energy: float
    max_gravity: float
    total_gravity: float
    total_potential: float
    mean_potential: float
    field_max: float
    field_mean: float
    field_energy: float
    flow_total_inflow: float
    flow_total_outflow: float
    thermodynamic_entropy: float
    normalized_entropy: float
    free_energy: float
    conservation_error: float
    is_conserved: bool
    discarded_fraction: float

    def to_dict(self) -> dict:
        return {
            "total_energy": round(self.total_energy, 6),
            "mean_energy": round(self.mean_energy, 6),
            "max_gravity": round(self.max_gravity, 6),
            "total_gravity": round(self.total_gravity, 6),
            "total_potential": round(self.total_potential, 6),
            "mean_potential": round(self.mean_potential, 6),
            "field_max": round(self.field_max, 6),
            "field_mean": round(self.field_mean, 6),
            "field_energy": round(self.field_energy, 6),
            "flow_total_inflow": round(self.flow_total_inflow, 6),
            "flow_total_outflow": round(self.flow_total_outflow, 6),
            "thermodynamic_entropy": round(self.thermodynamic_entropy, 6),
            "normalized_entropy": round(self.normalized_entropy, 6),
            "free_energy": round(self.free_energy, 6),
            "conservation_error": round(self.conservation_error, 6),
            "is_conserved": self.is_conserved,
            "discarded_fraction": round(self.discarded_fraction, 6),
        }

    def to_feature_vector(self) -> list:
        return [
            self.total_energy,
            self.mean_energy,
            self.max_gravity,
            self.total_gravity,
            self.total_potential,
            self.mean_potential,
            self.field_max,
            self.field_mean,
            self.field_energy,
            self.flow_total_inflow,
            self.flow_total_outflow,
            self.thermodynamic_entropy,
            self.normalized_entropy,
            self.free_energy,
            self.conservation_error,
            1.0 if self.is_conserved else 0.0,
            self.discarded_fraction,
        ]


class PhysicsMetricsCalculator:
    """
    Aggregates all physics signals into a single metrics object.
    """

    @staticmethod
    def aggregate(
        energy: Optional[EnergyField] = None,
        gravity: Optional[GravityField] = None,
        potential: Optional[PotentialField] = None,
        field: Optional[InformationField] = None,
        flow: Optional[InformationFlow] = None,
        thermo: Optional[ThermodynamicState] = None,
        conservation: Optional[ConservationReport] = None,
    ) -> PhysicsMetrics:
        return PhysicsMetrics(
            total_energy=energy.total_energy if energy else 0.0,
            mean_energy=energy.mean_energy if energy else 0.0,
            max_gravity=float(gravity.gravity.max()) if gravity is not None and gravity.gravity.size > 0 else 0.0,
            total_gravity=gravity.total_gravity if gravity else 0.0,
            total_potential=potential.total_potential if potential else 0.0,
            mean_potential=potential.mean_potential if potential else 0.0,
            field_max=field.max_density_location[1] if field else 0,  # placeholder; replaced below
            field_mean=field.mean_field_strength if field else 0.0,
            field_energy=field.total_field_energy if field else 0.0,
            flow_total_inflow=flow.total_inflow if flow else 0.0,
            flow_total_outflow=flow.total_outflow if flow else 0.0,
            thermodynamic_entropy=thermo.entropy if thermo else 0.0,
            normalized_entropy=thermo.normalized_entropy if thermo else 0.0,
            free_energy=thermo.free_energy if thermo else 0.0,
            conservation_error=conservation.conservation_error if conservation else 0.0,
            is_conserved=conservation.is_conserved if conservation else True,
            discarded_fraction=conservation.discarded_fraction if conservation else 0.0,
        )