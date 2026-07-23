"""
AEGIS-AMDI-OS — Engines Package
"""
from src.engines.geometry.geometry_engine import GeometryEngine, SpatialStats
from src.engines.frequency.frequency_engine import (
    FrequencyEngine, FrequencyStats,
    shannon_entropy, entropy_from_counter, information_density,
    jensen_shannon_divergence, tfidf_score, tokenize,
    DEFAULT_STOPWORDS,
)
from src.engines.recurrence.recurrence_engine import (
    RecurrenceEngine, RecurrenceGroup, RecurrenceStats,
)
from src.engines.matrix.matrix_engine import (
    MatrixEngine, TableMatrix, TableCell,
    _try_numeric, _is_numeric,
)
from src.engines.template.template_engine import (
    TemplateEngine, PageTemplate, PageFingerprint,
    DuplicateGroup, TemplateStats,
)
from src.engines.semantic.semantic_engine import (
    SemanticEngine, EmbeddingService,
    SemanticElement, Entity, Keyphrase, Topic, SentimentScore,
    EntityType, SemanticStats, SemanticResult,
)
from src.engines.graph import (
    GraphEngine, DocumentGraph, GraphNode, GraphEdge,
    GraphMetrics, CentralityScores, RelationshipPath,
    EdgeType,
)
from src.engines.topology import (
    TopologyEngine, TopologicalSignature, DocumentManifold,
    ConnectedComponentsResult, LoopsResult, ClustersResult,
    PersistenceResult, PersistenceDiagram, BettiNumbers,
    EulerCharacteristic, TopologicalMetrics,
)
from src.engines.spectral import (
    SpectralEngine, SpectralReport, AdjacencyMatrix, AdjacencyType,
    LaplacianBuilder, LaplacianType, LaplacianMatrix, EigenSolver, EigenResult,
    SpectralClusterer, SpectralClusterResult, Cluster, PatternDetector,
    PatternResult, Pattern, GraphSignal, HeatKernel, HeatDiffusionResult,
    GraphFourierTransform, FourierResult, SpectralEngineError, InvalidGraphError,
    EigenDecompositionError, ConvergenceError, InsufficientDataError,
)
from src.engines.tensor import (
    TensorEngine, TensorReport, DocumentTensor, TensorMode, TensorBuilder,
    mode_n_product, unfold, fold, tensor_norm, outer_product,
    khatri_rao_product, hadamard_product, TuckerDecomposition, TuckerResult,
    CPDecomposition, CPResult, TensorReducer, ReductionResult, marginalize,
    contract, TensorCompressor, TTDecomposition, TTResult, rank_truncate,
    TensorMetrics, explained_variance_ratio, reconstruction_error,
    TensorEngineError, InvalidTensorError, DecompositionError, CompressionError,
)
from src.engines.info_physics import (
    InformationPhysicsEngine, PhysicsReport, InformationEnergy, EnergyCalculator,
    InformationGravity, GravityCalculator, GravityField, InformationPotential,
    PotentialCalculator, InformationField, FieldCalculator, FieldMap,
    InformationFlow, FlowCalculator, FlowVector, ConservationLaw,
    ConservationChecker, ConservationReport, Thermodynamics, ThermodynamicState,
    EntropyCalculator, PhysicsMetrics, PhysicsMetricsCalculator, PhysicsEngineError,
    InvalidDocumentError, ConservationViolationError,
)
from src.engines.fusion import (
    FusionEngine, FusionReport, DynamicWeightLearner, WeightState,
    Ranker, RankingResult, RankedItem, ConfidenceEstimator, ConfidenceScore,
    FusionScorer, FusionScore, WeightOptimizer, OptimizationMethod,
    ScoreCalculator, ScoreFormula, FusionManager, FusionLifecycle,
    FusionEngineError, InvalidSignalError, WeightDimensionError, OptimizationError,
)
from src.engines.memory import (
    MemoryEngine, MemoryReport, HierarchicalMemory, MemoryStats,
    MemoryLevel, LevelMetadata, StorageManager, StorageBackend,
    CacheManager, CachePolicy, Promoter, PromotionPolicy,
    Evictor, EvictionPolicy, MemoryRetriever, RetrievalQuery,
    RetrievalResult, AccessTracker, AccessRecord, MemoryEngineError,
    LevelNotFoundError, CapacityExceededError, EvictionError,
    PromotionError,
)

__all__ = [
    "GeometryEngine", "SpatialStats",
    "FrequencyEngine", "FrequencyStats",
    "shannon_entropy", "entropy_from_counter", "information_density",
    "jensen_shannon_divergence", "tfidf_score", "tokenize",
    "DEFAULT_STOPWORDS",
    "RecurrenceEngine", "RecurrenceGroup", "RecurrenceStats",
    "MatrixEngine", "TableMatrix", "TableCell",
    "_try_numeric", "_is_numeric",
    "TemplateEngine", "PageTemplate", "PageFingerprint",
    "DuplicateGroup", "TemplateStats",
    "SemanticEngine", "EmbeddingService",
    "SemanticElement", "Entity", "Keyphrase", "Topic", "SentimentScore",
    "EntityType", "SemanticStats", "SemanticResult",
    "GraphEngine", "DocumentGraph", "GraphNode", "GraphEdge",
    "GraphMetrics", "CentralityScores", "RelationshipPath",
    "EdgeType",
    "TopologyEngine", "TopologicalSignature", "DocumentManifold",
    "ConnectedComponentsResult", "LoopsResult", "ClustersResult",
    "PersistenceResult", "PersistenceDiagram", "BettiNumbers",
    "EulerCharacteristic", "TopologicalMetrics",
    "SpectralEngine", "SpectralReport", "AdjacencyMatrix", "AdjacencyType",
    "LaplacianBuilder", "LaplacianType", "LaplacianMatrix", "EigenSolver", "EigenResult",
    "SpectralClusterer", "SpectralClusterResult", "Cluster", "PatternDetector",
    "PatternResult", "Pattern", "GraphSignal", "HeatKernel", "HeatDiffusionResult",
    "GraphFourierTransform", "FourierResult", "SpectralEngineError", "InvalidGraphError",
    "EigenDecompositionError", "ConvergenceError", "InsufficientDataError",
    "TensorEngine", "TensorReport", "DocumentTensor", "TensorMode", "TensorBuilder",
    "mode_n_product", "unfold", "fold", "tensor_norm", "outer_product",
    "khatri_rao_product", "hadamard_product", "TuckerDecomposition", "TuckerResult",
    "CPDecomposition", "CPResult", "TensorReducer", "ReductionResult", "marginalize",
    "contract", "TensorCompressor", "TTDecomposition", "TTResult", "rank_truncate",
    "TensorMetrics", "explained_variance_ratio", "reconstruction_error",
    "TensorEngineError", "InvalidTensorError", "DecompositionError", "CompressionError",
    "InformationPhysicsEngine", "PhysicsReport", "InformationEnergy", "EnergyCalculator",
    "InformationGravity", "GravityCalculator", "GravityField", "InformationPotential",
    "PotentialCalculator", "InformationField", "FieldCalculator", "FieldMap",
    "InformationFlow", "FlowCalculator", "FlowVector", "ConservationLaw",
    "ConservationChecker", "ConservationReport", "Thermodynamics", "ThermodynamicState",
    "EntropyCalculator", "PhysicsMetrics", "PhysicsMetricsCalculator", "PhysicsEngineError",
    "InvalidDocumentError", "ConservationViolationError",
    "FusionEngine", "FusionReport", "DynamicWeightLearner", "WeightState",
    "Ranker", "RankingResult", "RankedItem", "ConfidenceEstimator", "ConfidenceScore",
    "FusionScorer", "FusionScore", "WeightOptimizer", "OptimizationMethod",
    "ScoreCalculator", "ScoreFormula", "FusionManager", "FusionLifecycle",
    "FusionEngineError", "InvalidSignalError", "WeightDimensionError", "OptimizationError",
    "MemoryEngine", "MemoryReport", "HierarchicalMemory", "MemoryStats",
    "MemoryLevel", "LevelMetadata", "StorageManager", "StorageBackend",
    "CacheManager", "CachePolicy", "Promoter", "PromotionPolicy",
    "Evictor", "EvictionPolicy", "MemoryRetriever", "RetrievalQuery",
    "RetrievalResult", "AccessTracker", "AccessRecord", "MemoryEngineError",
    "LevelNotFoundError", "CapacityExceededError", "EvictionError",
    "PromotionError",
]



