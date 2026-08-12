from rag_api.adapters.in_memory_retriever import InMemoryRetriever


async def test_returns_relevant_chunks_best_first() -> None:
    retriever = InMemoryRetriever()

    results = await retriever.search("What is a port in hexagonal architecture?", limit=4)

    assert results
    assert results[0].document_id == "architecture-01"
    scores = [chunk.score for chunk in results]
    assert scores == sorted(scores, reverse=True)


async def test_respects_limit() -> None:
    retriever = InMemoryRetriever()

    results = await retriever.search("retrieval architecture guardrails evals", limit=2)

    assert len(results) <= 2


async def test_no_overlap_returns_empty() -> None:
    retriever = InMemoryRetriever()

    assert await retriever.search("zzzz qqqq", limit=3) == ()
