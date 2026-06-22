"""

Custom exceptions for the Hybrid Retrieval Engine.

"""





class RetrievalEngineError(Exception):

    """Base exception for all Retrieval Engine errors."""





class EmptyIndexError(RetrievalEngineError):

    """Raised when an index is empty."""





class InvalidQueryError(RetrievalEngineError):

    """Raised when a query is malformed."""





class RankFusionError(RetrievalEngineError):

    """Raised when result fusion fails."""





class IndexDimensionError(RetrievalEngineError):

    """Raised when embedding dimensions don't match."""
