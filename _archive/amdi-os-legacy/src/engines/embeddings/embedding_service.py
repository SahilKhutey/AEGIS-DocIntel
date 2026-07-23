"""
AMDI-OS — Embedding Service
===========================
Generates semantic embeddings for document blocks and queries.
Uses sentence-transformers if available, otherwise falls back to deterministic mock vectors.
"""
from __future__ import annotations
import hashlib
import logging
from typing import List, Optional
import numpy as np

import os
import sys

def _check_sentence_transformers() -> bool:
    is_test = "pytest" in sys.modules or os.getenv("AMDI_ENV") == "test"
    mock_env = os.getenv("AMDI_MOCK_EMBEDDINGS", "false").lower() == "true"
    if is_test or mock_env:
        return False
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False

HAS_SENTENCE_TRANSFORMERS = _check_sentence_transformers()

log = logging.getLogger("amdi.embeddings")


class EmbeddingService:
    """
    Embedding Service to generate dense vectors.
    """
    def __init__(
        self,
        model_name: str = "BAAI/bge-large-en-v1.5",
        device: str = "cpu",
        dim: int = 1024
    ) -> None:
        import os
        import sys
        self.model_name = model_name
        self.device = device
        self._dim = dim
        self._model: Optional[SentenceTransformer] = None
        
        is_test = "pytest" in sys.modules or os.getenv("AMDI_ENV") == "test"
        mock_env = os.getenv("AMDI_MOCK_EMBEDDINGS", "false").lower() == "true"
        
        self._is_mock = not HAS_SENTENCE_TRANSFORMERS or is_test or mock_env or model_name == "mock"
        
        if self._is_mock:
            log.warning(
                "EmbeddingService running in MOCK mode (generating deterministic vectors based on text hash)."
            )
        else:
            log.info(
                f"EmbeddingService initialized with model={model_name}, device={device}, dim={dim}"
            )

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def _lazy_load_model(self) -> None:
        if self._is_mock or self._model is not None:
            return
        
        try:
            log.info(f"Lazy loading sentence-transformer model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)
        except Exception as e:
            log.error(f"Failed to load sentence-transformers model {self.model_name}: {e}. Falling back to MOCK mode.")
            self._is_mock = True

    def _generate_mock_vector(self, text: str) -> np.ndarray:
        """
        Generates a deterministic unit vector based on the SHA-256 hash of the input text.
        """
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Seed RNG with the hash to make it reproducible
        seed = int.from_bytes(h[:4], byteorder="big")
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self._dim)
        norm = np.linalg.norm(v)
        if norm > 0:
            v = v / norm
        return v

    def encode(
        self,
        sentences: str | List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        **kwargs: Any
    ) -> np.ndarray | List[np.ndarray]:
        """
        Alias for encode_sync to provide sentence-transformers compatibility.
        """
        return self.encode_sync(sentences)

    def encode_sync(self, texts: str | List[str]) -> np.ndarray | List[np.ndarray]:
        """
        Synchronously encode a list of texts (or a single text) into dense vectors.
        """
        if not texts:
            return [] if not isinstance(texts, str) else np.zeros(self._dim, dtype=np.float32)
            
        is_str = isinstance(texts, str)
        actual_list = [texts] if is_str else texts
        
        self._lazy_load_model()
        
        if self._is_mock:
            results = [self._generate_mock_vector(t) for t in actual_list]
        else:
            try:
                # We assume self._model is loaded and not None
                embeddings = self._model.encode(actual_list, show_progress_bar=False, convert_to_numpy=True) # type: ignore
                # Handle shape adjustments if needed
                results = [np.array(emb, dtype=np.float32) for emb in embeddings]
            except Exception as e:
                log.error(f"Error during synchronous embedding generation: {e}. Falling back to mock vectors.")
                results = [self._generate_mock_vector(t) for t in actual_list]
                
        return results[0] if is_str else results

    async def encode_text(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Asynchronously encode a list of texts into dense vectors (runs sync encoding in a threadpool).
        """
        if not texts:
            return []
            
        loop = import_loop = None
        try:
            import asyncio
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
            
        if loop is not None:
            return await loop.run_in_executor(None, self.encode_sync, texts)
        else:
            return self.encode_sync(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query string.
        """
        res = self.encode_sync([query])
        if res:
            return res[0]
        # Return zeros in case of error/empty query
        return np.zeros(self._dim, dtype=np.float32)
