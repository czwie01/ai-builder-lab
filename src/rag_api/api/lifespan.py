"""Process-lifetime resources for the HTTP app.

The Qdrant client and the embedding model are expensive to build and
must outlive a single request — and the client has no async context
manager, so something has to close it explicitly. That something is the
lifespan, which is also the only place allowed to know that a client
exists at all.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from qdrant_client import AsyncQdrantClient

from rag_api.adapters.fastembed_embedder import FastEmbedEmbedder
from rag_api.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    if settings.retriever != "qdrant":
        yield
        return

    client = AsyncQdrantClient(url=settings.qdrant_url)
    app.state.qdrant_client = client
    # Building the embedder downloads the model on first run, so failures
    # surface at boot rather than on the first question.
    app.state.embedder = FastEmbedEmbedder(
        model_name=settings.embedding_model,
        cache_dir=settings.embedding_cache_dir,
    )
    try:
        yield
    finally:
        await client.close()
