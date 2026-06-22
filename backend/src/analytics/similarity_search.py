"""
AMDI-OS Advanced Analytics: Similarity Search
=============================================

Computes cosine similarity, calculates corpus and cluster centroids, 
and retrieves top-k similar documents based on high-dimensional embeddings.
"""

from typing import Dict, List, Tuple, Optional, Union
import numpy as np


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Computes the cosine similarity between two vectors.
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def compute_centroid(embeddings: List[Union[List[float], np.ndarray]]) -> List[float]:
    """
    Calculates the average (centroid) vector from a list of embeddings.
    """
    if not embeddings:
        raise ValueError("Cannot compute centroid of an empty list of embeddings.")
    
    arr = np.array(embeddings)
    centroid = np.mean(arr, axis=0)
    return centroid.tolist()


class SimilaritySearcher:
    """
    Manages document embeddings and performs similarity searches across the corpus.
    """
    def __init__(self):
        # Maps doc_id -> numpy array representation of the embedding
        self.corpus: Dict[str, np.ndarray] = {}
        # Maps doc_id -> metadata dictionary
        self.metadata: Dict[str, dict] = {}

    def add_document(self, doc_id: str, embedding: Union[List[float], np.ndarray], meta: Optional[dict] = None) -> None:
        """
        Adds or updates a document in the search corpus.
        """
        self.corpus[doc_id] = np.array(embedding, dtype=np.float32)
        self.metadata[doc_id] = meta or {}

    def remove_document(self, doc_id: str) -> bool:
        """
        Removes a document from the corpus.
        """
        if doc_id in self.corpus:
            del self.corpus[doc_id]
            del self.metadata[doc_id]
            return True
        return False

    def search_by_vector(self, query_vector: Union[List[float], np.ndarray], top_k: int = 5) -> List[Tuple[str, float, dict]]:
        """
        Searches the corpus using a raw query vector and returns top_k results.
        Returns:
            List of tuples (doc_id, similarity_score, metadata)
        """
        if not self.corpus:
            return []
        
        q_vec = np.array(query_vector, dtype=np.float32)
        results = []
        
        for doc_id, doc_vec in self.corpus.items():
            score = cosine_similarity(q_vec, doc_vec)
            results.append((doc_id, score, self.metadata[doc_id]))
            
        # Sort by similarity score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def search_by_document(self, doc_id: str, top_k: int = 5) -> List[Tuple[str, float, dict]]:
        """
        Finds the most similar documents to an existing document in the corpus.
        """
        if doc_id not in self.corpus:
            raise KeyError(f"Document with ID '{doc_id}' not found in the corpus.")
            
        q_vec = self.corpus[doc_id]
        # Run search and exclude the document itself
        all_results = self.search_by_vector(q_vec, top_k=top_k + 1)
        return [res for res in all_results if res[0] != doc_id][:top_k]

    def find_clusters(self, threshold: float = 0.8) -> List[List[str]]:
        """
        Groups documents whose similarity exceeds the given threshold.
        Simple single-linkage agglomerative clustering approach.
        """
        doc_ids = list(self.corpus.keys())
        if not doc_ids:
            return []
            
        n = len(doc_ids)
        visited = set()
        clusters = []
        
        # Build adjacency matrix
        adj = {d: [] for d in doc_ids}
        for i in range(n):
            for j in range(i + 1, n):
                d1, d2 = doc_ids[i], doc_ids[j]
                sim = cosine_similarity(self.corpus[d1], self.corpus[d2])
                if sim >= threshold:
                    adj[d1].append(d2)
                    adj[d2].append(d1)
                    
        # Find connected components (clusters)
        for doc_id in doc_ids:
            if doc_id not in visited:
                cluster = []
                queue = [doc_id]
                visited.add(doc_id)
                while queue:
                    curr = queue.pop(0)
                    cluster.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                clusters.append(cluster)
                
        return clusters
