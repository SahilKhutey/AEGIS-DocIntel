"""
AEGIS-DocIntel — Multi-Provider Embedding Service Tests
======================================================
Validates provider switching (OpenAI, LiteLLM, SentenceTransformers, Mock),
API error fallback resilience, dimension configuration, and orchestrator wiring.
"""
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from src.engines.embeddings.embedding_service import EmbeddingService
from src.core.orchestrator import AMDIOrchestrator


def test_embedding_service_mock_provider():
    service = EmbeddingService(provider="mock", dim=512)
    assert service.dim == 512
    assert service.is_mock is True
    assert service.is_using_real_embeddings is False

    vecs = service.encode(["alpha", "beta"])
    assert isinstance(vecs, np.ndarray)
    assert vecs.shape == (2, 512)

    # Unit norm check
    norm0 = np.linalg.norm(vecs[0])
    norm1 = np.linalg.norm(vecs[1])
    assert abs(norm0 - 1.0) < 1e-4
    assert abs(norm1 - 1.0) < 1e-4

    # Single string query
    q_vec = service.encode_query("What is the quarterly revenue?")
    assert isinstance(q_vec, np.ndarray)
    assert q_vec.shape == (512,)


def test_embedding_service_openai_provider():
    mock_item1 = MagicMock(embedding=[0.1] * 1536)
    mock_item2 = MagicMock(embedding=[0.2] * 1536)
    mock_resp = MagicMock(data=[mock_item1, mock_item2])

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_resp
        mock_openai_cls.return_value = mock_client

        service = EmbeddingService(
            provider="openai",
            model_name="text-embedding-3-small",
            api_key="sk-test-mock-key-12345",
            dim=1536,
        )
        assert service.provider == "openai"
        assert service.dim == 1536
        assert service.is_mock is False
        assert service.is_using_real_embeddings is True

        res = service.encode(["doc one", "doc two"])
        assert isinstance(res, np.ndarray)
        assert res.shape == (2, 1536)
        mock_client.embeddings.create.assert_called_once_with(
            input=["doc one", "doc two"],
            model="text-embedding-3-small",
        )


def test_embedding_service_litellm_provider():
    mock_resp = {
        "data": [
            {"embedding": [0.3] * 768},
            {"embedding": [0.4] * 768},
        ]
    }

    with patch("litellm.embedding", return_value=mock_resp) as mock_litellm_emb:
        service = EmbeddingService(
            provider="litellm",
            model_name="text-embedding-3-small",
            api_key="sk-test-litellm-key",
            dim=768,
        )
        assert service.provider == "litellm"
        assert service.is_mock is False

        res = service.encode(["chunk A", "chunk B"])
        assert isinstance(res, np.ndarray)
        assert res.shape == (2, 768)
        mock_litellm_emb.assert_called_once_with(
            model="text-embedding-3-small",
            input=["chunk A", "chunk B"],
            api_key="sk-test-litellm-key",
        )


def test_embedding_service_api_error_fallback():
    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = RuntimeError("OpenAI 500 internal server error")
        mock_openai_cls.return_value = mock_client

        service = EmbeddingService(
            provider="openai",
            model_name="text-embedding-3-small",
            api_key="sk-test-mock-key",
            dim=1536,
        )
        # Should gracefully fall back to mock without raising
        res = service.encode(["resilient text"])
        assert isinstance(res, np.ndarray)
        assert res.shape == (1, 1536)
        assert not np.isnan(res).any()


def test_orchestrator_wiring_with_embedding_config():
    config = {
        "embedding_provider": "mock",
        "embedding_model": "custom-bge-model",
        "embedding_dim": 512,
    }
    orchestrator = AMDIOrchestrator(config=config)
    assert orchestrator._embedding is not None
    assert orchestrator._embedding.dim == 512
    assert orchestrator._embedding.provider == "mock"
    assert orchestrator._embedding.model_name == "custom-bge-model"
