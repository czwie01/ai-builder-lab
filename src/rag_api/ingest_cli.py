"""`rag-ingest` — build the vector index from a directory of markdown.

A second composition root, deliberately free of FastAPI: indexing is a
batch job, not an HTTP concern. `--dry-run` reports what would be
indexed without touching the network, which makes it a cheap way to see
how a chunking change lands.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from qdrant_client import AsyncQdrantClient

from rag_api.adapters.fastembed_embedder import FastEmbedEmbedder
from rag_api.adapters.markdown_corpus import load_markdown_documents
from rag_api.adapters.qdrant_store import QdrantChunkIndex
from rag_api.application.chunking import chunk_markdown
from rag_api.application.ingest_corpus import IngestCorpus
from rag_api.config import Settings
from rag_api.domain.models import SourceDocument


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="rag-ingest", description="Index a markdown corpus into Qdrant."
    )
    parser.add_argument("--source", type=Path, default=Path("evals/corpus"))
    parser.add_argument("--collection", default=None, help="defaults to the configured collection")
    parser.add_argument("--recreate", action="store_true", help="drop the collection first")
    parser.add_argument("--dry-run", action="store_true", help="count chunks, index nothing")
    args = parser.parse_args()

    settings = Settings()
    collection: str = args.collection or settings.qdrant_collection
    if not args.source.is_dir():
        print(f"no such corpus directory: {args.source}", file=sys.stderr)
        return 1

    documents = load_markdown_documents(args.source)
    if not documents:
        print(f"no markdown files under {args.source}", file=sys.stderr)
        return 1

    if args.dry_run:
        chunks = sum(len(_chunks_of(document, settings)) for document in documents)
        print(f"{len(documents)} document(s) -> {chunks} chunk(s); nothing indexed (dry run)")
        return 0

    return asyncio.run(_ingest(documents, settings, collection, recreate=args.recreate))


def _chunks_of(document: SourceDocument, settings: Settings) -> list[object]:
    return list(
        chunk_markdown(
            document.text,
            document_id=document.document_id,
            source_path=document.source_path,
            max_chars=settings.chunk_max_chars,
            overlap_chars=settings.chunk_overlap_chars,
        )
    )


async def _ingest(
    documents: list[SourceDocument],
    settings: Settings,
    collection: str,
    *,
    recreate: bool,
) -> int:
    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        if recreate and await client.collection_exists(collection):
            await client.delete_collection(collection)
        embedder = FastEmbedEmbedder(
            model_name=settings.embedding_model,
            cache_dir=settings.embedding_cache_dir,
        )
        index = QdrantChunkIndex(client, collection=collection)
        report = await IngestCorpus(
            index,
            embedder,
            max_chars=settings.chunk_max_chars,
            overlap_chars=settings.chunk_overlap_chars,
        ).execute(documents)
        print(
            f"indexed {report.chunks} chunk(s) from {report.documents} document(s) "
            f"into '{collection}' at {settings.qdrant_url}"
        )
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    sys.exit(main())
