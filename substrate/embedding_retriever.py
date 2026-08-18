"""Embedding-based chunk retrieval for ExternalMemory.

Adds semantic retrieval alongside keyword overlap for better matching
of conceptually related but lexically different content.

Uses a lightweight sentence transformer model locally.

Note: Set HF_HOME env var to control cache location, e.g.:
  export HF_HOME="/Users/jake/Projects/cognitive core/.hf_cache"
"""

from __future__ import annotations
import os
import time
from typing import List, Optional, Tuple
import numpy as np


# Set HF cache to project-local by default
os.environ.setdefault("HF_HOME", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".hf_cache"))

# Lightweight model that runs well on Apple Silicon
DEFAULT_MODEL = "all-MiniLM-L6-v2"


class EmbeddingRetriever:
    """
    Embedding-based semantic retriever.

    Creates embeddings for chunks and queries, then scores by cosine similarity.
    Lazily loads the model on first use.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None
        self._chunk_embeddings: dict = {}  # chunk_id -> embedding vector
        self._chunk_texts: dict = {}  # chunk_id -> text
        self._load_time = 0.0

    def _load_model(self):
        if self._model is not None:
            return
        t0 = time.time()
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(self.model_name)
        self._load_time = time.time() - t0

    def index_chunk(self, chunk_id: str, text: str):
        """Add a chunk to the embedding index."""
        self._load_model()
        self._chunk_texts[chunk_id] = text
        # We don't compute embedding immediately — batch for efficiency
        # Instead we compute on first retrieve
        self._chunk_embeddings.pop(chunk_id, None)  # Mark for recomputation

    def _compute_all_embeddings(self):
        """Compute embeddings for all un-embedded chunks."""
        self._load_model()
        unembedded = [cid for cid in self._chunk_texts if cid not in self._chunk_embeddings]
        if not unembedded:
            return
        
        texts = [self._chunk_texts[cid] for cid in unembedded]
        # Batch encode
        embeddings = self._model.encode(texts, show_progress_bar=False, 
                                         normalize_embeddings=True)
        for cid, emb in zip(unembedded, embeddings):
            self._chunk_embeddings[cid] = emb

    def retrieve(self, query: str, chunk_ids: List[str], 
                 chunk_texts: dict, k: int = 5) -> List[Tuple[float, str]]:
        """
        Retrieve chunks by semantic similarity to query.
        
        Args:
            query: The search query
            chunk_ids: List of chunk IDs to search over
            chunk_texts: Dict of chunk_id -> text
            k: Number of results to return
            
        Returns:
            List of (score, chunk_id) sorted by relevance
        """
        self._load_model()
        
        # Index any new chunks
        for cid in chunk_ids:
            if cid not in self._chunk_texts and cid in chunk_texts:
                self._chunk_texts[cid] = chunk_texts[cid]
        
        # Compute embeddings
        self._compute_all_embeddings()
        
        # Query embedding
        query_emb = self._model.encode([query], normalize_embeddings=True)[0]
        
        # Score all indexed chunks
        scored = []
        for cid in chunk_ids:
            emb = self._chunk_embeddings.get(cid)
            if emb is None:
                continue
            similarity = float(np.dot(query_emb, emb))
            scored.append((similarity, cid))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    def statistics(self) -> dict:
        return {
            "model": self.model_name,
            "indexed_chunks": len(self._chunk_texts),
            "embedded_chunks": len(self._chunk_embeddings),
            "load_time": round(self._load_time, 2),
        }


class HybridRetriever:
    """
    Combines keyword overlap + embedding similarity.
    
    Scores are a weighted combination of both signals.
    """

    def __init__(self, keyword_weight: float = 0.3, embedding_weight: float = 0.7):
        self.keyword_weight = keyword_weight
        self.embedding_weight = embedding_weight
        self.embedding = EmbeddingRetriever()

    def retrieve(self, query: str, keyword_results: List[Tuple[float, str]],
                 all_chunk_ids: List[str], chunk_texts: dict, k: int = 5) -> List[Tuple[float, str]]:
        """
        Hybrid retrieval: combine keyword scores with embedding scores.
        
        Args:
            query: Search query
            keyword_results: Results from keyword retrieval (score, chunk_id)
            all_chunk_ids: All available chunk IDs (for embedding search)
            chunk_texts: Dict of chunk_id -> text
            k: Number of results
            
        Returns:
            List of (score, chunk_id) sorted by combined relevance
        """
        # Get keyword scores
        kw_scores = {cid: score for score, cid in keyword_results}
        
        # Get embedding scores for all chunks
        emb_results = self.embedding.retrieve(query, all_chunk_ids, chunk_texts, k=len(all_chunk_ids))
        emb_scores = {cid: score for score, cid in emb_results}
        
        # Normalize keyword scores to 0-1
        max_kw = max(kw_scores.values()) if kw_scores else 1.0
        
        # Combine
        combined = {}
        all_cids = set(list(kw_scores.keys()) + list(emb_scores.keys()))
        for cid in all_cids:
            kw = kw_scores.get(cid, 0.0) / max_kw
            emb = emb_scores.get(cid, 0.0)
            combined[cid] = self.keyword_weight * kw + self.embedding_weight * emb
        
        # Sort and return top k
        scored = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        return [(score, cid) for cid, score in scored[:k]]


def quick_test():
    """Demonstrate embedding retriever."""
    retriever = EmbeddingRetriever()
    
    print("=== Embedding Retriever Demo ===\n")
    
    # Index some chunks
    chunks = {
        "c1": "The capital of France is Paris, known for the Eiffel Tower.",
        "c2": "Python is a programming language used for machine learning.",
        "c3": "The CPU runs at 3.5 GHz with 16 cores and 32 threads.",
        "c4": "Paris is famous for its cuisine, art, and fashion.",
        "c5": "Machine learning models require large amounts of training data.",
    }
    
    for cid, text in chunks.items():
        retriever.index_chunk(cid, text)
    
    # Query
    queries = [
        "What is the capital of France?",
        "Tell me about programming and AI",
        "Computer processor specifications",
    ]
    
    for query in queries:
        results = retriever.retrieve(query, list(chunks.keys()), chunks, k=3)
        print(f"\nQuery: {query}")
        for score, cid in results:
            print(f"  [{score:.3f}] {chunks[cid][:70]}")
    
    print(f"\nStats: {retriever.statistics()}")


if __name__ == "__main__":
    quick_test()