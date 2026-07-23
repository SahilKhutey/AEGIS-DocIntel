'''
AEGIS-MIOS — Spectral Analysis
================================
A x = λx  — Eigenvalue decomposition
F(ω)     — Fourier transform
W(a, b)  — Wavelet transform

For: detecting repeated layouts, periodic templates, sections
'''

from __future__ import annotations

import numpy as np
from scipy.fft import fft, fftfreq, ifft, dct
from scipy.signal import stft, welch, find_peaks
from scipy.linalg import eigh


# ============================================================
# §1. EIGENVALUE DECOMPOSITION: A x = λ x
# ============================================================

def spectral_decomposition(adjacency: np.ndarray, k: int | None = None) -> dict:
    '''
    A x = λ x

    Compute eigenvalues and eigenvectors of adjacency matrix.
    Top-k eigenvalues reveal dominant structures.

    For document graphs:
    - Largest eigenvalue = connected component density
    - Eigenvalue gaps = community structure
    - Spectral gap = graph expansion
    '''
    # Symmetrize for real eigenvalues
    A = (adjacency + adjacency.T) / 2
    if k is None:
        k = min(A.shape[0] - 1, 20)
    k = min(k, A.shape[0] - 1)
    if k <= 0:
        return {'eigenvalues': np.array([]), 'eigenvectors': np.array([]).reshape(0, 0)}

    try:
        eigvals, eigvecs = eigh(A, subset_by_index=[A.shape[0] - k, A.shape[0] - 1])
        # Sort descending
        idx = np.argsort(eigvals)[::-1]
        eigvals = eigvals[idx]
        eigvecs = eigvecs[:, idx]
    except Exception:
        eigvals, eigvecs = np.linalg.eig(A)
        idx = np.argsort(np.real(eigvals))[::-1][:k]
        eigvals = np.real(eigvals[idx])
        eigvecs = np.real(eigvecs[:, idx])

    spectral_gap = eigvals[0] - eigvals[1] if len(eigvals) > 1 else 0
    return {
        'eigenvalues': eigvals,
        'eigenvectors': eigvecs,
        'spectral_gap': float(spectral_gap),
        'largest_eigenvalue': float(eigvals[0]),
        'is_expander': spectral_gap > 0.1 * abs(eigvals[0]) if len(eigvals) > 1 else False,
    }


def spectral_embedding(adjacency: np.ndarray, dim: int = 2) -> np.ndarray:
    '''
    Spectral embedding: project nodes to dim-D space using eigenvectors.

    Useful for: 2D visualization of document structure.
    '''
    spec = spectral_decomposition(adjacency, k=dim + 1)
    eigvals = spec['eigenvalues']
    eigvecs = spec['eigenvectors']
    # Skip the trivial first eigenvector (constant)
    if len(eigvals) >= dim + 1:
        # Scale by sqrt(eigenvalue)
        scaled = eigvecs[:, 1:dim + 1] * np.sqrt(np.abs(eigvals[1:dim + 1]))
        return scaled
    return np.zeros((adjacency.shape[0], dim))


def spectral_clustering(adjacency: np.ndarray, n_clusters: int = 3) -> np.ndarray:
    '''
    Spectral clustering using Ng-Jordan-Weiss algorithm.

    1. Compute normalized Laplacian
    2. Take top-k eigenvectors
    3. Cluster with k-means
    '''
    from sklearn.cluster import KMeans
    n = adjacency.shape[0]
    degree = np.array(adjacency.sum(axis=1)).flatten()
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(degree, 1e-9)))
    L = np.eye(n) - D_inv_sqrt @ adjacency @ D_inv_sqrt
    spec = spectral_decomposition(L, k=n_clusters)
    eigvecs = spec['eigenvectors'][:, :n_clusters]
    # Normalize rows
    norms = np.linalg.norm(eigvecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    eigvecs = eigvecs / norms
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=0)
    return kmeans.fit_predict(eigvecs)


# ============================================================
# §2. FOURIER TRANSFORM: F(ω)
# ============================================================

def fourier_transform(signal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    '''
    F(ω) = ∫ f(t) e^(-iωt) dt

    Returns (frequencies, complex spectrum).
    '''
    n = len(signal)
    freqs = fftfreq(n)
    spectrum = fft(signal)
    return freqs, spectrum


def power_spectrum(signal: np.ndarray) -> np.ndarray:
    '''P(ω) = |F(ω)|²'''
    _, spectrum = fourier_transform(signal)
    return np.abs(spectrum) ** 2


def fourier_periodicity(signal: np.ndarray, top_k_ratio: float = 0.1) -> float:
    '''
    Detect periodicity in signal.

    Returns ratio of power in top-k frequencies.
    1.0 = perfectly periodic, 0.0 = random.
    '''
    if len(signal) < 4:
        return 0.0
    power = power_spectrum(signal)
    power[0] = 0  # Remove DC
    total = power.sum()
    if total == 0:
        return 0.0
    top_k = max(1, int(len(power) * top_k_ratio))
    top_indices = np.argsort(power)[-top_k:]
    return float(power[top_indices].sum() / total)


def dominant_frequency(signal: np.ndarray, sample_rate: float = 1.0) -> float:
    '''Return the dominant frequency in the signal.'''
    freqs, spectrum = fourier_transform(signal)
    power = np.abs(spectrum) ** 2
    power[0] = 0  # Remove DC
    idx = np.argmax(power)
    return float(abs(freqs[idx]) * sample_rate)


def detect_periodic_structures(signal: np.ndarray) -> list[dict]:
    '''
    Find all significant periodic components.

    Returns list of {frequency, period, power, amplitude}.
    '''
    if len(signal) < 8:
        return []
    power = power_spectrum(signal)
    power[0] = 0
    freqs = fftfreq(len(signal))
    peaks, _ = find_peaks(power, height=power.mean() + power.std())
    structures = []
    for p in peaks:
        if power[p] > 0 and abs(freqs[p]) > 0:
            structures.append({
                'frequency': float(abs(freqs[p])),
                'period_samples': float(1.0 / max(1e-9, abs(freqs[p]))),
                'power': float(power[p]),
                'amplitude': float(np.sqrt(power[p])),
            })
    return sorted(structures, key=lambda x: x['power'], reverse=True)


def inverse_fourier(spectrum: np.ndarray) -> np.ndarray:
    '''f(t) = F^(-1)(F(ω))'''
    return np.real(ifft(spectrum))


def discrete_cosine_transform(signal: np.ndarray) -> np.ndarray:
    '''DCT-II. Used for: compression, spectral analysis.'''
    return dct(signal, type=2, norm='ortho')


def short_time_fourier(signal: np.ndarray, window_size: int = 64) -> dict:
    '''
    STFT for time-frequency analysis.

    Returns dict with 'frequencies', 'times', 'power'.
    '''
    f, t, Zxx = stft(signal, nperseg=window_size)
    return {'frequencies': f, 'times': t, 'power': np.abs(Zxx) ** 2}


def welch_psd(signal: np.ndarray, fs: float = 1.0) -> dict:
    '''Power spectral density via Welch's method.'''
    f, psd = welch(signal, fs=fs)
    return {'frequencies': f, 'psd': psd}


# ============================================================
# §3. WAVELET TRANSFORM: W(a, b)
# ============================================================

def wavelet_transform(signal: np.ndarray, scales: np.ndarray | None = None) -> np.ndarray:
    '''
    W(a, b) = (1/√a) ∫ f(t) ψ*((t-b)/a) dt

    Continuous wavelet transform using Morlet wavelet.
    '''
    from scipy.signal import morlet, cwt
    if scales is None:
        scales = np.arange(1, min(64, len(signal) // 2))
    return cwt(signal, morlet, scales)


def wavelet_energy_by_scale(signal: np.ndarray, scales: np.ndarray | None = None) -> dict:
    '''
    E(a) = Σ_b |W(a, b)|²

    Energy at each wavelet scale.
    '''
    coefs = wavelet_transform(signal, scales)
    if scales is None:
        scales = np.arange(1, coefs.shape[0] + 1)
    return {float(s): float(np.sum(np.abs(coefs[i]) ** 2)) for i, s in enumerate(scales)}


def dominant_scale(signal: np.ndarray) -> float:
    '''Find the wavelet scale with maximum energy.'''
    energies = wavelet_energy_by_scale(signal)
    return max(energies, key=energies.get)


def multi_resolution_decomposition(signal: np.ndarray) -> dict:
    '''
    Multi-scale feature extraction.

    Coarse: large structures (low frequency)
    Fine: small structures (high frequency)
    '''
    energies = wavelet_energy_by_scale(signal)
    scales = sorted(energies.keys())
    if not scales:
        return {'coarse_energy': 0, 'fine_energy': 0, 'ratio': 0}
    coarse_scales = [s for s in scales if s > np.median(scales)]
    fine_scales = [s for s in scales if s <= np.median(scales)]
    coarse = sum(energies[s] for s in coarse_scales) / max(1, len(coarse_scales))
    fine = sum(energies[s] for s in fine_scales) / max(1, len(fine_scales))
    return {
        'coarse_energy': coarse,
        'fine_energy': fine,
        'ratio': coarse / max(1e-9, fine),
        'dominant_scale': dominant_scale(signal),
    }
