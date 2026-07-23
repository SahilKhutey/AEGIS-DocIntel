'''
spectral_engine.py
==================
AEGIS-AMDI-OS · Spectral Analysis Engine

Provides FFT-based page-layout periodicity detection, IDF-weighted
Shannon-entropy scoring, layout eigenvalue decomposition, and multi-scale Wavelets.
Also implements end-to-end graph spectral analysis.
'''
from __future__ import annotations

import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

# Optional SciPy import — fall back to numpy.fft if not available
try:
    from scipy.fft import fft as _fft, fftfreq as _fftfreq  # type: ignore
    _SCIPY_AVAILABLE = True
except ImportError:
    from numpy.fft import fft as _fft  # type: ignore
    _SCIPY_AVAILABLE = False

    def _fftfreq(n: int, d: float = 1.0) -> np.ndarray:
        val = 1.0 / (n * d)
        results = np.empty(n, dtype=int)
        N = (n - 1) // 2 + 1
        p1 = np.arange(0, N, dtype=int)
        results[:N] = p1
        p2 = np.arange(-(n // 2), 0, dtype=int)
        results[N:] = p2
        return results * val

from src.engines.geometry.element import GeometricElement
from .adjacency import AdjacencyMatrix, AdjacencyType
from .eigen import EigenResult, EigenSolver
from .exceptions import InsufficientDataError, InvalidGraphError
from .fourier import FourierResult, GraphFourierTransform
from .graph_signals import GraphSignal
from .heat_kernel import HeatDiffusionResult, HeatKernel
from .laplacian import LaplacianBuilder, LaplacianMatrix, LaplacianType
from .pattern_detector import Pattern, PatternDetector, PatternResult
from .spectral_clustering import SpectralClusterResult, SpectralClusterer

log = logging.getLogger('amdi.engines.spectral')

_DENSITY_BINS: int = 64
_PERIODICITY_THRESHOLD: float = 0.55
_TOP_FREQ_COUNT: int = 3


@dataclass
class SpectralSignature:
    '''Signature of spectral patterns in a layout signal.'''
    page: int = 1
    dominant_freqs: List[int] = field(default_factory=list)
    power_spectrum: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    layout_periodicity: float = 0.0
    is_repetitive: bool = False
    
    # MIOS fields
    dominant_frequency: float = 0.0
    periodicity: float = 0.0
    eigenvalues: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))


@dataclass
class EntropyProfile:
    '''Entropy and priority information for a single document element.'''
    element_id: str
    entropy: float
    tfidf_score: float
    is_informative: bool
    priority: int


@dataclass
class SpectralReport:
    """
    Complete spectral analysis report.

    Attributes
    ----------
    adjacency : AdjacencyMatrix
    laplacian : LaplacianMatrix
    eigen : EigenResult
    clustering : SpectralClusterResult
    patterns : PatternResult
    fourier : Optional[FourierResult]
    heat : Optional[HeatDiffusionResult]
    metadata : Dict[str, Any]
    """

    adjacency: AdjacencyMatrix
    laplacian: LaplacianMatrix
    eigen: EigenResult
    clustering: SpectralClusterResult
    patterns: PatternResult
    fourier: Optional[FourierResult] = None
    heat: Optional[HeatDiffusionResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "adjacency": {
                "size": self.adjacency.size,
                "num_edges": self.adjacency.num_edges,
                "density": round(self.adjacency.density, 4),
                "is_weighted": self.adjacency.is_weighted,
            },
            "laplacian": {
                "type": self.laplacian.laplacian_type.value,
                "is_normalized": self.laplacian.is_normalized,
                "is_psd": self.laplacian.is_psd,
            },
            "eigen": {
                "num_eigenvalues": self.eigen.num_eigenvalues,
                "fiedler_value": round(self.eigen.fiedler_value, 6),
                "num_zero_eigenvalues": self.eigen.num_zero_eigenvalues,
                "spectral_radius": round(self.eigen.spectral_radius, 6),
                "eigengap": self.eigen.eigengap,
                "estimated_clusters": self.eigen.estimated_clusters,
                "eigenvalues_head": [round(float(x), 6) for x in self.eigen.eigenvalues[:10]],
            },
            "clustering": {
                "n_clusters": self.clustering.n_clusters,
                "largest_size": self.clustering.largest_cluster_size,
                "mean_size": round(self.clustering.mean_cluster_size, 4),
                "inertia": round(self.clustering.inertia, 6),
                "silhouette": round(self.clustering.silhouette, 4),
            },
            "patterns": {
                "num_patterns": self.patterns.num_patterns,
                "by_type": self.patterns.pattern_count_by_type,
            },
        }
        if self.fourier is not None:
            d["fourier"] = {
                "dominant_frequencies": self.fourier.dominant_frequencies,
                "energy_concentration": round(self.fourier.energy_concentration, 4),
            }
        if self.heat is not None:
            d["heat"] = {
                "heat_sources": self.heat.heat_sources,
                "max_heat_vertex": int(np.argmax(self.heat.diagonal)) if len(self.heat.diagonal) > 0 else -1,
            }
        d["metadata"] = self.metadata
        return d


class SpectralEngine:
    '''
    Spectral Engine.
    Performs FFT page layout analysis, Shannon entropy, Eigenvalue layout analysis,
    Wavelet decompositions, and graph spectral decomposition.
    '''

    def __init__(self, repetition_threshold: float = 0.55) -> None:
        self.repetition_threshold = repetition_threshold
        self._idf: dict[str, float] = {}
        self._corpus_size: int = 0
        log.debug(
            'SpectralEngine initialised (scipy=%s, bins=%d, threshold=%.2f)',
            _SCIPY_AVAILABLE,
            _DENSITY_BINS,
            repetition_threshold,
        )

    # ------------------------------------------------------------------
    # original AMDI methods
    # ------------------------------------------------------------------

    def analyze_page_layout(
        self, elements: List[GeometricElement], page: int
    ) -> SpectralSignature:
        '''Compute an FFT-based layout signature for a single page.'''
        page_els = [e for e in elements if getattr(e, 'page', None) == page]

        if not page_els:
            empty_ps = np.zeros(_DENSITY_BINS // 2 + 1, dtype=float)
            return SpectralSignature(
                page=page,
                dominant_freqs=[],
                power_spectrum=empty_ps,
                layout_periodicity=0.0,
                is_repetitive=False,
                dominant_frequency=0.0,
                periodicity=0.0,
                eigenvalues=np.array([], dtype=np.float32)
            )

        y_vals = np.array(
            [self._element_y_center(e) for e in page_els], dtype=float
        )
        y_vals = np.clip(y_vals, 0.0, 1.0)

        density, _ = np.histogram(y_vals, bins=_DENSITY_BINS, range=(0.0, 1.0))
        density = density.astype(float)
        density -= density.mean()

        spectrum = _fft(density)
        half = _DENSITY_BINS // 2 + 1
        ps = (np.abs(spectrum[:half]) ** 2)

        total_power = float(ps.sum())
        if total_power < 1e-12:
            periodicity = 0.0
            dom_freqs: List[int] = []
        else:
            ac_ps = ps[1:]
            top_idx = int(np.argmax(ac_ps))
            peak_power = float(ac_ps[top_idx])
            periodicity = float(np.clip(peak_power / total_power, 0.0, 1.0))

            sorted_idx = np.argsort(ac_ps)[::-1][:_TOP_FREQ_COUNT]
            dom_freqs = [int(i + 1) for i in sorted_idx]

        is_repetitive = periodicity > self.repetition_threshold

        return SpectralSignature(
            page=page,
            dominant_freqs=dom_freqs,
            power_spectrum=ps,
            layout_periodicity=periodicity,
            is_repetitive=is_repetitive,
            dominant_frequency=float(dom_freqs[0]) if dom_freqs else 0.0,
            periodicity=periodicity,
            eigenvalues=np.array([], dtype=np.float32)
        )

    def find_repetitive_pages(self, elements: List[GeometricElement]) -> List[int]:
        '''Return a sorted list of page numbers whose layout is repetitive.'''
        pages = sorted({getattr(e, 'page', None) for e in elements} - {None})
        repetitive: List[int] = []
        for pg in pages:
            sig = self.analyze_page_layout(elements, pg)
            if sig.is_repetitive:
                repetitive.append(pg)
        return repetitive

    def fit_idf(self, elements: List[GeometricElement]) -> None:
        '''Build an IDF dictionary from the full document corpus.'''
        N = len(elements)
        self._corpus_size = N
        df: Counter = Counter()

        for el in elements:
            tokens = set(self._tokenize(getattr(el, 'content', getattr(el, 'text', '')) or ''))
            df.update(tokens)

        self._idf = {
            token: math.log(1.0 + N / max(count, 1))
            for token, count in df.items()
        }

    def element_entropy(self, element: GeometricElement) -> float:
        '''Compute the IDF-weighted Shannon entropy of element's text.'''
        text = getattr(element, 'content', getattr(element, 'text', '')) or ''
        tokens = self._tokenize(text)

        if not tokens:
            return 0.0

        counts = Counter(tokens)
        total = len(tokens)
        shannon = -sum(
            (c / total) * math.log(c / total + 1e-12) for c in counts.values()
        )

        unique_tokens = list(counts.keys())
        if self._idf:
            idf_vals = [self._idf.get(t, math.log(1.0 + self._corpus_size))
                        for t in unique_tokens]
            mean_idf = float(np.mean(idf_vals)) if idf_vals else 0.0
        else:
            mean_idf = 0.0

        combined = shannon + 0.3 * mean_idf
        return float(max(combined, 0.0))

    def profile_elements(
        self, elements: List[GeometricElement]
    ) -> List[EntropyProfile]:
        '''Compute and rank entropy profiles for a list of elements.'''
        if not elements:
            return []

        raw_scores: List[float] = []
        tfidf_scores: List[float] = []

        for el in elements:
            h = self.element_entropy(el)
            raw_scores.append(h)
            tfidf_scores.append(self._tfidf_score(el))

        arr = np.array(raw_scores, dtype=float)
        span = arr.max() - arr.min()
        norm_scores = (arr - arr.min()) / span if span > 1e-12 else np.ones_like(arr)

        ranked_idx = np.argsort(norm_scores)[::-1]
        rank_map: dict[int, int] = {}
        for rank, idx in enumerate(ranked_idx, start=1):
            rank_map[int(idx)] = rank

        profiles: List[EntropyProfile] = []
        for i, el in enumerate(elements):
            norm_h = float(norm_scores[i])
            try:
                el.entropy = norm_h
            except AttributeError:
                pass

            profiles.append(
                EntropyProfile(
                    element_id=getattr(el, 'element_id', str(i)),
                    entropy=raw_scores[i],
                    tfidf_score=tfidf_scores[i],
                    is_informative=norm_h > 0.5,
                    priority=rank_map[i],
                )
            )

        profiles.sort(key=lambda p: p.priority)
        return profiles

    def entropy_score(self, element: GeometricElement) -> float:
        '''Return the normalised entropy score [0, 1] for a single element.'''
        raw = self.element_entropy(element)
        if self._idf:
            max_h = math.log(len(self._idf) + 1)
        else:
            text = getattr(element, 'content', getattr(element, 'text', '')) or ''
            tokens = self._tokenize(text)
            max_h = math.log(len(tokens) + 1) if tokens else 1.0

        return float(np.clip(raw / max(max_h, 1e-12), 0.0, 1.0))

    # ------------------------------------------------------------------
    # MIOS methods
    # ------------------------------------------------------------------

    def fourier_transform(self, signal: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        '''Computes FFT and returns frequencies and power spectrum.'''
        n = len(signal)
        if n == 0:
            return np.array([]), np.array([])
        spectrum = _fft(signal)
        freqs = _fftfreq(n)
        power = np.abs(spectrum) ** 2
        return freqs, power

    def compute_periodicity(self, signal: np.ndarray) -> float:
        '''Detects periodicity in layout signal (e.g. repeated spacing).'''
        if len(signal) < 4:
            return 0.0
        freqs, power = self.fourier_transform(signal)
        power = power.copy()
        power[0] = 0.0  # Remove DC offset
        total = power.sum()
        if total == 0:
            return 0.0
        
        peak_power = power.max()
        return float(peak_power / total)

    def eigenvalue_decomposition(self, adjacency_matrix: np.ndarray, k: int = 5) -> np.ndarray:
        '''
        Computes AX = λX eigenvalues of layout adjacency.
        Uses eigh for symmetric adjacency matrices.
        '''
        n = adjacency_matrix.shape[0]
        if n < 2:
            return np.zeros(1)
        try:
            sym_a = (adjacency_matrix + adjacency_matrix.T) / 2.0
            eigvals = np.linalg.eigvalsh(sym_a)
            eigvals = np.sort(np.abs(eigvals))[::-1]
            return eigvals[:k]
        except Exception as e:
            log.warning(f'Eigenvalue decomposition failed: {e}')
            return np.zeros(1)

    def wavelet_decomposition(self, signal: np.ndarray, scales: list[int] | None = None) -> dict[int, float]:
        '''
        Computes Wavelet energy coefficients W(a,b) over multi-scale window profiles.
        Uses a Morlet wavelet approximation.
        '''
        if scales is None:
            scales = [2, 4, 8, 16]
        
        n = len(signal)
        energy_by_scale = {}
        
        for scale in scales:
            t = np.arange(-scale * 2, scale * 2 + 1)
            morlet = np.cos(5.0 * t / scale) * np.exp(-0.5 * (t / scale) ** 2)
            coeffs = np.convolve(signal, morlet, mode='same')
            energy_by_scale[scale] = float(np.sum(np.abs(coeffs) ** 2) / (n * scale))
            
        return energy_by_scale

    def analyze(self, signal: np.ndarray, adjacency: np.ndarray | None = None) -> SpectralSignature:
        '''Runs complete spectral profiling on layout signal and adjacency.'''
        freqs, power = self.fourier_transform(signal)
        periodicity = self.compute_periodicity(signal)
        
        dominant_freq = 0.0
        if len(power) > 1:
            power = power.copy()
            power[0] = 0.0  # Ignore DC
            dom_idx = np.argmax(power)
            dominant_freq = float(abs(freqs[dom_idx]))

        eigvals = np.array([])
        if adjacency is not None:
            eigvals = self.eigenvalue_decomposition(adjacency)

        is_rep = periodicity >= self.repetition_threshold
        return SpectralSignature(
            dominant_frequency=dominant_freq,
            periodicity=periodicity,
            is_repetitive=is_rep,
            eigenvalues=eigvals
        )

    # ------------------------------------------------------------------
    # new advanced orchestrator methods
    # ------------------------------------------------------------------

    def analyze_graph(
        self,
        adjacency: AdjacencyMatrix,
        laplacian_type: LaplacianType = LaplacianType.SYMMETRIC_NORMALIZED,
        n_clusters: Optional[int] = None,
        signal: Optional[GraphSignal] = None,
        times: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SpectralReport:
        """
        Runs complete spectral profiling on a graph's adjacency matrix.

        Parameters
        ----------
        adjacency : AdjacencyMatrix
        laplacian_type : LaplacianType
        n_clusters : Optional[int]
        signal : Optional[GraphSignal]
        times : Optional[List[float]]
        metadata : Optional[Dict[str, Any]]
        """
        n = adjacency.size
        if n < 2:
            raise InsufficientDataError(f"Need at least 2 vertices for analysis, got {n}")

        # 1. Build Laplacian
        laplacian = LaplacianBuilder.build(adjacency, laplacian_type)

        # 2. Eigen-solve (compute all to get full report statistics)
        solver = EigenSolver()
        eigen_result = solver.solve(laplacian, k=None)

        # 3. Spectral Clustering
        clusterer = SpectralClusterer(laplacian_type=laplacian_type)
        clustering_result = clusterer.cluster(adjacency, n_clusters=n_clusters)

        # 4. Pattern Detection (requires n >= 3)
        if n >= 3:
            detector = PatternDetector()
            pattern_result = detector.detect(adjacency, eigen_result=eigen_result)
        else:
            # Fallback for 2-node graph
            pattern_result = PatternResult(
                patterns=[],
                bipartition=([0], [1]),
                hubs=[],
                motif_correlations=np.eye(1),
                pattern_count_by_type={}
            )

        # 5. Graph Fourier (optional)
        fourier_result = None
        if signal is not None:
            fourier_result = GraphFourierTransform.forward(signal, eigen_result)

        # 6. Heat kernel (optional)
        heat_result = None
        if signal is not None and times is not None:
            heat_result = HeatKernel(laplacian_type=laplacian_type).diffuse(
                adjacency, signal.values, times=times, eigen_result=eigen_result
            )

        return SpectralReport(
            adjacency=adjacency,
            laplacian=laplacian,
            eigen=eigen_result,
            clustering=clustering_result,
            patterns=pattern_result,
            fourier=fourier_result,
            heat=heat_result,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _element_y_center(element: GeometricElement) -> float:
        bbox = getattr(element, 'bbox', None)
        if bbox is None:
            return 0.5
        y0 = getattr(bbox, 'y0', None)
        y1 = getattr(bbox, 'y1', None)
        if y0 is not None and y1 is not None:
            return float((y0 + y1) / 2.0)
        try:
            return float((bbox[1] + bbox[3]) / 2.0)
        except (TypeError, IndexError):
            return 0.5

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        import re
        return [
            tok.lower()
            for tok in re.split(r'[^a-zA-Z0-9]+', text)
            if len(tok) >= 2
        ]

    def _tfidf_score(self, element: GeometricElement) -> float:
        text = getattr(element, 'content', getattr(element, 'text', '')) or ''
        tokens = self._tokenize(text)
        if not tokens:
            return 0.0
        counts = Counter(tokens)
        total = len(tokens)
        if not self._idf:
            return 0.0
        scores = [
            (counts[t] / total) * self._idf.get(t, 0.0)
            for t in counts
        ]
        return float(np.mean(scores)) if scores else 0.0
