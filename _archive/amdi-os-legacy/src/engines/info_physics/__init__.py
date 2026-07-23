"""
AMDI-OS Information Physics Engine
===================================

Treats documents as physical systems with:
- Information Energy      (per-element importance × relevance)
- Information Gravity     (importance / distance² attraction)
- Information Potential   (positional importance × connectivity)
- Information Fields      (continuous scalar field over the document)
- Information Flow        (rate of change / kinetics)
- Conservation Laws       (input = output + compressed + discarded)
- Thermodynamics          (entropy, temperature, free energy)

Mathematical Foundation:
    D = (I, E, T, S)
    I_E = i_H × i_R                       (Energy)
    G_i = (I_i × C_i) / d_i²               (Gravity)
    PE_i = Importance_i × Position_i       (Potential)
    Φ(x,y) = Σ W_i / d_i²                  (Field)
    dI/dt                                   (Flow)
    I_in = I_out + I_compressed + I_discarded   (Conservation)
    H(X) = -Σ p(x) log p(x)               (Entropy)

Author : AMDI-OS Development Team
Version: 1.0.0
License: Proprietary
"""

from .info_physics_engine import (
    InformationPhysicsEngine,
    PhysicsReport,
)
from .energy import InformationEnergy, EnergyCalculator
from .gravity import InformationGravity, GravityCalculator, GravityField
from .potential import InformationPotential, PotentialCalculator
from .fields import InformationField, FieldCalculator, FieldMap
from .flow import InformationFlow, FlowCalculator, FlowVector
from .conservation import (
    ConservationLaw,
    ConservationChecker,
    ConservationReport,
)
from .thermodynamics import (
    Thermodynamics,
    ThermodynamicState,
    EntropyCalculator,
)
from .metrics import (
    PhysicsMetrics,
    PhysicsMetricsCalculator,
)
from .exceptions import (
    PhysicsEngineError,
    InvalidDocumentError,
    ConservationViolationError,
)

__all__ = [
    "InformationPhysicsEngine",
    "PhysicsReport",
    "InformationEnergy",
    "EnergyCalculator",
    "InformationGravity",
    "GravityCalculator",
    "GravityField",
    "InformationPotential",
    "PotentialCalculator",
    "InformationField",
    "FieldCalculator",
    "FieldMap",
    "InformationFlow",
    "FlowCalculator",
    "FlowVector",
    "ConservationLaw",
    "ConservationChecker",
    "ConservationReport",
    "Thermodynamics",
    "ThermodynamicState",
    "EntropyCalculator",
    "PhysicsMetrics",
    "PhysicsMetricsCalculator",
    "PhysicsEngineError",
    "InvalidDocumentError",
    "ConservationViolationError",
]

__version__ = "1.0.0"