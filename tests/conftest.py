"""Shared test fixtures.

`HashEmbedder` is a tiny deterministic bag-of-words embedder, so retrieval tests
run fast and offline without downloading the real Sentence Transformer model.
"""

import hashlib
import re
import sys
from pathlib import Path

import numpy as np
import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "is", "are", "for", "on", "be", "by", "with", "what", "how", "who", "which", "at", "must", "within"}


class HashEmbedder:
    dimension = 512

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dimension, dtype=np.float32)
        for word in re.findall(r"[a-z]+", text.lower()):
            if word in _STOP or len(word) < 3:
                continue
            word = word[:6]  # crude stemming: auditor/auditors/audit -> same bucket
            v[int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dimension] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed_documents(self, texts, **_):
        return np.stack([self._vec(t) for t in texts]) if texts else np.zeros((0, self.dimension))

    def embed_query(self, text):
        return self._vec(text)


@pytest.fixture
def hash_embedder():
    return HashEmbedder()


def make_pdf(path: Path, pages: list[str], header: str | None = None) -> Path:
    doc = pymupdf.open()
    for i, body in enumerate(pages, 1):
        page = doc.new_page()
        if header:
            page.insert_text((50, 30), header, fontsize=8)
            page.insert_text((280, 820), f"Page {i}", fontsize=8)
        if body:
            page.insert_textbox(pymupdf.Rect(50, 60, 545, 780), body, fontsize=10)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def sample_pdf(tmp_path):
    pages = [
        "Introduction to Internal Auditing. Internal auditing is an independent assurance activity that evaluates governance and controls.",
        "Responsibilities of Internal Auditors. Internal auditors evaluate internal controls, assess operational risks and review compliance with policies.",
        "",  # empty page
        "Risk appetite. The Board approves the risk appetite statement every year. Breaches are reported to the Chief Risk Officer.",
    ]
    return make_pdf(tmp_path / "policy.pdf", pages, header="Example Co. | Audit Policy | CONFIDENTIAL")
