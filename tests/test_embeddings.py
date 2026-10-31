"""Tests for the real Sentence Transformer model.

The first run downloads all-MiniLM-L6-v2 (~90 MB). If there is no internet the
tests are skipped instead of failing.
"""

import numpy as np
import pytest

from src.embeddings.embedding_model import cosine_similarity


@pytest.fixture(scope="module")
def model():
    try:
        from src.embeddings.embedding_model import get_embedding_model
        return get_embedding_model()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"embedding model unavailable: {exc}")


def test_cosine_similarity_basics():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([0, 0], [1, 1]) == 0.0


def test_dimension_and_normalisation(model):
    vecs = model.embed_documents(["Internal auditing evaluates organizational controls."])
    assert vecs.shape == (1, 384)
    assert np.linalg.norm(vecs[0]) == pytest.approx(1.0, abs=1e-4)


def test_similar_texts_are_closer(model):
    q = model.embed_query("What does an internal auditor do?")
    related, unrelated = model.embed_documents([
        "Internal auditors evaluate controls and assess risks.",
        "The cafeteria serves lunch from noon until two.",
    ])
    assert cosine_similarity(q, related) > cosine_similarity(q, unrelated)
