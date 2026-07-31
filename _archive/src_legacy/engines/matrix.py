"""Alias for easy importing."""
from src.engines.matrix.matrix_engine import (
    MatrixEngine, TableMatrix, TableCell,
    _try_numeric, _is_numeric,
)

__all__ = [
    "MatrixEngine", "TableMatrix", "TableCell",
    "_try_numeric", "_is_numeric",
]
