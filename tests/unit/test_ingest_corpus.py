import pytest

from rag_api.application.ingest_corpus import IngestCorpus
from rag_api.domain.models import SourceDocument
from tests.fakes import FakeChunkIndex, HashEmbedder

DOCUMENTS = [
    SourceDocument(document_id="a", source_path="a.md", text="# A\n\nAlpha text about ports.\n"),
    SourceDocument(document_id="b", source_path="b.md", text="# B\n\nBeta text about adapters.\n"),
]


async def test_chunks_embeds_and_upserts() -> None:
    index = FakeChunkIndex()
    use_case = IngestCorpus(index, HashEmbedder())

    report = await use_case.execute(DOCUMENTS)

    assert report.documents == 2
    assert report.chunks == len(index.entries) == 2
    assert {entry.chunk.document_id for entry in index.entries} == {"a", "b"}
    assert all(len(entry.vector) == 64 for entry in index.entries)


async def test_prepares_the_index_for_the_embedder_dimension() -> None:
    index = FakeChunkIndex()

    await IngestCorpus(index, HashEmbedder(dimension=32)).execute(DOCUMENTS)

    assert index.dimensions == [32]


async def test_empty_corpus_still_prepares_the_index() -> None:
    index = FakeChunkIndex()

    report = await IngestCorpus(index, HashEmbedder()).execute([])

    assert report.chunks == 0
    assert index.dimensions == [64]
    assert index.entries == []


async def test_embedder_returning_the_wrong_count_is_an_error() -> None:
    class ShortEmbedder(HashEmbedder):
        async def embed_documents(self, texts: object) -> list[list[float]]:
            return [self.vector("only one")]

    with pytest.raises(ValueError, match="argument 2 is shorter"):
        await IngestCorpus(FakeChunkIndex(), ShortEmbedder()).execute(DOCUMENTS)
