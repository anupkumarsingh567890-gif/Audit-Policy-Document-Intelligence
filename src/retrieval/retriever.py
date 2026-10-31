"""Semantic retrieval: question -> embedding -> top-k chunks from ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass

from src.utils import config
from src.vector_store.chroma_db import ChromaVectorStore, SearchResult


@dataclass
class Reference:
    source: str
    page: int

    def __str__(self) -> str:
        return f"{self.source} — Page {self.page}"


class Retriever:
    def __init__(self, embedder, vector_store: ChromaVectorStore, top_k: int = config.TOP_K, min_score: float = 0.0):
        self.embedder = embedder
        self.store = vector_store
        self.top_k = top_k
        self.min_score = min_score

    def retrieve(self, question: str, top_k: int | None = None, source_filter: list[str] | None = None) -> list[SearchResult]:
        question = (question or "").strip()
        if not question:
            return []
        query_vec = self.embedder.embed_query(question)
        results = self.store.search(query_vec, top_k=top_k or self.top_k, source_filter=source_filter)
        return [r for r in results if r.score >= self.min_score]

    @staticmethod
    def references(results: list[SearchResult]) -> list[Reference]:
        """Unique (source, page) pairs in rank order."""
        seen, refs = set(), []
        for r in results:
            key = (r.source, r.page)
            if key not in seen:
                seen.add(key)
                refs.append(Reference(r.source, r.page))
        return refs
