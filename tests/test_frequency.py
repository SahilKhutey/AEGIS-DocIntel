"""Tests for the frequency engine."""
import math
import pytest
import numpy as np
from pathlib import Path
import sys

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.core.geometric_element import GeometricElement, ElementType
from src.core.normalized_document import BoundingBox
from src.engines.frequency.frequency_engine import (
    FrequencyEngine, FrequencyStats,
    shannon_entropy, entropy_from_counter, information_density,
    jensen_shannon_divergence, tfidf_score, tokenize,
    DEFAULT_STOPWORDS,
)


# ============================================================
# HELPERS
# ============================================================

def make_element(
    content: str = "test content",
    page: int = 1,
    etype: ElementType = ElementType.TEXT,
    x0: float = 0.1, y0: float = 0.1,
    x1: float = 0.5, y1: float = 0.3,
    section: str = None,
    frequency: int = 1,
    recurrence_id: str = None,
) -> GeometricElement:
    """Factory for creating test elements."""
    return GeometricElement(
        content=content,
        page=page,
        type=etype,
        bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
        section=section,
        frequency=frequency,
        recurrence_id=recurrence_id,
    )


# ============================================================
# TOKENIZATION
# ============================================================

def test_tokenize_basic():
    tokens = tokenize("Hello World")
    assert tokens == ["hello", "world"]


def test_tokenize_empty():
    assert tokenize("") == []
    assert tokenize(None) == []


def test_tokenize_punctuation():
    tokens = tokenize("Hello, World! How are you?")
    assert tokens == ["hello", "world", "how", "are", "you"]


def test_tokenize_unicode():
    tokens = tokenize("Héllo Wörld café")
    assert "héllo" in tokens
    assert "wörld" in tokens


def test_tokenize_remove_stopwords():
    tokens = tokenize("the quick brown fox", remove_stopwords=True)
    assert "the" not in tokens
    assert "quick" in tokens
    assert "brown" in tokens


def test_tokenize_no_stopwords():
    tokens = tokenize("the quick brown fox", remove_stopwords=False)
    assert "the" in tokens


# ============================================================
# STANDALONE FUNCTIONS
# ============================================================

def test_shannon_entropy_empty():
    assert shannon_entropy([]) == 0


def test_shannon_entropy_single_token():
    # Single token: 0 entropy (no uncertainty)
    assert shannon_entropy(["hello"]) == 0


def test_shannon_entropy_uniform():
    # 4 equally likely tokens: log2(4) = 2
    tokens = ["a", "b", "c", "d"] * 10
    h = shannon_entropy(tokens)
    assert h == pytest.approx(2.0, abs=0.01)


def test_shannon_entropy_skewed():
    # Skewed distribution: lower entropy
    tokens = ["a"] * 99 + ["b"]
    h = shannon_entropy(tokens)
    assert 0 < h < 1


def test_shannon_entropy_bounds():
    """Theorem 13.1: 0 <= H(X) <= log|X|"""
    import random
    random.seed(42)
    for _ in range(10):
        tokens = [str(random.randint(0, 10)) for _ in range(100)]
        h = shannon_entropy(tokens)
        n_unique = len(set(tokens))
        assert 0 <= h <= math.log2(n_unique) + 0.01


def test_entropy_from_counter():
    counter = {"a": 5, "b": 5}
    h = entropy_from_counter(counter)
    # Uniform 50/50: log2(2) = 1
    assert h == pytest.approx(1.0, abs=0.01)


def test_information_density():
    assert information_density(2.0, 0.5) == 4.0
    assert information_density(1.0, 0.0) == 0.0  # Zero area → 0


def test_jensen_shannon_divergence_identical():
    p = [0.5, 0.5]
    q = [0.5, 0.5]
    assert jensen_shannon_divergence(p, q) < 1e-10


def test_jensen_shannon_divergence_different():
    p = [1.0, 0.0]
    q = [0.0, 1.0]
    jsd = jensen_shannon_divergence(p, q)
    assert jsd == pytest.approx(1.0, abs=1e-5)  # Maximum divergence


def test_tfidf_score():
    # TF=10, DF=5, N=100
    score = tfidf_score(10, 5, 100)
    expected = 10 * math.log(100 / 5)
    assert score == pytest.approx(expected)


# ============================================================
# 1. WORD FREQUENCY
# ============================================================

def test_term_frequency():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple banana apple"),
        make_element(content="apple cherry"),
    ]
    engine.fit(elements)
    assert engine.term_frequency("apple") == 3
    assert engine.term_frequency("banana") == 1
    assert engine.term_frequency("cherry") == 1
    assert engine.term_frequency("missing") == 0


def test_term_frequency_case_insensitive():
    engine = FrequencyEngine()
    engine.fit([make_element(content="Apple APPLE apple")])
    assert engine.term_frequency("apple") == 3
    assert engine.term_frequency("APPLE") == 3


def test_document_frequency():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple banana"),
        make_element(content="apple cherry"),
        make_element(content="apple date"),
    ]
    engine.fit(elements)
    assert engine.document_frequency("apple") == 3  # In all 3
    assert engine.document_frequency("banana") == 1
    assert engine.document_frequency("cherry") == 1


def test_inverse_document_frequency():
    engine = FrequencyEngine()
    # 10 elements
    elements = [make_element(content=f"word{i}") for i in range(10)]
    engine.fit(elements)
    # Each word appears in only 1 element → high IDF
    idf = engine.inverse_document_frequency("word0")
    assert idf > 0


def test_tfidf():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple banana apple"),
        make_element(content="apple cherry"),
    ]
    engine.fit(elements)
    score = engine.tfidf("apple", elements[0])
    assert score > 0


def test_top_terms_by_tf():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple apple apple banana banana cherry"),
        make_element(content="apple"),
    ]
    engine.fit(elements)
    top = engine.top_terms(n=3, by="tf")
    assert top[0][0] == "apple"
    assert top[0][1] == 4


def test_top_terms_by_idf():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple banana"),
        make_element(content="cherry date"),
        make_element(content="apple"),
        make_element(content="banana"),
    ]
    engine.fit(elements)
    top = engine.top_terms(n=3, by="idf")
    assert len(top) > 0


# ============================================================
# 2. SECTION FREQUENCY
# ============================================================

def test_section_frequency():
    engine = FrequencyEngine()
    elements = [
        make_element(content="a", section="intro"),
        make_element(content="b", section="intro"),
        make_element(content="c", section="intro"),
        make_element(content="d", section="results"),
    ]
    engine.fit(elements)
    assert engine.section_frequency("intro") == 3
    assert engine.section_frequency("results") == 1
    assert engine.section_frequency("missing") == 0


def test_section_terms():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple apple banana", section="intro"),
        make_element(content="apple cherry", section="intro"),
        make_element(content="date fig", section="results"),
    ]
    engine.fit(elements)
    intro_terms = engine.section_terms("intro")
    assert intro_terms[0] == ("apple", 3)
    assert intro_terms[1] == ("banana", 1)


def test_section_entropy():
    engine = FrequencyEngine()
    # Diverse section: high entropy
    elements1 = [make_element(content=f"word{i}", section="diverse") for i in range(10)]
    # Repetitive section: low entropy
    elements2 = [make_element(content="same same same", section="repetitive")]
    engine.fit(elements1 + elements2)
    h1 = engine.section_entropy("diverse")
    h2 = engine.section_entropy("repetitive")
    assert h1 > h2


def test_all_sections():
    engine = FrequencyEngine()
    elements = [
        make_element(section="intro"),
        make_element(section="intro"),
        make_element(section="results"),
    ]
    engine.fit(elements)
    sections = engine.all_sections()
    assert "intro" in sections
    assert "results" in sections


# ============================================================
# 3. ENTITY FREQUENCY
# ============================================================

def test_entity_extraction():
    engine = FrequencyEngine()
    elements = [
        make_element(content="Apple Inc. is a technology company."),
        make_element(content="Microsoft Corp. and Apple Inc. compete."),
    ]
    engine.fit(elements)
    entities = engine.top_entities(n=10)
    entity_names = [e[0] for e in entities]
    assert "Apple Inc" in entity_names
    assert "Microsoft Corp" in entity_names


def test_top_entities():
    engine = FrequencyEngine()
    elements = [
        make_element(content="Apple and Apple and Apple"),
        make_element(content="Apple and Microsoft"),
        make_element(content="Microsoft and Microsoft"),
    ]
    engine.fit(elements)
    top = engine.top_entities(n=2)
    assert top[0][0] == "Apple"
    assert top[0][1] == 4


def test_rare_entities():
    engine = FrequencyEngine()
    elements = [
        make_element(content="Common and Word and Apple"),
        make_element(content="Microsoft"),
        make_element(content="Unique Entity"),
    ]
    engine.fit(elements)
    rare = engine.rare_entities(n=5)
    rare_names = [r[0] for r in rare]
    assert "Unique Entity" in rare_names


# ============================================================
# 4. DENSITY ANALYSIS
# ============================================================

def test_information_density_basic():
    engine = FrequencyEngine()
    elements = [make_element(content="apple banana cherry")]
    engine.fit(elements)
    e = elements[0]
    density = engine.information_density(e)
    assert density > 0


def test_information_density_zero_area():
    engine = FrequencyEngine()
    elements = [make_element(content="test", x1=0.1, y1=0.1)]  # Zero area
    engine.fit(elements)
    density = engine.information_density(elements[0])
    assert density == 0.0


def test_information_density_inverse_area():
    """Smaller area = higher density (for same entropy)."""
    engine = FrequencyEngine()
    elements = [
        make_element(content="same content here", x0=0, y0=0, x1=0.5, y1=0.5),
        make_element(content="same content here", x0=0, y0=0, x1=0.1, y1=0.1),
    ]
    engine.fit(elements)
    d_big = engine.information_density(elements[0])
    d_small = engine.information_density(elements[1])
    assert d_small > d_big


def test_density_percentile():
    engine = FrequencyEngine()
    elements = [
        make_element(content="a", x0=0, y0=0, x1=0.1, y1=0.1),
        make_element(content="b", x0=0, y0=0, x1=0.5, y1=0.5),
        make_element(content="c", x0=0, y0=0, x1=0.3, y1=0.3),
    ]
    engine.fit(elements)
    densities = [(e, engine.information_density(e)) for e in elements]
    densities.sort(key=lambda x: x[1], reverse=True)
    top = densities[0][0]
    assert top.content == "a"


def test_highest_density_elements():
    engine = FrequencyEngine()
    elements = [
        make_element(content="common word", x0=0, y0=0, x1=0.5, y1=0.5),
        make_element(content="rare unique", x0=0, y0=0, x1=0.05, y1=0.05),
    ]
    engine.fit(elements)
    top_density = engine.highest_density_elements(elements, n=1)
    assert top_density[0][0].content == "rare unique"


# ============================================================
# 5. ENTROPY ANALYSIS
# ============================================================

def test_element_entropy():
    engine = FrequencyEngine()
    elements = [make_element(content="apple apple apple banana")]
    engine.fit(elements)
    h = engine.element_entropy(elements[0])
    assert 0 < h < 2


def test_element_entropy_diverse():
    engine = FrequencyEngine()
    elements = [make_element(content="apple banana cherry date elephant")]
    engine.fit(elements)
    h = engine.element_entropy(elements[0])
    assert h > 0.5


def test_document_entropy():
    engine = FrequencyEngine()
    elements = [
        make_element(content="a b c d"),
        make_element(content="a b e f"),
    ]
    engine.fit(elements)
    h = engine.document_entropy()
    assert h > 0


def test_conditional_entropy():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple banana", section="intro"),
        make_element(content="cherry date", section="results"),
    ]
    engine.fit(elements)
    h = engine.conditional_entropy("intro")
    assert h >= 0


def test_mean_element_entropy():
    engine = FrequencyEngine()
    elements = [
        make_element(content="apple banana"),
        make_element(content="cherry date"),
    ]
    engine.fit(elements)
    h = engine.mean_element_entropy(elements)
    assert h > 0


# ============================================================
# 6. IMPORTANCE RANKING
# ============================================================

def test_type_baseline():
    engine = FrequencyEngine()
    assert engine.type_baseline(ElementType.TABLE) == 1.8
    assert engine.type_baseline(ElementType.HEADING) == 1.5
    assert engine.type_baseline(ElementType.FOOTER) == 0.1
    assert engine.type_baseline(ElementType.TEXT) == 1.0


def test_inverse_frequency_weight():
    engine = FrequencyEngine()
    elements = [make_element(content="rare")] * 1
    elements += [make_element(content="common")] * 10
    engine.fit(elements)
    w_rare = engine.inverse_frequency_weight("rare")
    w_common = engine.inverse_frequency_weight("common")
    assert w_rare > w_common


def test_inverse_frequency_bounds():
    """Theorem 12.2: I_f ∈ (0, 1]"""
    engine = FrequencyEngine()
    elements = [make_element(content="test")]
    engine.fit(elements)
    for content in ["test", "x", "completely_unique_token_xyz"]:
        w = engine.inverse_frequency_weight(content)
        assert 0 < w <= 1


def test_inverse_frequency_monotonicity():
    """Theorem 12.1: Strictly decreasing in frequency."""
    engine = FrequencyEngine()
    elements = []
    for _ in range(10):
        elements.append(make_element(content="common"))
    elements.append(make_element(content="rare"))
    engine.fit(elements)
    w_rare = engine.inverse_frequency_weight("rare")
    w_common = engine.inverse_frequency_weight("common")
    assert w_rare > w_common


def test_composite_importance_basic():
    engine = FrequencyEngine()
    elements = [make_element(content="important conclusion")]
    engine.fit(elements)
    e = elements[0]
    importance = engine.composite_importance(e)
    assert 0 <= importance <= 1.0


def test_assign_weights():
    engine = FrequencyEngine()
    elements = [
        make_element(content="Page 1"),
        make_element(content="Page 2"),
        make_element(content="Page 3"),
        make_element(content="Total revenue $1B"),
    ]
    engine.assign_weights(elements)
    for e in elements:
        assert e.importance_weight >= 0


def test_assign_weights_recurrence_penalty():
    """Recurrent elements should have reduced weight."""
    engine = FrequencyEngine()
    elements = [
        make_element(content="Header", frequency=10, recurrence_id="r1"),
        make_element(content="Important text", frequency=1),
    ]
    engine.assign_weights(elements)
    assert elements[1].importance_weight > elements[0].importance_weight


def test_rank_by_importance():
    engine = FrequencyEngine()
    elements = [
        make_element(content="Page 1"),
        make_element(content="Conclusion: critical result"),
        make_element(content="Page 2"),
    ]
    engine.assign_weights(elements)
    ranked = engine.rank_by_importance(elements)
    contents = [e.content[:15] for e in ranked]
    assert any("Conclusion" in c for c in contents[:2])


def test_top_k_important():
    engine = FrequencyEngine()
    elements = [make_element(content=f"text {i}") for i in range(20)]
    engine.assign_weights(elements)
    top5 = engine.top_k_important(elements, k=5)
    assert len(top5) == 5


def test_percentile_rank():
    engine = FrequencyEngine()
    elements = [make_element(content=f"text_{i}") for i in range(10)]
    engine.assign_weights(elements)
    pct = engine.percentile_rank(elements[0], elements)
    assert 0 <= pct <= 1
