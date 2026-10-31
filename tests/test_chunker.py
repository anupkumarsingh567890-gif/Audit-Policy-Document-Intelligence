import pytest

from src.document_processing.pdf_loader import LoadedDocument, PageText
from src.document_processing.text_chunker import chunk_document, split_text

LONG = " ".join(f"Sentence number {i} explains an internal control requirement." for i in range(60))


def test_short_text_is_one_chunk():
    assert split_text("Short policy text.", 1000, 200) == ["Short policy text."]


def test_chunks_respect_size():
    chunks = split_text(LONG, 300, 60)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)


def test_chunks_overlap():
    chunks = split_text(LONG, 300, 100)
    for a, b in zip(chunks, chunks[1:]):
        last_sentence = a.split(". ")[-1]
        assert last_sentence in b, "next chunk should begin with the tail of the previous one"


def test_chunks_end_on_sentence_boundary():
    for c in split_text(LONG, 300, 60):
        assert c.endswith(".")


def test_very_long_word_run_is_hard_split():
    text = "word " * 1000
    assert all(len(c) <= 200 for c in split_text(text, 200, 40))


def test_invalid_overlap():
    with pytest.raises(ValueError):
        split_text("abc", 100, 100)


def test_metadata_and_ids_are_preserved():
    doc = LoadedDocument(
        source="policy.pdf",
        num_pages=3,
        pages=[PageText(1, LONG), PageText(2, "", is_empty=True), PageText(3, "Final page about audit committee oversight duties.")],
    )
    chunks = chunk_document(doc, chunk_size=400, chunk_overlap=80, min_chunk_chars=10)
    assert {c.page for c in chunks} == {1, 3}               # empty page skipped
    assert all(c.source == "policy.pdf" for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert len({c.id for c in chunks}) == len(chunks)          # unique ids
    # deterministic ids -> re-ingesting overwrites rather than duplicating
    assert [c.id for c in chunk_document(doc, 400, 80, 10)] == [c.id for c in chunks]
