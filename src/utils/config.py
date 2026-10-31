"""Central configuration for APDIS.

All paths and tunable settings live here. Values can be overridden through
environment variables in the `.env` file (see `.env.example`).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = two levels above this file (src/utils/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DOCS_DIR = DATA_DIR / "raw" / "documents"
EXTRACTED_TEXT_DIR = DATA_DIR / "processed" / "extracted_text"
CHUNKS_DIR = DATA_DIR / "processed" / "chunks"
CHROMA_DIR = DATA_DIR / "vectorstore" / "chroma_db"

for _d in (RAW_DOCS_DIR, EXTRACTED_TEXT_DIR, CHUNKS_DIR, CHROMA_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- chunking
# all-MiniLM-L6-v2 only reads the first 256 word-pieces of a text; anything
# longer is silently truncated before embedding. ~1,000 characters is roughly
# 200-250 tokens, so every chunk is fully represented by its vector.
CHUNK_SIZE = _get_int("CHUNK_SIZE", 1000)        # characters
CHUNK_OVERLAP = _get_int("CHUNK_OVERLAP", 200)   # characters
MIN_CHUNK_CHARS = _get_int("MIN_CHUNK_CHARS", 50)

# ---------------------------------------------------------------- embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# ---------------------------------------------------------------- vector store
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "apdis_documents")

# ---------------------------------------------------------------- retrieval
TOP_K = _get_int("TOP_K", 5)

# ---------------------------------------------------------------- LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
# Primary model, then fallbacks tried in order if a model is unavailable
# for your key (renamed / retired / not on the free tier).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_FALLBACK_MODELS", "gemini-flash-lite-latest,gemini-2.5-flash-lite"
    ).split(",")
    if m.strip()
]
GEMINI_TEMPERATURE = _get_float("GEMINI_TEMPERATURE", 0.2)
GEMINI_MAX_OUTPUT_TOKENS = _get_int("GEMINI_MAX_OUTPUT_TOKENS", 2048)
# How much the model "thinks" before answering: off (fastest), low (default), default (model's own setting)
GEMINI_THINKING = os.getenv("GEMINI_THINKING", "low").strip().lower()
