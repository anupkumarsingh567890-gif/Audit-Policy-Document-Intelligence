"""APDIS assistant: connects ingestion, retrieval and Gemini into one object.

    assistant = APDISAssistant()
    assistant.ingest_file("data/raw/documents/policy.pdf")
    result = assistant.ask("What are the responsibilities of an internal auditor?", mode="rag")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.document_processing.pdf_loader import LoadedDocument, load_pdf, load_pdf_bytes, save_extracted_text
from src.document_processing.text_chunker import chunk_document, save_chunks
from src.document_processing.text_cleaner import clean_document
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.retrieval.retriever import Reference, Retriever
from src.utils import config
from src.vector_store.chroma_db import ChromaVectorStore, SearchResult

MODE_RETRIEVAL = "retrieval"
MODE_RAG = "rag"
NO_RESULTS_MESSAGE = "No documents have been processed yet, or nothing relevant was found. Upload PDFs first."


@dataclass
class IngestReport:
    source: str
    num_pages: int
    num_chunks: int
    empty_pages: list[int] = field(default_factory=list)
    likely_scanned: bool = False

    @property
    def message(self) -> str:
        if self.num_chunks == 0:
            return f"{self.source}: no text found — it looks like a scanned PDF (needs OCR)."
        msg = f"{self.source}: {self.num_pages} pages → {self.num_chunks} chunks"
        if self.empty_pages:
            msg += f" ({len(self.empty_pages)} empty/unreadable pages skipped)"
        return msg


@dataclass
class Answer:
    question: str
    mode: str
    answer: str
    results: list[SearchResult]
    references: list[Reference]
    model: str | None = None


class APDISAssistant:
    def __init__(self, embedder=None, vector_store: ChromaVectorStore | None = None, llm=None, top_k: int = config.TOP_K):
        if embedder is None:
            from src.embeddings.embedding_model import get_embedding_model
            embedder = get_embedding_model()
        self.embedder = embedder
        self.store = vector_store or ChromaVectorStore()
        self.retriever = Retriever(self.embedder, self.store, top_k=top_k)
        self._llm = llm   # created lazily so retrieval mode works without an API key

    # ------------------------------------------------------------ ingestion
    def _ingest_loaded(self, doc: LoadedDocument, save_intermediate: bool = True) -> IngestReport:
        cleaned = clean_document(doc)
        chunks = chunk_document(
            cleaned, config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.MIN_CHUNK_CHARS
        )
        if save_intermediate:
            save_extracted_text(cleaned, config.EXTRACTED_TEXT_DIR)
            save_chunks(chunks, doc.source, config.CHUNKS_DIR)
        # replace any earlier version of the same file
        self.store.delete_source(doc.source)
        if chunks:
            embeddings = self.embedder.embed_documents([c.text for c in chunks])
            self.store.add_chunks(chunks, embeddings)
        return IngestReport(
            source=doc.source,
            num_pages=doc.num_pages,
            num_chunks=len(chunks),
            empty_pages=cleaned.empty_pages,
            likely_scanned=doc.likely_scanned(),
        )

    def ingest_file(self, path: str | Path, save_intermediate: bool = True) -> IngestReport:
        return self._ingest_loaded(load_pdf(path), save_intermediate)

    def ingest_bytes(self, data: bytes, filename: str, save_copy: bool = True) -> IngestReport:
        if save_copy:   # keep the original in data/raw/documents (never modified)
            (config.RAW_DOCS_DIR / filename).write_bytes(data)
        return self._ingest_loaded(load_pdf_bytes(data, filename))

    def ingest_folder(self, folder: str | Path = config.RAW_DOCS_DIR) -> list[IngestReport]:
        return [self.ingest_file(p) for p in sorted(Path(folder).glob("*.pdf"))]

    def remove_document(self, source: str) -> None:
        self.store.delete_source(source)

    def documents(self) -> dict[str, int]:
        return self.store.list_sources()

    # ------------------------------------------------------------ question answering
    @property
    def llm(self):
        if self._llm is None:
            from src.llm.gemini import GeminiClient
            self._llm = GeminiClient()
        return self._llm

    def retrieve(self, question: str, top_k: int | None = None, source_filter: list[str] | None = None):
        results = self.retriever.retrieve(question, top_k=top_k, source_filter=source_filter)
        return results, Retriever.references(results)

    @staticmethod
    def format_passages(results: list[SearchResult]) -> str:
        return "\n\n".join(
            f"**[{i}] {r.source} — Page {r.page}** (similarity {r.score:.2f})\n\n{r.text}"
            for i, r in enumerate(results, 1)
        )

    def stream_answer(self, question: str, results: list[SearchResult]):
        """Yield Gemini's answer piece by piece (for the Streamlit UI)."""
        return self.llm.generate_stream(SYSTEM_PROMPT, build_user_prompt(question, results))

    def ask(self, question: str, mode: str = MODE_RAG, top_k: int | None = None, source_filter: list[str] | None = None) -> Answer:
        results, refs = self.retrieve(question, top_k, source_filter)

        if not results:
            return Answer(question, mode, NO_RESULTS_MESSAGE, [], [])

        if mode == MODE_RETRIEVAL:
            return Answer(question, mode, self.format_passages(results), results, refs)

        answer = self.llm.generate(SYSTEM_PROMPT, build_user_prompt(question, results))
        return Answer(question, mode, answer, results, refs, model=getattr(self.llm, "last_model_used", None))
