'''
AEGIS-MIOS — Information Physics
=================================
Complete implementation of all information physics concepts.

Concepts:
- D = (I, E, T, S) — Document as physical system
- IE_i = H_i × R_i — Information Energy
- G_i = (I × C) / d² — Information Gravity
- Φ(x) = Σ W_i / d_i² — Information Field
- PE = Importance × Position — Potential Energy
- IK = dI/dt — Information Kinetics
- Conservation: I_in = I_out + I_compressed + I_discarded
'''

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.ndimage import gaussian_filter


# ============================================================
# §1. DOCUMENT AS PHYSICAL SYSTEM: D = (I, E, T, S)
# ============================================================

@dataclass
class PhysicalDocument:
    '''
    D = (I, E, T, S) representation.

    I: Information content (bits)
    E: Energy (information energy)
    T: Time (versioning, evolution)
    S: Space (geometric coordinates)
    '''
    doc_id: str
    information: float = 0.0       # I - total bits
    energy: float = 0.0            # E - total energy
    time: float = 0.0              # T - creation/modification time
    space: np.ndarray | None = None  # S - spatial extent

    def to_tuple(self) -> tuple:
        return (self.information, self.energy, self.time, self.space)


# ============================================================
# §2. INFORMATION ENERGY: IE_i = H_i × R_i
# ============================================================

def information_energy(entropy: float, relevance: float) -> float:
    '''
    IE_i = H_i × R_i

    Information energy of element i.
    High energy → conclusion, warning, critical value
    Low energy → page number, header, footer
    '''
    if entropy < 0 or relevance < 0:
        return 0.0
    return entropy * relevance


def total_energy(entropies: np.ndarray, relevances: np.ndarray) -> float:
    '''Total information energy: E = Σ IE_i.'''
    return float(np.sum(entropies * relevances))


# ============================================================
# §3. INFORMATION GRAVITY: G_i = (I_i × C_i) / d_i²
# ============================================================

def information_gravity(
    importance: float,
    connectivity: int,
    distance: float,
    gravitational_constant: float = 1.0,
) -> float:
    '''
    G_i = G × (Importance_i × Connectivity_i) / d_i²

    Important nodes attract other information.
    High gravity: main tables, conclusions, abstracts
    '''
    if distance <= 0:
        return float('inf')
    return gravitational_constant * (importance * connectivity) / (distance ** 2)


def gravity_field(
    positions: np.ndarray,
    importances: np.ndarray,
    connectivities: np.ndarray,
    query_position: np.ndarray,
) -> float:
    '''Total gravitational pull at query position.'''
    if len(positions) == 0:
        return 0.0
    diffs = positions - query_position
    distances_sq = np.sum(diffs ** 2, axis=1) + 1e-9
    return float(np.sum(importances * connectivities / distances_sq))


def gravity_trajectory(
    start: np.ndarray,
    positions: np.ndarray,
    importances: np.ndarray,
    connectivities: np.ndarray,
    n_steps: int = 100,
    learning_rate: float = 0.01,
    mass: float = 1.0,
) -> np.ndarray:
    '''
    Simulate trajectory of a 'particle' in the information gravity field.
    Returns the path of the particle as it gets attracted to high-gravity nodes.
    '''
    path = np.zeros((n_steps, len(start)))
    position = start.copy()
    velocity = np.zeros_like(start)
    path[0] = position
    for t in range(1, n_steps):
        # Compute force from all nodes
        diffs = positions - position
        distances = np.linalg.norm(diffs, axis=1) + 1e-3
        force_vectors = diffs / (distances ** 3).reshape(-1, 1)
        force = np.sum(importances.reshape(-1, 1) * connectivities.reshape(-1, 1) * force_vectors, axis=0)
        # Newton's second law: F = ma → a = F/m
        acceleration = force / mass
        velocity = velocity * 0.95 + acceleration * learning_rate
        position = position + velocity
        path[t] = position
    return path


# ============================================================
# §4. INFORMATION FIELD: Φ(x,y) = Σ W_i / d_i²
# ============================================================

def information_field(
    query_position: np.ndarray,
    source_positions: np.ndarray,
    source_weights: np.ndarray,
    epsilon: float = 1e-9,
) -> float:
    '''
    Φ(x, y) = Σ W_i / d_i²

    Scalar field at query position.
    Used for attention maps, priority maps, retrieval maps.
    '''
    if len(source_positions) == 0:
        return 0.0
    diffs = source_positions - query_position
    distances_sq = np.sum(diffs ** 2, axis=1) + epsilon
    return float(np.sum(source_weights / distances_sq))


def field_heatmap(
    source_positions: np.ndarray,
    source_weights: np.ndarray,
    grid_size: int = 32,
    x_range: tuple = (0, 1),
    y_range: tuple = (0, 1),
    sigma: float = 1.0,
) -> np.ndarray:
    '''
    Generate 2D attention heatmap from information field.

    Useful for:
    - Attention visualization
    - Priority heatmaps
    - Retrieval focus maps
    '''
    heatmap = np.zeros((grid_size, grid_size))
    x_coords = np.linspace(x_range[0], x_range[1], grid_size)
    y_coords = np.linspace(y_range[0], y_range[1], grid_size)
    for i, x in enumerate(x_coords):
        for j, y in enumerate(y_coords):
            source_pos_2d = source_positions[:, :2] if source_positions.shape[1] >= 2 else np.column_stack([source_positions, np.zeros(len(source_positions))])
            heatmap[i, j] = information_field(
                np.array([x, y]),
                source_pos_2d,
                source_weights,
            )
    # Apply Gaussian smoothing for visualization
    heatmap = gaussian_filter(heatmap, sigma=sigma)
    # Normalize
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()
    return heatmap


def field_gradient(
    query_position: np.ndarray,
    source_positions: np.ndarray,
    source_weights: np.ndarray,
    epsilon: float = 1e-9,
    h: float = 1e-5,
) -> np.ndarray:
    '''Gradient of information field ∇Φ(x).'''
    grad = np.zeros_like(query_position)
    for i in range(len(query_position)):
        x_plus = query_position.copy()
        x_plus[i] += h
        x_minus = query_position.copy()
        x_minus[i] -= h
        phi_plus = information_field(x_plus, source_positions, source_weights, epsilon)
        phi_minus = information_field(x_minus, source_positions, source_weights, epsilon)
        grad[i] = (phi_plus - phi_minus) / (2 * h)
    return grad


# ============================================================
# §5. INFORMATION POTENTIAL ENERGY: PE = Importance × Position
# ============================================================

def potential_energy(importance: float, position_priority: float) -> float:
    '''
    PE = Importance × Position

    High PE → immediate retrieval
    '''
    return importance * position_priority


def potential_energy_field(
    importances: np.ndarray,
    positions: np.ndarray,
) -> np.ndarray:
    '''PE field over all elements.'''
    # Position priority = distance from top of page (lower y = higher priority)
    if len(positions) == 0:
        return np.array([])
    y_coords = positions[:, 1] if positions.ndim > 1 else np.zeros(len(positions))
    max_y = max(y_coords.max(), 1e-9)
    position_priorities = 1.0 - (y_coords / max_y)
    return importances * position_priorities


# ============================================================
# §6. INFORMATION KINETICS: IK = dI/dt
# ============================================================

def information_kinetic_rate(
    time_series: list[tuple[float, float]],
) -> float:
    '''
    IK = dI/dt — rate of information change.

    Useful for: versioned PDFs, document evolution tracking.
    '''
    if len(time_series) < 2:
        return 0.0
    times = np.array([t for t, _ in time_series])
    values = np.array([v for _, v in time_series])
    # Linear regression slope
    if np.std(times) == 0:
        return 0.0
    slope = np.polyfit(times, values, 1)[0]
    return float(slope)


def kinetic_energy(v: float, m: float = 1.0) -> float:
    '''KE = (1/2)mv².'''
    return 0.5 * m * v ** 2


def total_mechanical_energy(
    kinetic: float, potential: float,
) -> float:
    '''E = KE + PE.'''
    return kinetic + potential


# ============================================================
# §7. CONSERVATION LAW: I_in = I_out + I_comp + I_disc
# ============================================================

def verify_conservation(
    i_input: float,
    i_output: float,
    i_compressed: float,
    i_discarded: float,
    discard_threshold: float = 0.05,
    tolerance: float = 1e-6,
) -> dict:
    '''
    I_in = I_out + I_compressed + I_discarded

    Returns conservation status and discard ratio.
    Goal: I_discarded / I_in < 5%
    '''
    total_out = i_output + i_compressed + i_discarded
    delta = abs(i_input - total_out)
    is_conserved = delta < tolerance
    discard_ratio = i_discarded / max(1e-9, i_input)
    return {
        'is_conserved': is_conserved,
        'delta': delta,
        'discard_ratio': discard_ratio,
        'discard_pct': discard_ratio * 100,
        'within_threshold': discard_ratio < discard_threshold,
        'compression_pct': (i_compressed / max(1e-9, i_input)) * 100,
        'retention_pct': (i_output / max(1e-9, i_input)) * 100,
    }
