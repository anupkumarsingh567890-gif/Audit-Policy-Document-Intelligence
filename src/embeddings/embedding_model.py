"""Embedding generation with Sentence Transformers (all-MiniLM-L6-v2, 384 dimensions)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from src.utils import config


class EmbeddingModel:
    """Wraps a SentenceTransformer model. Vectors are L2-normalised, so the
    dot product of two vectors equals their cosine similarity."""

    def __init__(self, model_name: str = config.EMBEDDING_MODEL):
        # Imported lazily: torch is slow to import and tests can use a fake model
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    @property
    def max_seq_length(self) -> int:
        return self._model.max_seq_length

    def embed_documents(self, texts: list[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

    def embed_query(self, text: str) -> np.ndarray:
        return self._model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]


@lru_cache(maxsize=2)
def get_embedding_model(model_name: str = config.EMBEDDING_MODEL) -> EmbeddingModel:
    """Load the model once per process (first load downloads ~90 MB)."""
    return EmbeddingModel(model_name)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0
