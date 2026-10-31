"""Ingest every PDF in data/raw/documents into ChromaDB.

Usage (from the project folder):
    python scripts/ingest.py            # add / update all PDFs
    python scripts/ingest.py --reset    # wipe the vector DB first
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.chatbot.assistant import APDISAssistant  # noqa: E402
from src.utils import config  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDFs into the APDIS vector database")
    parser.add_argument("--folder", default=str(config.RAW_DOCS_DIR))
    parser.add_argument("--reset", action="store_true", help="delete all stored chunks first")
    args = parser.parse_args()

    pdfs = sorted(Path(args.folder).glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {args.folder}. Add files there (or run scripts/make_sample_docs.py).")
        return

    print("Loading embedding model…")
    assistant = APDISAssistant()
    if args.reset:
        assistant.store.reset()
        print("Vector database cleared.")

    start = time.time()
    for pdf in pdfs:
        report = assistant.ingest_file(pdf)
        flag = "  ⚠ looks scanned — needs OCR" if report.likely_scanned else ""
        print(f"  ✓ {report.message}{flag}")
    print(f"\nDone in {time.time() - start:.1f}s. Total chunks in DB: {assistant.store.count()}")


if __name__ == "__main__":
    main()
