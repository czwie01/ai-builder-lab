"""Application settings, loaded from the environment with the RAG_API_ prefix.

Defaults are chosen so a fresh clone runs with no configuration at all:
the in-memory retriever needs no service, no model download, and no
network. Pointing `RAG_API_RETRIEVER` at `qdrant` opts into the real
pipeline.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_API_")

    app_name: str = "ai-builder-lab RAG API"
    log_level: str = "INFO"
    guard_max_question_length: int = 1000

    retriever: Literal["memory", "qdrant"] = "memory"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "rag_chunks"

    # Kept as a plain string so settings stay free of adapter imports.
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_cache_dir: str | None = None

    chunk_max_chars: int = 1800
    chunk_overlap_chars: int = 200
