"""
Substrate — External Memory (InfLLM-style Baseline)

From Memory Spec §9, §10. Implements the LC0 baseline:
  - External raw-history store (append-only)
  - Chunk index with semantic keys
  - Simple retrieval for materialisation into working context

Memory hierarchy (from Spec §10):
  L0: Hot working context (~8-16K)
  L1: Materialised historical context (~8-48K)
  L2: Chunk/event index (semantic keys, time range, importance)
  L3: Modus structured memory (claims, events, decisions)
  L4: Raw exact history (≥1M tokens, cold but addressable)
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Chunk:
    """
    A chunk in the external memory index.

    From Memory Spec §11 — Chunk representation.
    """
    chunk_id: str
    """Content-addressed ID."""

    tokens: List[str]
    """Token sequence (can be re-tokenised on demand)."""

    token_start: int = 0
    """Global token position in the history."""

    token_end: int = 0

    semantic_key: str = ""
    """Brief semantic label."""

    retrieval_keywords: List[str] = field(default_factory=list)
    """Keywords for overlap retrieval."""

    importance: float = 0.5
    """0.0-1.0 importance score."""

    timestamp: float = 0.0
    """When this chunk was created."""

    provenance: List[str] = field(default_factory=list)
    """Source event IDs."""

    content_hash: str = ""
    """Hash of raw text content for dedup."""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tokens"] = d["tokens"][:10]  # Don't serialize full tokens
        d["_token_count"] = len(self.tokens)
        return d


@dataclass
class HistoryEntry:
    """A raw entry in the append-only history store (L4)."""
    entry_id: str
    text: str
    timestamp: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExternalMemory:
    """
    External memory store with chunk indexing.

    Implements the LC0 baseline from Memory Spec §9:
      - Raw history store (L4)
      - Chunk index (L2)
      - Simple retrieval for materialisation
      
    Supports three retrieval modes:
      - 'keyword': Fast keyword overlap (default)
      - 'embedding': Semantic similarity via sentence-transformers
      - 'hybrid': Weighted combination of keyword + embedding
    """

    def __init__(self, chunk_size_tokens: int = 256, 
                 retrieval_mode: str = "keyword"):
        self.chunk_size = chunk_size_tokens
        self.retrieval_mode = retrieval_mode
        self._history: List[HistoryEntry] = []
        self._chunks: Dict[str, Chunk] = {}  # chunk_id → Chunk
        self._keyword_index: Dict[str, List[str]] = {}  # keyword → [chunk_id]
        self._total_tokens: int = 0
        self._embedding = None  # Lazy-loaded EmbeddingRetriever

    def append(self, text: str, source: str = "system",
               metadata: Optional[Dict] = None) -> Chunk:
        """
        Append text to the history store. Automatically chunks.
        Returns the last created chunk.
        """
        entry_id = f"hist_{hashlib.sha256(text.encode()).hexdigest()[:16]}_{len(self._history)}"

        entry = HistoryEntry(
            entry_id=entry_id,
            text=text,
            timestamp=time.time(),
            source=source,
            metadata=metadata or {},
        )
        self._history.append(entry)

        # Simple whitespace-based tokenisation
        tokens = text.split()
        self._total_tokens += len(tokens)

        # Create chunks
        last_chunk = None
        for i in range(0, len(tokens), self.chunk_size):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_tokens)
            content_hash = hashlib.sha256(chunk_text.encode()).hexdigest()

            # Skip if content-identical chunk exists
            if content_hash in {c.content_hash for c in self._chunks.values()}:
                continue

            # Extract keywords (unique words with length > 3, excluding punctuation)
            keywords = list(set(
                w.lower().strip(".,!?;:()[]{}'\"") for w in chunk_tokens
                if len(w.strip(".,!?;:()[]{}'\"")) > 2
            ))
            # Also add stem-like prefixes for matching
            extra_keywords = []
            for kw in keywords:
                if len(kw) > 4:
                    extra_keywords.append(kw[:-1])  # e.g. "named" → "name"
                    extra_keywords.append(kw[:-2])  # e.g. "named" → "nam"
            keywords.extend(extra_keywords)
            keywords = list(set(keywords))

            chunk = Chunk(
                chunk_id=f"chk_{hashlib.sha256(chunk_text.encode()).hexdigest()[:24]}",
                tokens=chunk_tokens,
                token_start=self._total_tokens - len(tokens) + i,
                token_end=self._total_tokens - len(tokens) + i + len(chunk_tokens),
                semantic_key=chunk_tokens[:5] if chunk_tokens else "",
                retrieval_keywords=keywords,
                timestamp=time.time(),
                provenance=[entry_id],
                content_hash=content_hash,
            )

            self._chunks[chunk.chunk_id] = chunk
            for kw in keywords:
                self._keyword_index.setdefault(kw, []).append(chunk.chunk_id)

            last_chunk = chunk

        return last_chunk

    def retrieve(self, query: str, k: int = 5,
                 min_importance: float = 0.0) -> List[Tuple[float, Chunk]]:
        """
        Retrieve relevant chunks for a query.

        Uses the configured retrieval_mode:
          - 'keyword': Simple keyword overlap scoring
          - 'embedding': Semantic similarity via sentence-transformers
          - 'hybrid': Weighted combination of both

        Returns list of (score, chunk) sorted by relevance.
        """
        if self.retrieval_mode == "embedding":
            return self._retrieve_embedding(query, k, min_importance)
        elif self.retrieval_mode == "hybrid":
            return self._retrieve_hybrid(query, k, min_importance)
        else:
            return self._retrieve_keyword(query, k, min_importance)

    def _ensure_embedding(self):
        """Lazy-load the embedding retriever."""
        if self._embedding is None:
            from .embedding_retriever import EmbeddingRetriever
            self._embedding = EmbeddingRetriever()
            # Index all existing chunks
            for cid, chunk in self._chunks.items():
                text = " ".join(chunk.tokens)
                self._embedding.index_chunk(cid, text)

    def _retrieve_keyword(self, query: str, k: int = 5,
                          min_importance: float = 0.0) -> List[Tuple[float, Chunk]]:
        """Keyword overlap retrieval."""
        query_lower = query.lower()
        query_words = set(
            w.strip(".,!?;:()[]{}'\"") for w in query_lower.split()
            if len(w.strip(".,!?;:()[]{}'\"")) > 2
        )

        scored = []
        for chunk in self._chunks.values():
            if chunk.importance < min_importance:
                continue

            # Keyword overlap
            kw_overlap = sum(1 for kw in chunk.retrieval_keywords if kw in query_words)
            relevance = kw_overlap / max(len(query_words), 1)

            if relevance <= 0:
                continue

            # Combined score: relevance + importance + recency
            recency = 1.0 - (time.time() - chunk.timestamp) / 86400
            score = (0.5 * relevance +
                     0.3 * chunk.importance +
                     0.2 * max(0, recency))
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    def _retrieve_embedding(self, query: str, k: int = 5,
                            min_importance: float = 0.0) -> List[Tuple[float, Chunk]]:
        """Embedding-based semantic retrieval."""
        self._ensure_embedding()
        
        # Get all chunk IDs
        all_ids = list(self._chunks.keys())
        chunk_texts = {cid: " ".join(self._chunks[cid].tokens) for cid in all_ids}
        
        # Retrieve via embeddings
        results = self._embedding.retrieve(query, all_ids, chunk_texts, k=k * 2)
        
        # Map back to Chunk objects and apply importance filter
        scored = []
        for score, cid in results:
            chunk = self._chunks.get(cid)
            if chunk and chunk.importance >= min_importance:
                scored.append((score, chunk))
        
        return scored[:k]

    def _retrieve_hybrid(self, query: str, k: int = 5,
                         min_importance: float = 0.0) -> List[Tuple[float, Chunk]]:
        """Hybrid keyword + embedding retrieval."""
        # Get keyword results
        kw_results = self._retrieve_keyword(query, k=k * 3, min_importance=min_importance)
        
        # Get embedding results
        self._ensure_embedding()
        all_ids = list(self._chunks.keys())
        chunk_texts = {cid: " ".join(self._chunks[cid].tokens) for cid in all_ids}
        emb_results = self._embedding.retrieve(query, all_ids, chunk_texts, k=k * 3)
        
        # Build combined scores using chunk_id as the key
        kw_scores = {c.chunk_id: s for s, c in kw_results}
        emb_scores = {cid: s for s, cid in emb_results}
        max_kw = max(kw_scores.values()) if kw_scores else 1.0
        
        combined = {}
        for s, c in kw_results:
            cid = c.chunk_id
            combined[cid] = (c, 0.3 * (kw_scores.get(cid, 0) / max_kw) + 0.7 * emb_scores.get(cid, 0))
        for s, cid in emb_results:
            if cid in combined:
                continue  # Already scored from keyword
            chunk = self._chunks.get(cid)
            if chunk and chunk.importance >= min_importance:
                combined[cid] = (chunk, 0.7 * s)
        
        scored = [(s, c) for c, s in combined.values()]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    def retrieve_by_keywords(self, keywords: List[str], k: int = 5) -> List[Chunk]:
        """Retrieve chunks matching specific keywords."""
        matching_ids = set()
        for kw in keywords:
            kw_lower = kw.lower()
            for chunk_kw, chunk_ids in self._keyword_index.items():
                if kw_lower in chunk_kw or chunk_kw in kw_lower:
                    matching_ids.update(chunk_ids)

        chunks = [self._chunks[cid] for cid in matching_ids if cid in self._chunks]
        chunks.sort(key=lambda c: c.importance, reverse=True)
        return chunks[:k]

    def retrieve_recent(self, k: int = 5, min_importance: float = 0.0) -> List[Tuple[float, Chunk]]:
        """
        Retrieve the most recent chunks by timestamp.
        Useful for state-tracking and accumulation tasks where the most
        recent conversation history is more relevant than semantic similarity.
        Returns list of (timestamp, chunk) sorted by recency (newest first).
        """
        scored = []
        for chunk in self._chunks.values():
            if chunk.importance < min_importance:
                continue
            scored.append((chunk.timestamp, chunk))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(s, c) for s, c in scored[:k]]

    def materialise(self, chunk_ids: List[str], preserve_order: bool = False) -> str:
        """
        Materialise chunks into a text string for the context window.
        From Memory Spec §5: content is serialised at ordinary local positions.
        """
        parts = []
        for cid in chunk_ids:
            chunk = self._chunks.get(cid)
            if chunk:
                text = " ".join(chunk.tokens)
                parts.append(f"[ref:{chunk.chunk_id}] {text}")
        return "\n\n".join(parts)

    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get recent history entries."""
        entries = self._history[-limit:] if limit else self._history
        return [{"id": e.entry_id, "text": e.text[:100], "source": e.source}
                for e in entries]

    def statistics(self) -> dict:
        stats = {
            "total_tokens": self._total_tokens,
            "chunks": len(self._chunks),
            "history_entries": len(self._history),
            "keyword_index_size": len(self._keyword_index),
            "chunk_size": self.chunk_size,
            "retrieval_mode": self.retrieval_mode,
        }
        if self._embedding is not None:
            stats["embedding"] = self._embedding.statistics()
        return stats


def quick_test():
    """Demonstrate external memory."""
    mem = ExternalMemory(chunk_size_tokens=20)

    print("=== External Memory (LC0 Baseline) ===\n")

    # Append some text
    mem.append(
        "The capital of France is Paris. The city is known for the Eiffel Tower.",
        source="fact_kb"
    )
    mem.append(
        "MiniCPM5 is a 1.08 billion parameter language model with 131K native context.",
        source="model_doc"
    )
    mem.append(
        "Project Phoenix uses Python language with dark theme and font size 16.",
        source="session_state"
    )

    print(f"History entries: {len(mem._history)}")
    print(f"Chunks created:  {len(mem._chunks)}")
    print(f"Total tokens:    {mem._total_tokens}")

    # Retrieve
    results = mem.retrieve("What is the capital of France?", k=3)
    print(f"\nRetrieve 'What is the capital of France?':")
    for score, chunk in results:
        text = " ".join(chunk.tokens)[:80]
        print(f"  [{score:.2f}] {text}...")

    results = mem.retrieve("language model Python project", k=3)
    print(f"\nRetrieve 'language model Python project':")
    for score, chunk in results:
        text = " ".join(chunk.tokens)[:80]
        print(f"  [{score:.2f}] {text}...")

    # Materialise
    chunk_ids = [c.chunk_id for _, c in mem.retrieve("France Paris capital", k=2)]
    materialised = mem.materialise(chunk_ids)
    print(f"\nMaterialised context:\n{materialised[:200]}...")

    print(f"\nStatistics: {mem.statistics()}")


if __name__ == "__main__":
    quick_test()