'''
AEGIS-MIOS — Harmonic Analysis
===============================
Frequency domain transform and synthesis algorithms:
- Fourier Series square wave reconstruction
- Discrete Fourier Transform (DFT) from scratch
- Short-Time Fourier Transform (STFT) with custom windowing
- Discrete Wavelet Transform (1D Haar DWT)
'''

from __future__ import annotations

import numpy as np


def fourier_series_square(t: np.ndarray, n_harmonics: int, frequency: float = 1.0) -> np.ndarray:
    '''
    Reconstruct a square wave of specified frequency using Fourier Series.
    x(t) = (4/π) * Σ_{k=1,3,5...}^{2N-1} (1/k) * sin(2π k f t)
    '''
    omega = 2.0 * np.pi * frequency
    signal = np.zeros_like(t)
    for i in range(n_harmonics):
        k = 2 * i + 1
        signal += (1.0 / k) * np.sin(k * omega * t)
    return (4.0 / np.pi) * signal


def dft(x: np.ndarray) -> np.ndarray:
    '''
    Compute Discrete Fourier Transform (DFT) from scratch (O(N^2) complexity).
    X_k = Σ_{n=0}^{N-1} x_n * exp(-i * 2π * k * n / N)
    '''
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    e = np.exp(-2j * np.pi * k * n / N)
    return e @ x


def stft(x: np.ndarray, window_size: int = 64, hop_size: int = 32) -> np.ndarray:
    '''
    Compute Short-Time Fourier Transform (STFT) using sliding window and DFT.
    Uses a Hann window by default.
    Returns:
    - spectrogram: complex array of shape (n_frequencies, n_frames)
    '''
    n_samples = len(x)
    n_frames = (n_samples - window_size) // hop_size + 1
    if n_frames <= 0:
        return np.zeros((window_size // 2 + 1, 0), dtype=complex)

    # Hann window
    window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(window_size) / (window_size - 1)))

    spectrogram = []
    for f in range(n_frames):
        start = f * hop_size
        end = start + window_size
        segment = x[start:end] * window
        # Compute DFT and take the positive frequencies
        spectrum = dft(segment)
        spectrogram.append(spectrum[:window_size // 2 + 1])

    return np.column_stack(spectrogram)


def haar_dwt(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    '''
    Compute 1-level Discrete Wavelet Transform (DWT) using Haar Wavelet.
    Approximation coefficients (scaling): a_i = (x_{2i} + x_{2i+1}) / √2
    Detail coefficients (wavelet):   d_i = (x_{2i} - x_{2i+1}) / √2
    '''
    # Pad to even length if needed
    if len(x) % 2 != 0:
        x = np.append(x, x[-1])

    n = len(x) // 2
    approximation = np.zeros(n)
    detail = np.zeros(n)

    for i in range(n):
        approximation[i] = (x[2 * i] + x[2 * i + 1]) / np.sqrt(2.0)
        detail[i] = (x[2 * i] - x[2 * i + 1]) / np.sqrt(2.0)

    return approximation, detail
