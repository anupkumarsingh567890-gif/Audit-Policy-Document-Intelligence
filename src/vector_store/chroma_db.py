"""ChromaDB vector store: persist chunks + embeddings + metadata, search by cosine similarity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
import numpy as np
from chromadb.config import Settings

from src.document_processing.text_chunker import Chunk
from src.utils import config


@dataclass
class SearchResult:
    id: str
    text: str
    source: str
    page: int
    score: float        # cosine similarity, higher is better (max 1.0)


class ChromaVectorStore:
    def __init__(
        self,
        persist_dir: str | Path | None = config.CHROMA_DIR,
        collection_name: str = config.COLLECTION_NAME,
    ):
        settings = Settings(anonymized_telemetry=False)
        if persist_dir is None:
            self._client = chromadb.EphemeralClient(settings=settings)   # in-memory (tests)
        else:
            self._client = chromadb.PersistentClient(path=str(persist_dir), settings=settings)
        self.collection_name = collection_name
        # We pass our own embeddings, so no embedding_function is attached.
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,
        )

    # ------------------------------------------------------------ write
    def add_chunks(self, chunks: list[Chunk], embeddings: np.ndarray, batch_size: int = 500) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self._collection.upsert(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                metadatas=[c.metadata for c in batch],
                embeddings=np.asarray(embeddings[start : start + batch_size]).tolist(),
            )
        return len(chunks)

    def delete_source(self, source: str) -> None:
        self._collection.delete(where={"source": source})

    def reset(self) -> None:
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )

    # ------------------------------------------------------------ read
    def search(self, query_embedding: np.ndarray, top_k: int = 5, source_filter: list[str] | None = None) -> list[SearchResult]:
        count = self.count()
        if count == 0:
            return []
        where = None
        if source_filter:
            where = {"source": source_filter[0]} if len(source_filter) == 1 else {"source": {"$in": source_filter}}
        res = self._collection.query(
            query_embeddings=[np.asarray(query_embedding).tolist()],
            n_results=min(top_k, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        results: list[SearchResult] = []
        for id_, text, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            results.append(
                SearchResult(
                    id=id_,
                    text=text,
                    source=meta.get("source", "unknown"),
                    page=int(meta.get("page", 0)),
                    score=round(1.0 - float(dist), 4),   # cosine distance -> similarity
                )
            )
        return results

    def count(self) -> int:
        return self._collection.count()

    def list_sources(self) -> dict[str, int]:
        """{source file name: number of chunks}"""
        data = self._collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for meta in data["metadatas"] or []:
            src = meta.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return dict(sorted(counts.items()))
