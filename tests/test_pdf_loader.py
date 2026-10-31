import pytest

from src.document_processing.pdf_loader import load_pdf, load_pdf_bytes
from src.document_processing.text_cleaner import clean_document, normalize_text


def test_extracts_pages_with_numbers(sample_pdf):
    doc = load_pdf(sample_pdf)
    assert doc.source == "policy.pdf"
    assert doc.num_pages == 4
    assert [p.page for p in doc.pages] == [1, 2, 3, 4]
    assert "Responsibilities of Internal Auditors" in doc.pages[1].text


def test_detects_empty_pages(sample_pdf, tmp_path):
    from tests.conftest import make_pdf

    # raw page 3 only has header/footer text; after cleaning it is empty
    assert clean_document(load_pdf(sample_pdf)).empty_pages == [3]
    plain = load_pdf(make_pdf(tmp_path / "plain.pdf", ["Some policy text here.", ""]))
    assert plain.empty_pages == [2]
    assert not load_pdf(sample_pdf).likely_scanned()


def test_load_from_bytes(sample_pdf):
    doc = load_pdf_bytes(sample_pdf.read_bytes(), "upload.pdf")
    assert doc.source == "upload.pdf" and doc.num_pages == 4


def test_missing_and_invalid_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pdf(tmp_path / "nope.pdf")
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    with pytest.raises(ValueError):
        load_pdf(bad)


def test_cleaner_removes_repeated_header_and_page_numbers(sample_pdf):
    cleaned = clean_document(load_pdf(sample_pdf))
    for page in cleaned.pages:
        assert "CONFIDENTIAL" not in page.text
        assert "Page " not in page.text
    assert "Internal auditors evaluate internal controls" in cleaned.pages[1].text


def test_normalize_text():
    raw = "risk  manage-\nment policy “quoted”\n\n\n\nnext"
    out = normalize_text(raw)
    assert "risk management policy" in out
    assert '"quoted"' in out
    assert "\n\n\n" not in out
