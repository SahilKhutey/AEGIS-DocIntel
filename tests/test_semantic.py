"""Tests for the semantic engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import pytest
import numpy as np

from src.engines.semantic import (
    SemanticEngine, EmbeddingService,
    SemanticElement, Entity, EntityType,
    Keyphrase, Topic, SentimentScore,
)


# ============================================================
# INITIALIZATION
# ============================================================

def test_init():
    engine = SemanticEngine()
    assert engine.embedder is not None


# ============================================================
# 1. EMBEDDINGS
# ============================================================

def test_embedder_fallback():
    """Without sentence-transformers, use hash fallback."""
    service = EmbeddingService(model_name="nonexistent-model")
    vecs = service.encode(["hello", "world"])
    assert vecs.shape[0] == 2
    assert vecs.shape[1] == 1024  # Default dim


def test_encode_normalized():
    service = EmbeddingService()
    vec = service.encode(["test"])[0]
    norm = np.linalg.norm(vec)
    if norm > 0:
        assert abs(norm - 1.0) < 0.01


def test_encode_empty():
    service = EmbeddingService()
    vecs = service.encode([])
    assert vecs.shape[0] == 0


def test_encode_query():
    service = EmbeddingService()
    vec = service.encode_query("What is X?")
    assert vec.ndim == 1


def test_deterministic_hash_embeddings():
    """Same text → same embedding (fallback)."""
    service = EmbeddingService()
    v1 = service.encode(["hello world"])[0]
    v2 = service.encode(["hello world"])[0]
    assert np.allclose(v1, v2)


def test_different_texts_different_embeddings():
    service = EmbeddingService()
    v1 = service.encode(["hello world"])[0]
    v2 = service.encode(["goodbye world"])[0]
    assert not np.allclose(v1, v2)


def test_semantic_engine_embeddings():
    import asyncio
    engine = SemanticEngine()
    elements = asyncio.run(engine.compute_embeddings(["test text"]))
    assert len(elements) == 1
    assert elements[0].embedding is not None


# ============================================================
# 2. ENTITY EXTRACTION
# ============================================================

def test_extract_money():
    engine = SemanticEngine()
    entities = engine.extract_entities("The price is $100.")
    money_entities = [e for e in entities if e.type == EntityType.MONEY]
    assert len(money_entities) >= 1
    assert "$100" in money_entities[0].text


def test_extract_money_with_suffix():
    engine = SemanticEngine()
    entities = engine.extract_entities("Revenue was $5 million.")
    money = [e for e in entities if e.type == EntityType.MONEY]
    assert len(money) >= 1


def test_extract_percent():
    engine = SemanticEngine()
    entities = engine.extract_entities("Growth was 25.5%.")
    pct = [e for e in entities if e.type == EntityType.PERCENT]
    assert len(pct) >= 1
    assert "25.5" in pct[0].text


def test_extract_dates_iso():
    engine = SemanticEngine()
    entities = engine.extract_entities("Date: 2024-01-15")
    dates = [e for e in entities if e.type == EntityType.DATE]
    assert len(dates) >= 1


def test_extract_dates_quarter():
    engine = SemanticEngine()
    entities = engine.extract_entities("Revenue in Q1 2024 was strong.")
    dates = [e for e in entities if e.type == EntityType.DATE]
    assert any("Q1 2024" in d.text for d in dates)


def test_extract_email():
    engine = SemanticEngine()
    entities = engine.extract_entities("Contact: john@example.com")
    emails = [e for e in entities if e.type == EntityType.EMAIL]
    assert len(emails) >= 1
    assert "john@example.com" in emails[0].text


def test_extract_url():
    engine = SemanticEngine()
    entities = engine.extract_entities("Visit https://example.com for info.")
    urls = [e for e in entities if e.type == EntityType.URL]
    assert len(urls) >= 1


def test_extract_phone():
    engine = SemanticEngine()
    entities = engine.extract_entities("Call +1-555-123-4567")
    phones = [e for e in entities if e.type == EntityType.PHONE]
    assert len(phones) >= 1


def test_extract_organization_acronym():
    engine = SemanticEngine()
    entities = engine.extract_entities("IBM and NASA are major organizations.")
    orgs = [e for e in entities if e.type == EntityType.ORGANIZATION]
    assert any("IBM" in o.text or "NASA" in o.text for o in orgs)


def test_extract_person_with_title():
    engine = SemanticEngine()
    entities = engine.extract_entities("Dr. Smith presented the findings.")
    persons = [e for e in entities if e.type == EntityType.PERSON]
    assert any("Smith" in p.text for p in persons)


def test_extract_entities_empty():
    engine = SemanticEngine()
    entities = engine.extract_entities("")
    assert entities == []


def test_extract_entities_deduplicated():
    """Same entity twice → only one result."""
    engine = SemanticEngine()
    text = "$100 and $100 again"
    entities = engine.extract_entities(text)
    money = [e for e in entities if e.type == EntityType.MONEY]
    assert len(money) == 1


# ============================================================
# 3. TOPIC MODELING
# ============================================================

def test_extract_keyphrases_basic():
    engine = SemanticEngine()
    keyphrases = engine.extract_keyphrases(
        "Machine learning models process natural language data efficiently.",
        top_k=5,
    )
    assert len(keyphrases) >= 1


def test_extract_keyphrases_empty():
    engine = SemanticEngine()
    keyphrases = engine.extract_keyphrases("")
    assert keyphrases == []


def test_extract_keyphrases_filters_stopwords():
    engine = SemanticEngine()
    keyphrases = engine.extract_keyphrases(
        "The machine learning algorithm processes the data efficiently.",
        top_k=5,
    )
    texts = [k.text for k in keyphrases]
    assert "the" not in texts


def test_model_topics_basic():
    engine = SemanticEngine()
    docs = [
        "Machine learning and artificial intelligence",
        "Deep learning neural networks",
        "Database systems and SQL queries",
        "Data science and analytics",
    ]
    topics = engine.model_topics(docs, n_topics=2)
    assert len(topics) >= 1
    for t in topics:
        assert isinstance(t, Topic)
        assert len(t.keywords) > 0


def test_model_topics_empty():
    engine = SemanticEngine()
    topics = engine.model_topics([])
    assert topics == []


def test_model_topics_single_doc():
    engine = SemanticEngine()
    docs = ["Machine learning algorithms process data."]
    topics = engine.model_topics(docs, n_topics=3)
    assert isinstance(topics, list)


# ============================================================
# 4. SIMILARITY SEARCH
# ============================================================

def test_cosine_similarity_identical():
    engine = SemanticEngine()
    v = np.array([1.0, 0.0, 0.0])
    sim = engine.cosine_similarity(v, v)
    assert sim == pytest.approx(1.0, abs=1e-6)


def test_cosine_similarity_orthogonal():
    engine = SemanticEngine()
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    sim = engine.cosine_similarity(v1, v2)
    assert sim == pytest.approx(0.0, abs=1e-6)


def test_cosine_similarity_opposite():
    engine = SemanticEngine()
    v1 = np.array([1.0, 0.0])
    v2 = np.array([-1.0, 0.0])
    sim = engine.cosine_similarity(v1, v2)
    assert sim == pytest.approx(-1.0, abs=1e-6)


def test_cosine_similarity_zero_vector():
    engine = SemanticEngine()
    v1 = np.zeros(3)
    v2 = np.array([1.0, 0.0, 0.0])
    sim = engine.cosine_similarity(v1, v2)
    assert sim == 0.0


def test_cosine_similarity_matrix():
    engine = SemanticEngine()
    vecs = np.array([
        [1, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
    ], dtype=np.float32)
    sim = engine.cosine_similarity_matrix(vecs)
    assert sim.shape == (3, 3)
    assert np.allclose(np.diag(sim), 1.0)
    assert sim[0, 1] == pytest.approx(1.0)
    assert sim[0, 2] == pytest.approx(0.0, abs=1e-6)


def test_euclidean_distance():
    engine = SemanticEngine()
    v1 = np.array([0.0, 0.0, 0.0])
    v2 = np.array([3.0, 4.0, 0.0])
    dist = engine.euclidean_distance(v1, v2)
    assert dist == 5.0


def test_find_similar_basic():
    engine = SemanticEngine()
    query = np.array([1.0, 0.0, 0.0])
    candidates = np.array([
        [1.0, 0.0, 0.0],
        [0.5, 0.5, 0.0],
        [0.0, 1.0, 0.0],
    ])
    results = engine.find_similar(query, candidates, top_k=2)
    assert len(results) == 2
    assert results[0][1] > results[1][1]


def test_find_similar_with_threshold():
    engine = SemanticEngine()
    query = np.array([1.0, 0.0, 0.0])
    candidates = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ])
    results = engine.find_similar(query, candidates, top_k=5, threshold=0.9)
    assert len(results) == 1


def test_find_similar_empty():
    engine = SemanticEngine()
    query = np.array([1.0, 0.0])
    candidates = np.zeros((0, 2))
    results = engine.find_similar(query, candidates)
    assert results == []


def test_find_similar_text():
    engine = SemanticEngine()
    candidates = [
        "Machine learning is great",
        "Deep learning is powerful",
        "I love pizza",
    ]
    results = engine.find_similar_text("Neural networks learn", candidates, top_k=2)
    assert len(results) <= 2


# ============================================================
# 5. SUMMARIZATION
# ============================================================

def test_summarize_extractive_basic():
    engine = SemanticEngine()
    text = (
        "Machine learning is a field of AI. "
        "Deep learning uses neural networks with many layers. "
        "Natural language processing handles text data. "
        "Computer vision processes images. "
        "Reinforcement learning trains agents via rewards."
    )
    summary = engine.summarize_extractive(text, n_sentences=2)
    assert len(summary) > 0
    assert len(summary) < len(text)


def test_summarize_short_text():
    engine = SemanticEngine()
    text = "Short text."
    summary = engine.summarize_extractive(text, n_sentences=3)
    assert summary == "Short text."


def test_summarize_empty_text():
    engine = SemanticEngine()
    summary = engine.summarize_extractive("")
    assert summary == ""


def test_summarize_extracts_key_sentences():
    engine = SemanticEngine()
    text = (
        "Revenue grew 25%. "
        "The company launched new products. "
        "Costs increased due to expansion. "
        "Net profit improved significantly. "
        "The board approved dividends."
    )
    summary = engine.summarize_extractive(text, n_sentences=2)
    assert any(word in summary.lower() for word in ["revenue", "profit", "growth", "25"])


def test_summarize_preserves_order():
    engine = SemanticEngine()
    text = "First sentence here. Second sentence. Third sentence. Fourth. Fifth."
    summary = engine.summarize_extractive(text, n_sentences=3)
    first_pos = summary.find("First")
    third_pos = summary.find("Third")
    assert first_pos < third_pos


def test_textrank_scores():
    engine = SemanticEngine()
    sim_matrix = np.array([
        [1.0, 0.5, 0.0],
        [0.5, 1.0, 0.3],
        [0.0, 0.3, 1.0],
    ])
    scores = engine._textrank_scores(sim_matrix)
    assert scores.shape == (3,)
    assert np.all(scores > 0)


def test_summarize_long_text():
    engine = SemanticEngine()
    sentences = [f"This is sentence number {i} about topic {i % 3}." for i in range(30)]
    text = " ".join(sentences)
    summary = engine.summarize_extractive(text, n_sentences=5)
    assert len(summary) > 0
    assert summary.count(".") >= 4


# ============================================================
# SENTIMENT
# ============================================================

def test_sentiment_positive():
    engine = SemanticEngine()
    sentiment = engine.analyze_sentiment("This is great, excellent and profitable!")
    assert sentiment.compound > 0
    assert sentiment.label == "positive"


def test_sentiment_negative():
    engine = SemanticEngine()
    sentiment = engine.analyze_sentiment("This is poor, bad and a loss.")
    assert sentiment.compound < 0
    assert sentiment.label == "negative"


def test_sentiment_neutral():
    engine = SemanticEngine()
    sentiment = engine.analyze_sentiment("The table has columns and rows.")
    assert sentiment.compound == 0 or abs(sentiment.compound) < 0.05
    assert sentiment.label == "neutral"


def test_sentiment_empty():
    engine = SemanticEngine()
    sentiment = engine.analyze_sentiment("")
    assert sentiment.compound == 0


def test_sentiment_mixed():
    engine = SemanticEngine()
    sentiment = engine.analyze_sentiment("Good progress but some loss.")
    assert -1 <= sentiment.compound <= 1


def test_sentiment_label_property():
    s = SentimentScore(compound=0.5)
    assert s.label == "positive"
    s = SentimentScore(compound=-0.5)
    assert s.label == "negative"
    s = SentimentScore(compound=0.0)
    assert s.label == "neutral"


# ============================================================
# UTILITIES
# ============================================================

def test_tokenize_basic():
    engine = SemanticEngine()
    tokens = engine._tokenize("Hello, World!")
    assert tokens == ["hello", "world"]


def test_tokenize_removes_stopwords():
    engine = SemanticEngine()
    tokens = engine._tokenize("The quick brown fox")
    assert "the" not in tokens
    assert "quick" in tokens


def test_split_sentences():
    engine = SemanticEngine()
    sentences = engine._split_sentences("First. Second! Third? Fourth.")
    assert len(sentences) == 4


def test_split_sentences_empty():
    engine = SemanticEngine()
    assert engine._split_sentences("") == []


def test_detect_language():
    engine = SemanticEngine()
    assert engine._detect_language("Hello world") == "en"
    assert engine._detect_language("") == "en"


# ============================================================
# STATISTICS
# ============================================================

def test_statistics_empty():
    engine = SemanticEngine()
    stats = engine.statistics([])
    assert stats.n_elements == 0


def test_statistics_with_elements():
    engine = SemanticEngine()
    elements = [
        SemanticElement(
            element_id="e1", text="Apple Inc. is a tech company.",
            entities=[
                Entity(text="Apple Inc.", type="ORG"),
                Entity(text="$100", type="MONEY"),
            ],
            topics=["technology"],
        ),
        SemanticElement(
            element_id="e2", text="Microsoft Corp. competes in tech.",
            entities=[Entity(text="Microsoft Corp.", type="ORG")],
            topics=["technology"],
        ),
    ]
    stats = engine.statistics(elements)
    assert stats.n_elements == 2
    assert stats.n_entities == 3
    assert "ORG" in stats.entity_types
    assert "technology" in [t[0] for t in stats.top_topics]


def test_statistics_keyphrase_count():
    engine = SemanticEngine()
    elements = [
        SemanticElement(
            element_id="e1", text="Test",
            keyphrases=[Keyphrase(text="k1", score=0.9), Keyphrase(text="k2", score=0.8)],
        ),
    ]
    stats = engine.statistics(elements)
    assert stats.n_keyphrases == 2


# ============================================================
# DATA CLASSES
# ============================================================

def test_entity_creation():
    e = Entity(text="Apple", type="ORG", confidence=0.9)
    assert e.text == "Apple"
    assert e.confidence == 0.9


def test_entity_to_dict():
    e = Entity(text="X", type="Y", page=5)
    d = e.to_dict()
    assert d["text"] == "X"
    assert d["page"] == 5


def test_keyphrase_creation():
    k = Keyphrase(text="test", score=0.9, frequency=3)
    assert k.text == "test"
    assert k.score == 0.9


def test_topic_creation():
    t = Topic(name="ML", keywords=["neural", "learning"], weight=0.8)
    assert t.name == "ML"
    assert len(t.keywords) == 2


def test_sentiment_score_label():
    s = SentimentScore(compound=0.3)
    assert s.label == "positive"
    s = SentimentScore(compound=-0.3)
    assert s.label == "negative"
    s = SentimentScore(compound=0.0)
    assert s.label == "neutral"


def test_semantic_element_creation():
    e = SemanticElement(element_id="x", text="hello", page=1)
    assert e.element_id == "x"
    assert e.page == 1


# ============================================================
# INTEGRATION
# ============================================================

def test_full_pipeline():
    """Test full semantic processing pipeline."""
    import asyncio
    engine = SemanticEngine()

    text = """
    Apple Inc. reported revenue of $100 billion in Q1 2024, a 15% increase.
    Dr. Smith noted that the company has been growing rapidly.
    Contact: investor@apple.com, https://apple.com
    """

    elements = asyncio.run(engine.compute_embeddings([text]))
    assert len(elements) == 1
    elem = elements[0]

    elem.entities = engine.extract_entities(text, page=1)
    elem.keyphrases = engine.extract_keyphrases(text, top_k=5)
    elem.sentiment = engine.analyze_sentiment(text)

    entity_types = {e.type for e in elem.entities}
    assert EntityType.MONEY in entity_types
    assert EntityType.EMAIL in entity_types
    assert EntityType.URL in entity_types
    assert elem.sentiment.compound > 0
