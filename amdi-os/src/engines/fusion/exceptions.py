"""

Custom exceptions for the Fusion Engine.

"""





class FusionEngineError(Exception):

    """Base exception for all Fusion Engine errors."""





class InvalidSignalError(FusionEngineError):

    """Raised when an input signal is malformed or has wrong shape."""





class WeightDimensionError(FusionEngineError):

    """Raised when weight vector dimensions don't match signal dimensions."""





class OptimizationError(FusionEngineError):

    """Raised when weight optimization fails to converge."""





class ConfidenceEstimationError(FusionEngineError):

    """Raised when confidence estimation fails."""
