# Project Overview

## Problem
Organisations keep large numbers of PDF documents — audit reports, financial policies, internal audit guidelines, risk policies, compliance and regulatory guidelines, SOPs. Keyword search in a PDF reader finds words, not answers: it cannot interpret a question, combine information across documents, or explain it in plain language.

## Solution
APDIS lets a user upload PDFs and ask natural-language questions. It retrieves the most relevant passages by meaning (semantic search over embeddings stored in ChromaDB) and has Google Gemini compose an answer **only from those passages**, citing the document and page for each point.

## Objectives
| # | Objective | Implemented in |
|---|---|---|
| 1 | Document processing — extract text with page numbers | `src/document_processing/pdf_loader.py`, `text_cleaner.py` |
| 2 | Text chunking with overlap and metadata | `src/document_processing/text_chunker.py` |
| 3 | Embedding generation | `src/embeddings/embedding_model.py` |
| 4 | Semantic search | `src/vector_store/chroma_db.py`, `src/retrieval/retriever.py` |
| 5 | LLM integration | `src/llm/gemini.py`, `src/llm/prompts.py` |
| 6 | Interactive interface | `app.py` |
| + | Source references and retrieval-only comparison mode | `src/chatbot/assistant.py`, `app.py` |

## Users
Internal auditors, risk and compliance teams, finance operations staff, and students learning audit and regulatory material.

## Deliverables
Working Streamlit app with multi-PDF upload; modular ingestion pipeline; ChromaDB knowledge base; retrieval-only and Gemini RAG modes; page-level citations; pytest suite; evaluation script with a 24-question test set; documentation.
