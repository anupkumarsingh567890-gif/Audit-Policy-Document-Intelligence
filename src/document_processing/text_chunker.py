"""Text chunking: split each page into overlapping chunks, keeping source + page metadata.

Chunks never cross a page boundary, so every chunk maps to exactly one page and
the page reference shown to the user is always precise.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .pdf_loader import LoadedDocument


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    page: int
    chunk_index: int   # position within the document

    @property
    def metadata(self) -> dict:
        return {"source": self.source, "page": self.page, "chunk_index": self.chunk_index}


_SENTENCE_END_RE = re.compile(r"(?<=[\.\!\?\:\;])\s+|\n\n+|\n(?=\s*(?:[-•]|\d+[\.\)]|\([a-z0-9]+\))\s)")


def _split_units(text: str) -> list[str]:
    """Split text into sentence-like units (sentences, paragraphs, list items)."""
    return [u.strip() for u in _SENTENCE_END_RE.split(text) if u and u.strip()]


def _hard_split(unit: str, size: int) -> list[str]:
    """Split a very long unit (no punctuation) at word boundaries."""
    words, parts, current = unit.split(), [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > size:
            parts.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        parts.append(current)
    return parts


def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Split text into chunks of ~chunk_size characters with ~chunk_overlap overlap.

    Splits on sentence/paragraph boundaries where possible, so chunks don't
    start or end mid-sentence.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    units: list[str] = []
    for unit in _split_units(text):
        units.extend(_hard_split(unit, chunk_size) if len(unit) > chunk_size else [unit])

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for unit in units:
        added = len(unit) + (1 if current else 0)
        if current and current_len + added > chunk_size:
            chunks.append(" ".join(current))
            # carry trailing units forward as overlap
            overlap: list[str] = []
            overlap_len = 0
            for prev in reversed(current):
                if overlap_len + len(prev) + 1 > chunk_overlap:
                    break
                overlap.insert(0, prev)
                overlap_len += len(prev) + 1
            current, current_len = overlap, max(overlap_len - 1, 0)
            added = len(unit) + (1 if current else 0)
        current.append(unit)
        current_len += added
    if current:
        chunks.append(" ".join(current))
    return chunks


def make_chunk_id(source: str, page: int, index: int) -> str:
    """Stable id: re-ingesting the same file overwrites rather than duplicates."""
    digest = hashlib.md5(source.encode("utf-8")).hexdigest()[:10]
    return f"{digest}_p{page}_c{index}"


def chunk_document(
    doc: LoadedDocument,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_chars: int = 50,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    index = 0
    for page in doc.pages:
        if page.is_empty:
            continue
        for piece in split_text(page.text, chunk_size, chunk_overlap):
            if len(piece) < min_chunk_chars:
                continue
            chunks.append(
                Chunk(
                    id=make_chunk_id(doc.source, page.page, index),
                    text=piece,
                    source=doc.source,
                    page=page.page,
                    chunk_index=index,
                )
            )
            index += 1
    return chunks


def save_chunks(chunks: list[Chunk], source: str, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(source).stem}_chunks.json"
    out_path.write_text(
        json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path
