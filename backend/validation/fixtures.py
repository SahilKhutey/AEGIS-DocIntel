"""
Test fixtures for AMDI-OS validation.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def sample_pdf_text() -> str:
    """Sample PDF text for testing."""
    return (
        "Quantum mechanics is a fundamental theory in physics that describes "
        "nature at the smallest scales of energy levels of atoms and subatomic "
        "particles. Quantum mechanics is the foundation of several disciplines "
        "including nanotechnology, quantum computing, and quantum information "
        "science. The theory was developed in the early 20th century by physicists "
        "such as Max Planck, Albert Einstein, Niels Bohr, Werner Heisenberg, "
        "and Erwin Schrödinger. "
        "\n\n"
        "Machine learning is a method of data analysis that automates analytical "
        "model building. It is a branch of artificial intelligence based on the "
        "idea that systems can learn from data, identify patterns and make "
        "decisions with minimal human intervention. Machine learning algorithms "
        "are often categorized as supervised or unsupervised. "
        "\n\n"
        "The combination of quantum computing and machine learning has given rise "
        "to the field of quantum machine learning, which explores the intersection "
        "of these two revolutionary technologies."
    )


def sample_document() -> Dict[str, Any]:
    """Sample document data."""
    return {
        "id": "doc_test_001",
        "name": "quantum_ml_overview.pdf",
        "type": "pdf",
        "size_bytes": 4096,
        "page_count": 12,
        "text": sample_pdf_text(),
        "metadata": {
            "author": "Smith, J.",
            "year": 2024,
            "title": "Quantum Machine Learning: An Overview",
        },
    }


def sample_ground_truth() -> List[Dict[str, Any]]:
    """Sample ground truth Q&A pairs."""
    return [
        {
            "question": "Who developed quantum mechanics?",
            "expected_answer": "Max Planck, Albert Einstein, Niels Bohr, Werner Heisenberg, and Erwin Schrödinger.",
            "expected_pages": [1, 2],
            "category": "scientific",
            "difficulty": "easy",
        },
        {
            "question": "What is quantum machine learning?",
            "expected_answer": "A field that combines quantum computing and machine learning.",
            "expected_pages": [3],
            "category": "scientific",
            "difficulty": "medium",
        },
        {
            "question": "What year was quantum mechanics developed?",
            "expected_answer": "Early 20th century.",
            "expected_pages": [1],
            "category": "scientific",
            "difficulty": "easy",
        },
    ]


def sample_embeddings(n: int = 64, dim: int = 384, seed: int = 42) -> np.ndarray:
    """Generate sample embeddings."""
    rng = np.random.RandomState(seed)
    return rng.rand(n, dim).astype(np.float64)


def sample_table_data() -> Dict[str, Any]:
    """Sample table data."""
    return {
        "headers": ["Method", "Accuracy", "Speed"],
        "rows": [
            ["Classical", "85%", "10ms"],
            ["Quantum", "92%", "5ms"],
            ["Hybrid", "95%", "7ms"],
        ],
    }


def sample_graph_data() -> Dict[str, Any]:
    """Sample graph data."""
    return {
        "nodes": [
            {"id": "n1", "label": "Quantum", "type": "concept"},
            {"id": "n2", "label": "ML", "type": "concept"},
            {"id": "n3", "label": "Hybrid", "type": "concept"},
        ],
        "edges": [
            {"source": "n1", "target": "n3", "weight": 1.0},
            {"source": "n2", "target": "n3", "weight": 1.0},
        ],
    }


def sample_corpus(n_documents: int = 10) -> List[Dict[str, Any]]:
    """Generate a small synthetic corpus."""
    rng = np.random.RandomState(42)
    docs = []
    topics = [
        "quantum computing", "machine learning", "neural networks",
        "data science", "computer vision", "NLP",
        "robotics", "bioinformatics", "cryptography", "optimization",
    ]
    for i in range(n_documents):
        topic = topics[i % len(topics)]
        docs.append({
            "id": f"doc_{i}",
            "name": f"document_{i}.pdf",
            "type": "pdf",
            "text": f"This document discusses {topic}. " * 50,
            "topic": topic,
            "size_bytes": rng.randint(1000, 100000),
            "metadata": {"topic": topic},
        })
    return docs
