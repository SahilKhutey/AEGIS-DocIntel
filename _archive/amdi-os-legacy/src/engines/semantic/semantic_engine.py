"""
AEGIS-AMDI-OS — Semantic Engine
==================================
Semantic understanding layer with:
- Dense embeddings (Sentence-BERT compatible)
- Named Entity Recognition (regex + NER)
- Topic Modeling (TF-IDF + clustering)
- Similarity Search (cosine + FAISS-style)
- Summarization (extractive + abstractive ready)

Backends:
- Default: sentence-transformers (BGE, MiniLM, etc.)
- Fallback: hash-based deterministic embeddings for testing
"""
from __future__ import annotations

import hashlib
import logging
import math
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional, Any

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

_TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

DEFAULT_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "this", "that",
    "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "what", "which", "who", "where", "when", "why", "how", "all",
    "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "can", "just", "now",
})


# ============================================================
# DATA CLASSES
# ============================================================

class EntityType:
    """Named entity types."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    DATE = "DATE"
    TIME = "TIME"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    EMAIL = "EMAIL"
    URL = "URL"
    PHONE = "PHONE"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"
    QUANTITY = "QUANTITY"
    OTHER = "OTHER"


@dataclass
class Entity:
    """A named entity."""
    text: str
    type: str
    confidence: float = 1.0
    start_offset: int = 0
    end_offset: int = 0
    page: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "type": self.type,
            "confidence": self.confidence,
            "page": self.page,
        }


@dataclass
class Keyphrase:
    """An extracted keyphrase."""
    text: str
    score: float
    frequency: int = 1
    page: int = 0


@dataclass
class Topic:
    """A topic/theme."""
    name: str
    keywords: list[str]
    weight: float = 1.0
    pages: list[int] = field(default_factory=list)
    document_indices: list[int] = field(default_factory=list)


@dataclass
class SentimentScore:
    """Sentiment analysis result."""
    positive: float = 0.0
    neutral: float = 1.0
    negative: float = 0.0
    compound: float = 0.0

    @property
    def label(self) -> str:
        if self.compound > 0.05:
            return "positive"
        elif self.compound < -0.05:
            return "negative"
        return "neutral"


@dataclass
class SemanticElement:
    """Complete semantic representation."""
    element_id: str
    text: str
    embedding: np.ndarray | None = None
    entities: list[Entity] = field(default_factory=list)
    keyphrases: list[Keyphrase] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    sentiment: SentimentScore = field(default_factory=SentimentScore)
    summary: str = ""
    language: str = "en"
    page: int = 0
    token_count: int = 0


@dataclass
class SemanticStats:
    """Statistics about semantic analysis."""
    n_elements: int = 0
    n_entities: int = 0
    n_topics: int = 0
    n_keyphrases: int = 0
    avg_tokens: float = 0
    avg_entities_per_element: float = 0
    entity_types: dict = field(default_factory=dict)
    top_topics: list = field(default_factory=list)


@dataclass
class SemanticResult:
    """Legacy compatibility result container."""
    element_id: str
    embedding: Optional[np.ndarray] = field(default=None, repr=False)
    entities: list[dict[str, str]] = field(default_factory=list)
    keyphrases: list[str] = field(default_factory=list)
    summary: str = ""
    token_count: int = 0
    sentiment: str = "NEUTRAL"


# ============================================================
# EMBEDDING SERVICE
# ============================================================

class EmbeddingService:
    """
    Text embedding service.

    Uses sentence-transformers when available,
    falls back to hash-based deterministic embeddings.
    """

    DEFAULT_MODEL = "BAAI/bge-large-en-v1.5"
    DEFAULT_DIM = 1024

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        dimension: int = DEFAULT_DIM,
    ):
        self.model_name = model_name
        self.device = device
        self.dimension = dimension
        self._model = None
        self._loaded = False

    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return self._model is not None
        self._loaded = True
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(self.model_name, device=self.device)
                if hasattr(self._model, "get_embedding_dimension"):
                    self.dimension = self._model.get_embedding_dimension()
                else:
                    self.dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Loaded {self.model_name}, dim={self.dimension}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load {self.model_name}: {e}")
        return False

    def encode(self, texts: list[str], normalize: bool = True) -> np.ndarray:
        """
        Encode list of texts to embeddings.

        Returns: (N, D) numpy array
        """
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        if self._ensure_loaded() and self._model is not None:
            try:
                return np.array(
                    self._model.encode(
                        texts,
                        normalize_embeddings=normalize,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                    ),
                    dtype=np.float32,
                )
            except Exception as e:
                logger.warning(f"Encoding failed: {e}. Using hash fallback.")
        return self._hash_embed_batch(texts)

    def encode_query(self, query: str) -> np.ndarray:
        """Encode query with instruction prefix (for BGE models)."""
        if self._ensure_loaded() and self._model is not None:
            instruction = "Represent this sentence for searching relevant passages: "
            try:
                return np.array(
                    self._model.encode(
                        [instruction + query],
                        normalize_embeddings=True,
                        convert_to_numpy=True,
                    )[0],
                    dtype=np.float32,
                )
            except Exception:
                pass
        return self._hash_embed_batch([query])[0]

    def _hash_embed_batch(self, texts: list[str]) -> np.ndarray:
        """Deterministic hash-based fallback embeddings."""
        embeddings = []
        for text in texts:
            embeddings.append(self._hash_embed(text))
        return np.stack(embeddings).astype(np.float32)

    def _hash_embed(self, text: str) -> np.ndarray:
        """Hash-based deterministic embedding."""
        vec = np.zeros(self.dimension, dtype=np.float32)
        text_lower = text.lower().strip()
        tokens = re.findall(r"\w+", text_lower)
        if not tokens:
            return vec
        for i, token in enumerate(tokens):
            for block_idx in range(self.dimension // 8):
                h = hashlib.sha256(f"{token}_{i % 5}_{block_idx}".encode()).digest()
                subvec = np.frombuffer(h[:8], dtype=np.uint8).astype(np.float32) / 255.0
                vec[block_idx * 8:(block_idx + 1) * 8] += subvec
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


# ============================================================
# SEMANTIC ENGINE
# ============================================================

class SemanticEngine:
    """
    Phase 11: Semantic Engine.

    Provides semantic understanding through:
    - Embeddings (dense vector representations)
    - Entity extraction (NER)
    - Keyphrase extraction
    - Topic modeling
    - Sentiment analysis
    - Similarity search
    - Summarization
    """

    # Sentiment lexicon (simple)
    POSITIVE_WORDS = frozenset({
        "good", "great", "excellent", "positive", "success", "successful",
        "profit", "growth", "increase", "improved", "best", "win", "won",
        "achievement", "outstanding", "strong", "high", "up", "rise",
    })
    NEGATIVE_WORDS = frozenset({
        "bad", "poor", "negative", "loss", "decrease", "decline", "failed",
        "worst", "weak", "low", "down", "fall", "fell", "drop", "risk",
        "concern", "issue", "problem", "challenge", "difficult",
    })

    def __init__(
        self,
        embedder: EmbeddingService | None = None,
        remove_stopwords: bool = True,
        top_k_keyphrases: int = 8,
        summary_sentences: int = 3,
    ):
        self.embedder = embedder or EmbeddingService()
        self.remove_stopwords = remove_stopwords
        self.top_k_keyphrases = top_k_keyphrases
        self.summary_sentences = summary_sentences

        # IDF table built by fit()
        self._idf_table: dict[str, float] = {}
        self._corpus_size: int = 0

    # ============================================================
    # 1. EMBEDDINGS
    # ============================================================

    async def compute_embeddings(
        self, texts: list[str], elements: list | None = None
    ) -> list[SemanticElement]:
        """
        Compute embeddings for all texts.

        Args:
            texts: List of text strings
            elements: Optional list of source elements

        Returns: List of SemanticElement with embeddings
        """
        if not texts:
            return []
        embeddings = self.embedder.encode(texts)
        results = []
        for i, text in enumerate(texts):
            element_id = elements[i].element_id if elements and i < len(elements) else f"sem-{i}"
            page = elements[i].page if elements and i < len(elements) else 0
            results.append(SemanticElement(
                element_id=element_id,
                text=text,
                embedding=embeddings[i],
                page=page,
                token_count=len(self._tokenize(text)),
                language=self._detect_language(text),
            ))
        return results

    def encode_text(self, text: str) -> np.ndarray:
        """Encode single text."""
        return self.embedder.encode([text])[0]

    def encode_query(self, query: str) -> np.ndarray:
        """Encode query for retrieval."""
        return self.embedder.encode_query(query)

    # ============================================================
    # 2. ENTITY EXTRACTION
    # ============================================================

    def extract_entities(self, text: str, page: int = 0) -> list[Entity]:
        """
        Extract named entities using regex patterns.

        Detects: PERSON, ORG, MONEY, PERCENT, DATE, EMAIL, URL, PHONE.
        """
        if not text:
            return []
        entities = []
        # MONEY
        for m in re.finditer(r"[\$€£¥₹]\s?[\d,]+(?:\.\d+)?\s?(?:K|M|B|T|million|billion|thousand)?",
                             text, re.IGNORECASE):
            entities.append(Entity(
                text=m.group(), type=EntityType.MONEY,
                confidence=0.95, start_offset=m.start(), end_offset=m.end(),
                page=page,
            ))
        # PERCENT
        for m in re.finditer(r"\b\d+(?:\.\d+)?\s?%", text):
            entities.append(Entity(
                text=m.group(), type=EntityType.PERCENT,
                confidence=0.95, start_offset=m.start(), end_offset=m.end(),
                page=page,
            ))
        # DATE (multiple formats)
        date_patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",              # 2024-01-15
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",       # 1/15/2024
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b",
            r"\bQ[1-4]\s+\d{4}\b",                  # Q1 2024
            r"\b(?:FY)?\d{4}\b",                     # FY2024
        ]
        for pattern in date_patterns:
            for m in re.finditer(pattern, text):
                entities.append(Entity(
                    text=m.group(), type=EntityType.DATE,
                    confidence=0.9, start_offset=m.start(), end_offset=m.end(),
                    page=page,
                ))
        # EMAIL
        for m in re.finditer(r"\b[\w.-]+@[\w.-]+\.\w+\b", text):
            entities.append(Entity(
                text=m.group(), type=EntityType.EMAIL,
                confidence=0.99, start_offset=m.start(), end_offset=m.end(),
                page=page,
            ))
        # URL
        for m in re.finditer(r"https?://\S+", text):
            entities.append(Entity(
                text=m.group(), type=EntityType.URL,
                confidence=0.99, start_offset=m.start(), end_offset=m.end(),
                page=page,
            ))
        # PHONE
        for m in re.finditer(r"\b\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b", text):
            entities.append(Entity(
                text=m.group(), type=EntityType.PHONE,
                confidence=0.85, start_offset=m.start(), end_offset=m.end(),
                page=page,
            ))
        # ORGANIZATION (uppercase acronyms 2+ letters)
        for m in re.finditer(r"\b[A-Z]{2,}(?:\s+[A-Z][a-z]+)?\b", text):
            if len(m.group()) >= 2:
                entities.append(Entity(
                    text=m.group(), type=EntityType.ORGANIZATION,
                    confidence=0.7, start_offset=m.start(), end_offset=m.end(),
                    page=page,
                ))
        # PERSON (Title Case phrases)
        for m in re.finditer(r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text):
            entities.append(Entity(
                text=m.group(), type=EntityType.PERSON,
                confidence=0.9, start_offset=m.start(), end_offset=m.end(),
                page=page,
            ))
        # PERSON (heuristic: 2-3 capitalized words)
        for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b", text):
            if len(m.group()) > 5 and " " in m.group():
                entities.append(Entity(
                    text=m.group(), type=EntityType.PERSON,
                    confidence=0.6, start_offset=m.start(), end_offset=m.end(),
                    page=page,
                ))
        # Deduplicate
        seen = set()
        unique = []
        for e in entities:
            key = (e.text.lower(), e.type)
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique

    # ============================================================
    # 3. TOPIC MODELING
    # ============================================================

    def extract_keyphrases(self, text: str, top_k: int = 10) -> list[Keyphrase]:
        """
        Extract keyphrases using TF-IDF scoring.
        """
        if not text:
            return []
        tokens = self._tokenize(text)
        if not tokens:
            return []
        unigrams = tokens
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        tf = Counter(tokens)
        scores: dict[str, float] = {}
        for token in set(unigrams):
            if token in DEFAULT_STOPWORDS or len(token) < 3:
                continue
            scores[token] = tf[token] * self._idf(token)
        for bigram in set(bigrams):
            words = bigram.split()
            if any(w in DEFAULT_STOPWORDS for w in words):
                continue
            # Bigrams get a 1.5x boost
            scores[bigram] = tf.get(words[0], 0) * tf.get(words[1], 0) * 1.5
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            Keyphrase(
                text=phrase, score=float(score),
                frequency=tf.get(phrase.split()[0], 1) if " " in phrase else tf.get(phrase, 1)
            )
            for phrase, score in top
        ]

    def _idf(self, term: str) -> float:
        """Compute IDF lookup."""
        return self._idf_table.get(term, 1.0)

    def model_topics(
        self,
        documents: list[str],
        n_topics: int = 5,
    ) -> list[Topic]:
        """
        Simple topic modeling via TF-IDF + SVD.
        """
        if not documents or n_topics <= 0:
            return []
        vocab, tfidf_matrix = self._build_tfidf(documents)
        if len(vocab) == 0 or tfidf_matrix.shape[0] == 0:
            return []
        n_components = min(n_topics, tfidf_matrix.shape[1], tfidf_matrix.shape[0])
        try:
            U, S, Vt = np.linalg.svd(tfidf_matrix, full_matrices=False)
        except Exception:
            return []
        topics = []
        for k in range(n_components):
            top_indices = np.argsort(np.abs(Vt[k]))[::-1][:5]
            topic_words = [vocab[i] for i in top_indices if i < len(vocab)]
            if topic_words:
                name = " ".join(topic_words[:2]).title()
                topics.append(Topic(
                    name=name,
                    keywords=topic_words,
                    weight=float(S[k]) / max(1.0, float(S[0])),
                    document_indices=list(range(len(documents))),
                ))
        return topics

    def _build_tfidf(self, documents: list[str]) -> tuple[list[str], np.ndarray]:
        """Build TF-IDF matrix from documents."""
        docs_tokens = [self._tokenize(doc) for doc in documents]
        vocab_set = set()
        for tokens in docs_tokens:
            vocab_set.update(tokens)
        vocab = sorted(vocab_set)
        vocab_idx = {w: i for i, w in enumerate(vocab)}
        n_docs = len(documents)
        n_vocab = len(vocab)
        if n_vocab == 0:
            return [], np.zeros((0, 0))
        tf = np.zeros((n_docs, n_vocab), dtype=np.float32)
        for i, tokens in enumerate(docs_tokens):
            for token in tokens:
                if token in vocab_idx:
                    tf[i, vocab_idx[token]] += 1
        df = (tf > 0).sum(axis=0)
        idf = np.log((n_docs + 1) / (df + 1)) + 1
        tfidf = tf * idf
        norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
        norms[norms == 0] = 1
        tfidf = tfidf / norms
        return vocab, tfidf

    # ============================================================
    # 4. SIMILARITY SEARCH
    # ============================================================

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def cosine_similarity_matrix(self, vectors: np.ndarray) -> np.ndarray:
        """Compute NxN cosine similarity matrix."""
        if vectors.shape[0] == 0:
            return np.zeros((0, 0))
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normalized = vectors / norms
        return normalized @ normalized.T

    def euclidean_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Euclidean distance."""
        return float(np.linalg.norm(a - b))

    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[tuple[int, float]]:
        """
        Find top-k most similar candidates to query.
        """
        if candidate_embeddings.shape[0] == 0:
            return []
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        q_norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
        q_norm[q_norm == 0] = 1
        q_normed = query_embedding / q_norm
        c_norm = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
        c_norm[c_norm == 0] = 1
        c_normed = candidate_embeddings / c_norm
        sims = (c_normed @ q_normed.T).flatten()
        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score >= threshold:
                results.append((int(idx), score))
        return results

    def find_similar_text(
        self,
        query: str,
        candidates: list[str],
        top_k: int = 5,
    ) -> list[tuple[int, float, str]]:
        """Find similar texts to a query."""
        query_emb = self.encode_query(query)
        candidate_embs = self.embedder.encode(candidates)
        results = self.find_similar(query_emb, candidate_embs, top_k=top_k)
        return [(idx, score, candidates[idx]) for idx, score in results]

    # ============================================================
    # 5. SUMMARIZATION
    # ============================================================

    def summarize_extractive(
        self, text: str, n_sentences: int = 3, page: int = 0
    ) -> str:
        """
        Extractive summarization using TextRank-like PageRank algorithm.
        """
        if not text:
            return ""
        sentences = self._split_sentences(text)
        # Filter out extremely short sentences
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if len(sentences) <= n_sentences:
            return " ".join(sentences)
        if len(sentences) > 50:
            return self._summarize_tfidf(text, n_sentences)
        try:
            embeddings = self.embedder.encode(sentences)
            sim_matrix = self.cosine_similarity_matrix(embeddings)
            scores = self._textrank_scores(sim_matrix)
            top_indices = sorted(np.argsort(scores)[::-1][:n_sentences])
            return " ".join(sentences[i] for i in top_indices)
        except Exception:
            return self._summarize_tfidf(text, n_sentences)

    def _textrank_scores(self, sim_matrix: np.ndarray, damping: float = 0.85, n_iter: int = 50) -> np.ndarray:
        n = sim_matrix.shape[0]
        if n == 0:
            return np.zeros(0)
        row_sums = sim_matrix.sum(axis=1)
        row_sums[row_sums == 0] = 1
        normalized = sim_matrix / row_sums[:, np.newaxis]
        scores = np.ones(n) / n
        for _ in range(n_iter):
            scores = (1 - damping) / n + damping * normalized.T @ scores
        return scores

    def _summarize_tfidf(self, text: str, n_sentences: int) -> str:
        sentences = self._split_sentences(text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if len(sentences) <= n_sentences:
            return " ".join(sentences)
        vocab, tfidf = self._build_tfidf(sentences)
        if tfidf.size == 0:
            return " ".join(sentences[:n_sentences])
        scores = tfidf.sum(axis=1)
        top_indices = sorted(np.argsort(scores)[::-1][:n_sentences])
        return " ".join(sentences[i] for i in top_indices)

    async def summarize_abstractive(
        self, text: str, n_sentences: int = 3, llm_call=None
    ) -> str:
        """
        Abstractive summarization via LLM callback.
        """
        if llm_call is None:
            return self.summarize_extractive(text, n_sentences)
        try:
            prompt = f"Summarize the following text in {n_sentences} sentences:\n\n{text[:3000]}"
            return await llm_call(prompt)
        except Exception:
            return self.summarize_extractive(text, n_sentences)

    # ============================================================
    # SENTIMENT
    # ============================================================

    def analyze_sentiment(self, text: str) -> SentimentScore:
        """Simple lexicon-based sentiment analysis."""
        if not text:
            return SentimentScore()
        tokens = self._tokenize(text)
        if not tokens:
            return SentimentScore()
        pos_count = sum(1 for t in tokens if t in self.POSITIVE_WORDS)
        neg_count = sum(1 for t in tokens if t in self.NEGATIVE_WORDS)
        total = pos_count + neg_count
        if total == 0:
            return SentimentScore()
        positive = pos_count / len(tokens)
        negative = neg_count / len(tokens)
        neutral = max(0.0, 1.0 - positive - negative)
        compound = (pos_count - neg_count) / max(1.0, total)
        return SentimentScore(
            positive=positive,
            negative=negative,
            neutral=neutral,
            compound=compound,
        )

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase words."""
        if not text:
            return []
        tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
        if self.remove_stopwords:
            tokens = [t for t in tokens if t not in DEFAULT_STOPWORDS]
        return tokens

    def _split_sentences(self, text: str) -> list[str]:
        if not text:
            return []
        return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]

    def _detect_language(self, text: str) -> str:
        if not text:
            return "en"
        try:
            from langdetect import detect
            return detect(text)
        except ImportError:
            return "en"

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self, elements: list[SemanticElement] | None = None) -> SemanticStats:
        """Compute statistics."""
        if not elements:
            return SemanticStats()
        entity_types: Counter = Counter()
        all_topics: list = []
        for e in elements:
            for ent in e.entities:
                entity_types[ent.type] += 1
            all_topics.extend(e.topics)
        topic_counts = Counter(all_topics)
        return SemanticStats(
            n_elements=len(elements),
            n_entities=sum(len(e.entities) for e in elements),
            n_topics=len(set(all_topics)),
            n_keyphrases=sum(len(e.keyphrases) for e in elements),
            avg_tokens=sum(e.token_count for e in elements) / max(1, len(elements)),
            avg_entities_per_element=sum(len(e.entities) for e in elements) / max(1, len(elements)),
            entity_types=dict(entity_types),
            top_topics=topic_counts.most_common(5),
        )

    # ============================================================
    # BACKWARDS COMPATIBILITY WRAPPERS
    # ============================================================

    def fit(self, elements: list[Any]) -> SemanticEngine:
        """Build the IDF table from the supplied corpus of elements."""
        logger.info("Fitting IDF on %d elements ...", len(elements))
        doc_freq: dict[str, int] = {}
        n = len(elements)

        for el in elements:
            content = getattr(el, "content", "") or ""
            tokens = self._tokenize(content)
            for tok in set(tokens):
                doc_freq[tok] = doc_freq.get(tok, 0) + 1

        self._corpus_size = max(n, 1)
        self._idf_table = {
            tok: math.log((self._corpus_size + 1) / (df + 1)) + 1.0
            for tok, df in doc_freq.items()
        }
        logger.info("IDF table built: %d unique terms.", len(self._idf_table))
        return self

    def process(self, elements: list[Any]) -> list[SemanticResult]:
        """Legacy entrypoint routing."""
        if not elements:
            return []

        logger.info("SemanticEngine.process(): %d elements.", len(elements))
        texts = [getattr(el, "content", "") or "" for el in elements]
        embeddings = self.embedder.encode(texts)

        results = []
        for idx, el in enumerate(elements):
            content = getattr(el, "content", "") or ""
            emb = embeddings[idx]

            # Extract via standard functions
            entities_dt = self.extract_entities(content, page=getattr(el, "page", 0))
            keyphrases_dt = self.extract_keyphrases(content, top_k=self.top_k_keyphrases)
            summary = self.summarize_extractive(content, n_sentences=self.summary_sentences)
            sentiment_score = self.analyze_sentiment(content)

            # Map to legacy forms
            entities_legacy = [{"type": ent.type, "value": ent.text} for ent in entities_dt]
            keyphrases_legacy = [kp.text for kp in keyphrases_dt]
            sentiment_legacy = sentiment_score.label.upper()

            # Write back to element attributes
            if hasattr(el, "embedding"):
                el.embedding = emb
            if hasattr(el, "entities"):
                # Also map tuple list for GeometricElement compatibility
                el.entities = [(ent.type, ent.text) for ent in entities_dt]
            if hasattr(el, "keyphrases"):
                el.keyphrases = keyphrases_legacy
            if hasattr(el, "summary"):
                el.summary = summary

            result = SemanticResult(
                element_id=getattr(el, "element_id", f"sem-{idx}"),
                embedding=emb,
                entities=entities_legacy,
                keyphrases=keyphrases_legacy,
                summary=summary,
                token_count=len(self._tokenize(content)),
                sentiment=sentiment_legacy,
            )
            results.append(result)

        logger.info("SemanticEngine.process() complete: %d results.", len(results))
        return results

    def analyze(self, elements: list[Any]) -> None:
        """Call process."""
        self.process(elements)

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Compute query embedding vector."""
        return self.embedder.encode_query(query)

    def score(self, *args, **kwargs) -> Any:
        """Supports:
        - score(query_emb, element) -> float
        - score(query, elements, query_emb) -> dict[str, float]
        """
        if len(args) >= 2 and isinstance(args[1], list):
            query, elements = args[0], args[1]
            q_emb = args[2] if len(args) > 2 else None
            if q_emb is None:
                q_emb = self.embed_query(query)
            return {el.element_id: self._score_single(q_emb, el) for el in elements}
        else:
            query_emb = args[0] if len(args) > 0 else None
            element = args[1] if len(args) > 1 else None
            return self._score_single(query_emb, element)

    def _score_single(self, query_emb: Optional[np.ndarray], element: Any) -> float:
        if element is None:
            return 0.0
        el_emb = getattr(element, "embedding", None)

        if query_emb is not None and el_emb is not None:
            return float(self.cosine_similarity(query_emb, el_emb))

        # Lexical fallback Jaccard
        query_text = str(query_emb) if query_emb is not None else ""
        query_tokens = set(self._tokenize(query_text))
        el_tokens = set(self._tokenize(getattr(element, "content", "") or ""))
        if not query_tokens and not el_tokens:
            return 0.0
        intersection = len(query_tokens & el_tokens)
        union = len(query_tokens | el_tokens)
        return intersection / union if union > 0 else 0.0
