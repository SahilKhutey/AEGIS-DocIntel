"""

Custom exceptions for the Benchmarking framework.

"""





class BenchmarkError(Exception):

    """Base exception for all benchmarking errors."""





class DatasetMissingError(BenchmarkError):

    """Raised when a required dataset is not found."""





class MetricComputationError(BenchmarkError):

    """Raised when metric computation fails."""





class BaselineMismatchError(BenchmarkError):

    """Raised when baseline configuration is invalid."""





class GroundTruthError(BenchmarkError):

    """Raised when ground truth data is malformed."""
