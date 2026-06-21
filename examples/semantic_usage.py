"""Examples of using the semantic engine."""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

import numpy as np

from src.engines.semantic import (
    SemanticEngine, EmbeddingService,
    EntityType, SemanticElement, Topic
)


def main():
    print("=== Semantic Engine Usage ===")
    # Initialize engine
    engine = SemanticEngine()
    
    # 1. Embeddings
    print("\n1. Computing embeddings...")
    texts = [
        "Apple Inc. reported record revenue of $100 billion in Q1 2024, showing 15% growth.",
        "Dr. Alice Smith and Prof. Bob Jones discussed neural network architectures.",
        "Please contact support@example.com or visit http://example.com/help",
    ]
    elements = asyncio.run(engine.compute_embeddings(texts))
    for el in elements:
        print(f"  ID: {el.element_id}, Token Count: {el.token_count}, Dim: {el.embedding.shape[0]}")
        
    # 2. Entity Extraction
    print("\n2. Extracting named entities...")
    for idx, text in enumerate(texts):
        entities = engine.extract_entities(text)
        print(f"  Text {idx+1}: '{text.strip()}'")
        for ent in entities:
            print(f"    - Found {ent.type}: '{ent.text}' (confidence: {ent.confidence})")
            
    # 3. Topic Modeling & Keyphrases
    print("\n3. Extraction of keyphrases and topic modeling...")
    keyphrases = engine.extract_keyphrases(texts[0], top_k=3)
    print(f"  Keyphrases for Text 1:")
    for kp in keyphrases:
        print(f"    - '{kp.text}' (score: {kp.score:.3f})")
        
    topics = engine.model_topics(texts, n_topics=2)
    print(f"  Extracted Topics:")
    for topic in topics:
        print(f"    - Topic '{topic.name}' (weight: {topic.weight:.3f}): Keywords: {topic.keywords}")
        
    # 4. Similarity Search
    print("\n4. Similarity search...")
    query = "financial revenue and quarterly growth"
    query_emb = engine.encode_query(query)
    candidate_embs = np.stack([el.embedding for el in elements])
    results = engine.find_similar(query_emb, candidate_embs, top_k=2)
    print(f"  Query: '{query}'")
    for idx, score in results:
        print(f"    - Match score: {score:.3f}: '{texts[idx].strip()}'")
        
    # 5. Summarization & Sentiment
    print("\n5. Summarization & Sentiment Analysis...")
    long_text = (
        "Artificial intelligence is transforming industries. "
        "Deep learning models process complex natural language data. "
        "This progress provides major benefits and strong efficiency gains. "
        "However, training massive neural networks involves high risk and costly challenges. "
        "Organizations must balance innovation and concern carefully."
    )
    summary = engine.summarize_extractive(long_text, n_sentences=2)
    print(f"  Extractive Summary: '{summary}'")
    
    sentiment = engine.analyze_sentiment(long_text)
    print(f"  Sentiment Compound: {sentiment.compound:.3f} ({sentiment.label})")
    
    # 6. Overall statistics
    print("\n6. Statistics...")
    for i, el in enumerate(elements):
        el.entities = engine.extract_entities(texts[i])
        el.topics = [t.name for t in topics]
    stats = engine.statistics(elements)
    print(f"  Total elements analyzed: {stats.n_elements}")
    print(f"  Total entities extracted: {stats.n_entities}")
    print(f"  Average tokens per element: {stats.avg_tokens:.1f}")
    print(f"  Entity type distribution: {stats.entity_types}")


if __name__ == "__main__":
    main()
