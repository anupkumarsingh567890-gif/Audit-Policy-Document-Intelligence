# System Architecture

## Components

```
                ┌──────────────────────── app.py (Streamlit) ────────────────────────┐
                │  sidebar: upload · document list · mode · top-k · document filter    │
                │  main:    metrics · chat · answer · source chips · retrieved passages│
                └───────────────────────────────┬────────────────────────────────────┘
                                                │
                                   src/chatbot/assistant.py
                          ┌─────────────────────┴─────────────────────┐
                    ingest_file / ingest_bytes                      ask(question, mode)
                          │                                            │
     pdf_loader ─► text_cleaner ─► text_chunker              retriever.retrieve()
                          │                                            │
                 embedding_model.embed_documents      embedding_model.embed_query
                          │                                            │
                          └──────────►  chroma_db (ChromaDB, cosine) ◄─┘
                                                                       │
                                                       mode = retrieval ─► passages
                                                       mode = rag ─► prompts + gemini.py ─► answer [n]
```

## A. Ingestion pipeline
1. **Extract** (`pdf_loader.py`): PyMuPDF reads each page (`sort=True` for reading order). Pages under 20 characters are marked empty; a document with mostly empty pages is flagged as likely scanned.
2. **Clean** (`text_cleaner.py`): Unicode normalisation, smart quotes/bullets/soft hyphens normalised, words hyphenated across lines re-joined, mid-sentence line breaks joined, standalone page numbers removed, and lines repeated at the top/bottom of ≥50% of pages (headers/footers) removed.
3. **Chunk** (`text_chunker.py`): each page is split into sentence/paragraph/list-item units, then packed into chunks of ≤1,000 characters, carrying ≤200 characters of trailing sentences into the next chunk as overlap. Chunks never span two pages.
4. **Embed** (`embedding_model.py`): `all-MiniLM-L6-v2`, 384 dimensions, L2-normalised.
5. **Store** (`chroma_db.py`): upsert into a persistent ChromaDB collection configured for cosine distance, with `{source, page, chunk_index}` metadata. IDs are deterministic, so re-ingesting replaces the old version.

Intermediate outputs are saved to `data/processed/extracted_text/*.json` and `data/processed/chunks/*_chunks.json` for inspection.

## B. Question answering pipeline
1. Embed the question with the same model.
2. Query ChromaDB for the top-k nearest chunks (optionally filtered to selected documents). Similarity = 1 − cosine distance.
3. **Retrieval mode:** return the passages with source, page and similarity.
4. **RAG mode:** build a prompt with numbered excerpts (`[1] Source: file | Page n`), send it with a grounding system instruction to Gemini at temperature 0.2, and return the answer plus unique (source, page) references.

## Gemini client behaviour
- Primary model from `GEMINI_MODEL`; on "model not found" it moves to the next fallback model.
- On rate-limit (HTTP 429) it waits 10 s, 20 s, then moves to the next model; on server errors it retries with shorter waits.
- Invalid keys produce a clear error message rather than a stack trace.

## Why embeddings are generated only once
Chunk embeddings are computed at ingestion and stored. At question time only the question is embedded, and Gemini receives only the retrieved chunks — not the whole PDF — which keeps requests small, fast and within free-tier limits.
