"""PDF loading: extract text page by page while keeping page numbers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pymupdf  # PyMuPDF


@dataclass
class PageText:
    page: int          # 1-based page number, as a human reads it
    text: str
    is_empty: bool = False


@dataclass
class LoadedDocument:
    source: str                     # file name, e.g. "internal_audit_policy.pdf"
    num_pages: int
    pages: list[PageText] = field(default_factory=list)

    @property
    def empty_pages(self) -> list[int]:
        return [p.page for p in self.pages if p.is_empty]

    @property
    def total_chars(self) -> int:
        return sum(len(p.text) for p in self.pages)

    def likely_scanned(self, threshold: float = 0.5) -> bool:
        """True when most pages have no selectable text (needs OCR)."""
        if self.num_pages == 0:
            return False
        return len(self.empty_pages) / self.num_pages >= threshold


# Pages with fewer characters than this are treated as empty/unreadable.
_EMPTY_PAGE_CHARS = 20


def _extract(doc: "pymupdf.Document", source: str) -> LoadedDocument:
    pages: list[PageText] = []
    for index, page in enumerate(doc):
        text = page.get_text("text", sort=True) or ""
        pages.append(
            PageText(page=index + 1, text=text, is_empty=len(text.strip()) < _EMPTY_PAGE_CHARS)
        )
    return LoadedDocument(source=source, num_pages=len(pages), pages=pages)


def load_pdf(path: str | Path) -> LoadedDocument:
    """Read a PDF file from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {path.name}")
    try:
        with pymupdf.open(path) as doc:
            return _extract(doc, path.name)
    except pymupdf.FileDataError as exc:
        raise ValueError(f"Could not open {path.name}: file is corrupt or not a PDF") from exc


def load_pdf_bytes(data: bytes, source: str) -> LoadedDocument:
    """Read a PDF from memory (used for Streamlit uploads)."""
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            return _extract(doc, source)
    except pymupdf.FileDataError as exc:
        raise ValueError(f"Could not open {source}: file is corrupt or not a PDF") from exc


def save_extracted_text(doc: LoadedDocument, out_dir: str | Path) -> Path:
    """Save extracted page text as JSON for inspection/debugging."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(doc.source).stem}.json"
    out_path.write_text(json.dumps(asdict(doc), ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
