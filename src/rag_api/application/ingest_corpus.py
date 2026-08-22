"""IngestCorpus use case: documents in, indexed chunks out.

Reading files is the caller's job (the CLI); this use case only knows
domain objects and the two ports it was handed.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from rag_api.application.chunking import (
    DEFAULT_MAX_CHARS,
    DEFAULT_OVERLAP_CHARS,
    chunk_markdown,
)
from rag_api.domain.models import EmbeddedChunk, SourceDocument
from rag_api.ports.chunk_index import ChunkIndex
from rag_api.ports.text_embedder import TextEmbedder


@dataclass(frozen=True, slots=True)
class IngestReport:
    documents: int
    chunks: int


class IngestCorpus:
    def __init__(
        self,
        index: ChunkIndex,
        embedder: TextEmbedder,
        *,
        max_chars: int = DEFAULT_MAX_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    ) -> None:
        self._index = index
        self._embedder = embedder
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    async def execute(self, documents: Sequence[SourceDocument]) -> IngestReport:
        chunks = [
            chunk
            for document in documents
            for chunk in chunk_markdown(
                document.text,
                document_id=document.document_id,
                source_path=document.source_path,
                max_chars=self._max_chars,
                overlap_chars=self._overlap_chars,
            )
        ]
        await self._index.ensure_ready(dimension=self._embedder.dimension)
        if not chunks:
            return IngestReport(documents=len(documents), chunks=0)

        vectors = await self._embedder.embed_documents([chunk.text for chunk in chunks])
        entries = [
            EmbeddedChunk(chunk=chunk, vector=tuple(vector))
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        await self._index.upsert(entries)
        return IngestReport(documents=len(documents), chunks=len(chunks))
