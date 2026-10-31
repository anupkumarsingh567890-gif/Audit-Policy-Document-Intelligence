"""Text cleaning: normalise whitespace, fix broken words, drop repeated headers/footers."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .pdf_loader import LoadedDocument, PageText

# Characters PDFs often contain that hurt matching
_REPLACEMENTS = {
    "­": "",      # soft hyphen
    "​": "",      # zero-width space
    "﻿": "",      # BOM
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "–": "-", "—": "-",
    "•": "-", "●": "-", "": "-", "▪": "-",
    " ": " ",
}

_PAGE_NUMBER_RE = re.compile(r"^\s*(page\s*)?\d+(\s*(of|/)\s*\d+)?\s*$", re.IGNORECASE)


def normalize_text(text: str) -> str:
    """Clean a single block of text."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    for bad, good in _REPLACEMENTS.items():
        text = text.replace(bad, good)
    # Remove control chars except newline/tab
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    # Re-join words hyphenated across line breaks: "manage-\nment" -> "management"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Strip each line
    text = "\n".join(line.strip() for line in text.split("\n"))
    # Join lines broken mid-sentence (line not ending with punctuation, next starts lowercase)
    text = re.sub(r"(?<=[^\.\:\;\!\?\n])\n(?=[a-z])", " ", text)
    # Max one blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _edge_lines(text: str, n: int = 2) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return lines[:n] + lines[-n:] if len(lines) > n * 2 else lines


def find_repeated_lines(pages: list[str], min_ratio: float = 0.5, min_pages: int = 3) -> set[str]:
    """Lines that appear at the top/bottom of many pages (headers/footers)."""
    if len(pages) < min_pages:
        return set()
    counts: Counter[str] = Counter()
    for text in pages:
        counts.update(set(_edge_lines(text)))
    threshold = max(min_pages, int(len(pages) * min_ratio))
    return {line for line, c in counts.items() if c >= threshold and len(line) < 150}


def clean_document(doc: LoadedDocument, remove_headers_footers: bool = True) -> LoadedDocument:
    """Return a new LoadedDocument with cleaned page text."""
    raw_pages = [p.text for p in doc.pages]
    repeated = find_repeated_lines(raw_pages) if remove_headers_footers else set()

    cleaned: list[PageText] = []
    for page in doc.pages:
        lines = []
        for line in page.text.split("\n"):
            stripped = line.strip()
            if stripped in repeated or _PAGE_NUMBER_RE.match(stripped):
                continue
            lines.append(line)
        text = normalize_text("\n".join(lines))
        cleaned.append(PageText(page=page.page, text=text, is_empty=len(text) < 20))

    return LoadedDocument(source=doc.source, num_pages=doc.num_pages, pages=cleaned)
