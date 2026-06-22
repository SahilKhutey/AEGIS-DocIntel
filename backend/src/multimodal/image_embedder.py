"""
Image Embedder
================

CLIP-based image + text embeddings for cross-modal retrieval.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np


class ImageEmbedder(ABC):
    """Abstract image embedder."""

    @abstractmethod
    def embed(self, image_data: bytes) -> Optional[np.ndarray]:
        """Embed an image to a vector."""
        ...

    @abstractmethod
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Embed text (for cross-modal retrieval)."""
        ...

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        ...


class CLIPEmbedder(ImageEmbedder):
    """
    CLIP-based embedder (mock implementation).

    In production, this would use `open_clip` or HuggingFace transformers:
        from transformers import CLIPModel, CLIPProcessor
    """

    def __init__(self, model_name: str = "ViT-B/32", embedding_dim: int = 512) -> None:
        self.model_name = model_name
        self._embedding_dim = embedding_dim
        self._model = None
        self._processor = None
        try:
            # Lazy load CLIP if available
            from transformers import CLIPModel, CLIPProcessor  # noqa: F401
            self._clip_available = True
        except ImportError:
            self._clip_available = False

    def _ensure_loaded(self) -> None:
        """Lazy-load the CLIP model."""
        if self._model is None and self._clip_available:
            try:
                from transformers import CLIPModel, CLIPProcessor
                self._model = CLIPModel.from_pretrained(
                    f"openai/clip-{self.model_name.lower()}"
                )
                self._processor = CLIPProcessor.from_pretrained(
                    f"openai/clip-{self.model_name.lower()}"
                )
            except Exception:
                self._clip_available = False

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    def embed(self, image_data: bytes) -> Optional[np.ndarray]:
        """Embed image bytes to a vector."""
        self._ensure_loaded()
        if not self._clip_available or self._model is None:
            # fallback: deterministic hash-based embedding
            return self._fallback_embed(image_data)
        try:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            import torch
            inputs = self._processor(images=image, return_tensors="pt")
            with torch.no_grad():
                features = self._model.get_image_features(**inputs)
            embedding = features[0].cpu().numpy()
            return embedding / np.linalg.norm(embedding)
        except Exception:
            return self._fallback_embed(image_data)

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Embed text using CLIP text encoder."""
        self._ensure_loaded()
        if not self._clip_available or self._model is None:
            return self._fallback_embed(text.encode())
        try:
            import torch
            inputs = self._processor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                features = self._model.get_text_features(**inputs)
            embedding = features[0].cpu().numpy()
            return embedding / np.linalg.norm(embedding)
        except Exception:
            return self._fallback_embed(text.encode())

    def _fallback_embed(self, data: bytes) -> np.ndarray:
        """Deterministic fallback embedding when CLIP unavailable."""
        # Use SHA-256 to seed RNG, then generate fixed-size vector
        seed = int.from_bytes(hashlib.sha256(data).digest()[:4], "big")
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self._embedding_dim).astype(np.float32)
        return embedding / np.linalg.norm(embedding)

    def embed_batch(self, images: List[bytes]) -> List[Optional[np.ndarray]]:
        """Embed a batch of images."""
        return [self.embed(img) for img in images]
