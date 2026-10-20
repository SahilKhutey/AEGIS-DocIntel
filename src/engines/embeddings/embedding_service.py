"""
AMDI-OS — Embedding Service
===========================
Generates semantic embeddings for document blocks and queries.
Supports SentenceTransformers, native OpenAI embeddings, and LiteLLM embeddings,
with deterministic hash-based mock fallback.
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
from typing import Any, List, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

def _check_sentence_transformers() -> bool:
    is_test = "pytest" in sys.modules or os.getenv("AMDI_ENV") == "test"
    mock_env = os.getenv("AMDI_MOCK_EMBEDDINGS", "false").lower() == "true"
    if is_test or mock_env:
        return False
    try:
        import importlib.util
        return importlib.util.find_spec("sentence_transformers") is not None
    except Exception:
        return False

HAS_SENTENCE_TRANSFORMERS = _check_sentence_transformers()

log = logging.getLogger("amdi.embeddings")


class EmbeddingService:
    """
    Dense text embedding service supporting local, OpenAI, LiteLLM, and deterministic mock providers.
    """
    def __init__(
        self,
        model_name: str = "BAAI/bge-large-en-v1.5",
        device: str = "cpu",
        dim: int = 1024,
        provider: str = "auto",
        api_key: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self._dim = dim
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model: Optional[SentenceTransformer] = None

        env_provider = os.getenv("EMBEDDING_PROVIDER") or os.getenv("AMDI_EMBEDDING_PROVIDER")
        resolved_provider = (env_provider or provider).lower()

        is_test = "pytest" in sys.modules or os.getenv("AMDI_ENV") == "test"
        mock_env = os.getenv("AMDI_MOCK_EMBEDDINGS", "false").lower() == "true"

        if mock_env or model_name == "mock" or resolved_provider == "mock":
            self.provider = "mock"
            self._is_mock = True
        elif resolved_provider in ("openai", "azure"):
            self.provider = "openai"
            self._is_mock = False
            if self._dim == 1024 and ("text-embedding" in self.model_name or self.model_name == "BAAI/bge-large-en-v1.5"):
                if self.model_name == "BAAI/bge-large-en-v1.5":
                    self.model_name = "text-embedding-3-small"
                self._dim = 1536
        elif resolved_provider == "litellm":
            self.provider = "litellm"
            self._is_mock = False
        elif resolved_provider == "sentence_transformers":
            if HAS_SENTENCE_TRANSFORMERS and not is_test:
                self.provider = "sentence_transformers"
                self._is_mock = False
            else:
                self.provider = "mock"
                self._is_mock = True
        elif resolved_provider == "auto":
            if self.api_key and not is_test and ("text-embedding" in model_name or not HAS_SENTENCE_TRANSFORMERS):
                self.provider = "openai"
                self._is_mock = False
                if self._dim == 1024 and "text-embedding" in self.model_name:
                    self._dim = 1536
            elif HAS_SENTENCE_TRANSFORMERS and not is_test:
                self.provider = "sentence_transformers"
                self._is_mock = False
            else:
                self.provider = "mock"
                self._is_mock = True
        else:
            self.provider = "mock"
            self._is_mock = True

        if self._is_mock:
            log.warning(
                "EmbeddingService running in MOCK mode (generating deterministic vectors based on text hash)."
            )
        else:
            log.info(
                "EmbeddingService initialized with provider=%s, model=%s, dim=%d",
                self.provider, self.model_name, self._dim
            )

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    @property
    def is_using_real_embeddings(self) -> bool:
        return not self._is_mock

    def _lazy_load_model(self) -> None:
        if self._is_mock or self._model is not None:
            return
        
        try:
            log.info(f"Lazy loading sentence-transformer model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)
            if hasattr(self._model, "get_embedding_dimension"):
                self._dim = self._model.get_embedding_dimension()
            elif hasattr(self._model, "get_sentence_embedding_dimension"):
                self._dim = self._model.get_sentence_embedding_dimension()
        except Exception as e:
            log.error(f"Failed to load sentence-transformers model {self.model_name}: {e}. Falling back to MOCK mode.")
            self._is_mock = True
            self.provider = "mock"

    def _generate_mock_vector(self, text: str) -> np.ndarray:
        """Generates a deterministic unit vector based on the SHA-256 hash of the input text."""
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:4], byteorder="big")
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(self._dim).astype(np.float32)
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
        """Sentence-transformers compatible encode method returning numpy arrays."""
        if not sentences:
            if isinstance(sentences, str):
                return np.zeros(self._dim, dtype=np.float32)
            return np.empty((0, self._dim), dtype=np.float32)

        res = self.encode_sync(sentences)
        if convert_to_numpy:
            return np.array(res, dtype=np.float32)
        return res

    def encode_sync(self, texts: str | List[str]) -> np.ndarray | List[np.ndarray]:
        """Synchronously encode a list of texts (or a single text) into dense vectors."""
        if not texts:
            return [] if not isinstance(texts, str) else np.zeros(self._dim, dtype=np.float32)
            
        is_str = isinstance(texts, str)
        actual_list = [texts] if is_str else texts

        if self._is_mock or self.provider == "mock":
            results = [self._generate_mock_vector(t) for t in actual_list]
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                resp = client.embeddings.create(input=actual_list, model=self.model_name)
                results = [np.array(item.embedding, dtype=np.float32) for item in resp.data]
            except Exception as e:
                log.error(f"OpenAI embedding error: {e}. Falling back to mock vectors.")
                results = [self._generate_mock_vector(t) for t in actual_list]
        elif self.provider == "litellm":
            try:
                import litellm
                resp = litellm.embedding(model=self.model_name, input=actual_list, api_key=self.api_key)
                results = [np.array(item["embedding"], dtype=np.float32) for item in resp["data"]]
            except Exception as e:
                log.error(f"LiteLLM embedding error: {e}. Falling back to mock vectors.")
                results = [self._generate_mock_vector(t) for t in actual_list]
        elif self.provider == "sentence_transformers":
            self._lazy_load_model()
            if self._is_mock:
                results = [self._generate_mock_vector(t) for t in actual_list]
            else:
                try:
                    embeddings = self._model.encode(actual_list, show_progress_bar=False, convert_to_numpy=True)  # type: ignore
                    results = [np.array(emb, dtype=np.float32) for emb in embeddings]
                except Exception as e:
                    log.error(f"SentenceTransformer error: {e}. Falling back to mock vectors.")
                    results = [self._generate_mock_vector(t) for t in actual_list]
        else:
            results = [self._generate_mock_vector(t) for t in actual_list]
                
        return results[0] if is_str else results

    async def encode_text(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Asynchronously encode a list of texts into dense vectors."""
        if not texts:
            return []
            
        loop = None
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
        """Generate embedding for a single query string."""
        res = self.encode_sync([query])
        if res:
            return res[0]
        return np.zeros(self._dim, dtype=np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        """Alias for embed_query."""
        return self.embed_query(query)
