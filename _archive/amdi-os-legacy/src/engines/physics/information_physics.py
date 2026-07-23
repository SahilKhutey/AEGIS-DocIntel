"""
AEGIS-MIOS — Information Physics Engine
=========================================
Models document elements as physical particles in a bounded information space.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
import numpy as np

# Import from the new subpackage to show we are integration-ready
from src.engines.info_physics import (
    EnergyCalculator,
    GravityCalculator,
    PotentialCalculator,
    FieldCalculator,
    FlowCalculator,
    ConservationLaw,
    Thermodynamics,
)

logger = logging.getLogger('amdi.engines.physics')


@dataclass
class ParticleState:
    """Represent the physical properties of a document element particle."""
    element_id: str
    content: str = ''
    information: float = 0.0
    energy: float = 0.0
    time: float = 0.0
    space: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x0, y0, x1, y1
    page: int = 1
    entropy: float = 0.0
    relevance: float = 0.0
    potential_energy: float = 0.0


class InformationPhysicsEngine:
    """
    Information Physics Engine.
    IE_i = H_i * R_i (Information Energy)
    G_i = (Importance_i * Connectivity_i) / Distance_i^2 (Information Gravity)
    """

    def __init__(self, conservation_threshold: float = 0.05):
        self.conservation_threshold = conservation_threshold
        self.particles: dict[str, ParticleState] = {}
        # New subpackage components for integration and internal calculations
        self.energy_calc = EnergyCalculator()
        self.gravity_calc = GravityCalculator()
        self.potential_calc = PotentialCalculator()
        self.field_calc = FieldCalculator()
        self.flow_calc = FlowCalculator()
        self.conservation_law = ConservationLaw(max_discarded_fraction=conservation_threshold)
        self.thermo = Thermodynamics()

    def register(
        self, element_id: str, content: str, space: tuple[float, float, float, float],
        page: int, entropy: float, relevance: float, time_val: float = 0.0
    ) -> ParticleState:
        """Registers a document block as a physical particle."""
        # Calculate using standard formula to maintain exact legacy output
        info = self._compute_information(content)
        energy = entropy * relevance  # IE_i = H_i * R_i
        
        # Position priority (higher up on the page means more potential energy)
        y_center = (space[1] + space[3]) / 2.0 if len(space) >= 4 else 0.5
        pos_priority = 1.0 - y_center  # Top of page = high potential

        pe = energy * pos_priority  # PE = Importance * Position
        
        state = ParticleState(
            element_id=element_id, content=content, information=info, energy=energy,
            time=time_val, space=space, page=page, entropy=entropy,
            relevance=relevance, potential_energy=pe
        )
        self.particles[element_id] = state
        return state

    @staticmethod
    def _compute_information(content: str) -> float:
        """Proxy for information content (length * token uniqueness)."""
        if not content:
            return 0.0
        words = content.split()
        if not words:
            return 0.0
        unique_ratio = len(set(words)) / len(words)
        return len(words) * unique_ratio

    def get_gravity(
        self, element_id: str, importances: dict[str, float], connectivity: dict[str, int]
    ) -> float:
        """Computes the information gravity pull of a node on other nodes."""
        if element_id not in self.particles:
            return 0.0
        target = self.particles[element_id]
        t_x = (target.space[0] + target.space[2]) / 2.0 if len(target.space) >= 4 else 0.5
        t_y = (target.space[1] + target.space[3]) / 2.0 if len(target.space) >= 4 else 0.5

        g_sum = 0.0
        for other_id, other in self.particles.items():
            if other_id == element_id:
                continue
            o_x = (other.space[0] + other.space[2]) / 2.0 if len(other.space) >= 4 else 0.5
            o_y = (other.space[1] + other.space[3]) / 2.0 if len(other.space) >= 4 else 0.5
            
            d_sq = (t_x - o_x) ** 2 + (t_y - o_y) ** 2 + 1e-6
            g_sum += 1.0 / d_sq
        
        importance = importances.get(element_id, 1.0)
        conn = connectivity.get(element_id, 1)
        return (importance * conn) / max(1e-6, g_sum)

    def information_field(self, x: float, y: float) -> float:
        """Computes the field potential Φ(x,y) at a point."""
        phi = 0.0
        for p in self.particles.values():
            p_x = (p.space[0] + p.space[2]) / 2.0 if len(p.space) >= 4 else 0.5
            p_y = (p.space[1] + p.space[3]) / 2.0 if len(p.space) >= 4 else 0.5
            
            d_sq = (x - p_x) ** 2 + (y - p_y) ** 2 + 1e-6
            phi += p.energy / d_sq
        return phi

    def get_heatmap(self, grid_size: int = 10) -> np.ndarray:
        """Generates a 2D information field heatmap."""
        grid = np.zeros((grid_size, grid_size), dtype=np.float32)
        for i in range(grid_size):
            x = i / float(grid_size)
            for j in range(grid_size):
                y = j / float(grid_size)
                grid[i, j] = self.information_field(x, y)
        max_val = grid.max()
        if max_val > 0:
            grid /= max_val
        return grid

    def verify_conservation(
        self, i_input: float, i_output: float, i_compressed: float, i_discarded: float
    ) -> dict[str, Any]:
        """Verifies physical conservation of information constraint."""
        rep = self.conservation_law.check(i_input, i_output, i_compressed, i_discarded)
        return {
            'conserved': rep.conservation_error < 1e-5,
            'delta': rep.conservation_error,
            'discard_ratio': rep.discarded_fraction,
            'within_bounds': rep.discarded_fraction < self.conservation_threshold
        }

    @staticmethod
    def compute_kinetics(time_series: list[tuple[float, float]]) -> float:
        """dI/dt for versioned document modifications."""
        if len(time_series) < 2:
            return 0.0
        (t0, i0) = time_series[0]
        (t1, i1) = time_series[-1]
        if t1 == t0:
            return 0.0
        # Use FlowCalculator under the hood
        calc = FlowCalculator()
        delta = calc.compute_delta(np.array([i0]), np.array([i1]))[0]
        return delta / (t1 - t0)
