# Practice 02 — Vector retrieval with Qdrant

- Timebox: one focused session (~3 h; larger than Practice 01 because the eval gate had to be
  rebuilt before the retriever could be trusted)
- Focus: infrastructure — Qdrant, fastembed, chunking, ingest pipelines
- Outcome: the same `POST /api/v1/answers` contract, answered by real dense vector search over
  an ingested corpus, selectable with one environment variable

## Key concept: the payoff commit

Practice 01 built a seam and asserted it with a test. This practice cashes it in. Retrieval
moves from counting shared words to comparing embeddings — a total change of mechanism,
technology, and infrastructure — and the route, the request and response schemas, the use
case, and the domain models are all untouched. The diff that switches implementations is one
branch in `api/dependencies.py`.

That is the whole argument for ports and adapters, and it is only convincing because it was
set up before it was needed. The `Retriever` protocol was written when the only implementation
was four hardcoded strings; nothing about it had to change to accept a vector database.

Two capabilities genuinely are new, so they became new ports rather than being smuggled into
the existing one: `TextEmbedder` (turning text into vectors) and `ChunkIndex` (writing to the
index). Keeping writes out of `Retriever` means the serving path cannot mutate the index just
because it can search it.

## Exercise

1. Add `TextEmbedder` and `ChunkIndex` protocols in `ports/`. Vectors cross the boundary as
   plain sequences of floats — the domain may not import numpy any more than it may import
   FastAPI.
2. Write a heading-aware markdown chunker in the application layer using only the standard
   library. Structural, not semantic: recursive splitting at ~400–500 tokens benchmarks better
   than embedding-similarity chunking at a fraction of the cost.
3. Add an `IngestCorpus` use case that chunks, embeds, and upserts. File reading stays with
   the caller so the use case knows only domain objects and its ports.
4. Implement `FastEmbedEmbedder`, `QdrantChunkIndex`, and `QdrantRetriever` as adapters.
5. Select the retriever from `Settings`; default to in-memory so a fresh clone still runs with
   no service, no model, and no network.
6. Give the Qdrant client a lifespan to own and close it — it has no async context manager.
7. Add `rag-ingest` as a second, FastAPI-free entry point.
8. **Rebuild the eval gate before trusting any of it** (see below).
9. Keep `uv run pytest` fully offline.

## The eval gate was the real work

The gate inherited from Practice 01 was arithmetically broken, and the practice could not
honestly proceed until it was fixed. With 8 questions, each with one relevant document, over a
**four-document** corpus at k=3:

- a random retriever scores ~0.75 recall@3, because returning 3 of 4 documents is nearly
  everything;
- `recall@3 >= 0.9` demanded a perfect 8/8, since 7/8 = 0.875 fails.

Simultaneously vacuous and knife-edge. Swapping in a new retrieval mechanism against that gate
would have proven nothing while risking a red build on a single flipped question.

So the corpus grew to 6 documents (31 chunks) under `evals/corpus/`, frozen and
version-controlled, and the golden set to 25 questions **deliberately worded differently from
the source text** — otherwise word overlap answers them for free and semantic retrieval has
nothing to prove.

| Retriever | recall@3 | MRR | misses |
|---|---|---|---|
| term overlap (Practice 01) | 0.840 | 0.793 | 4 / 25 |
| dense (bge-small-en-v1.5) | *pending first CI run* | | |

Thresholds were set **after** measuring, just below the observed values (0.80 and 0.75),
leaving room for one more miss before the build fails. They are numerically lower than the old
0.9/0.8 while testing something far harder — the kind of change that has to be stated out loud
rather than slipped into a diff.

The dense thresholds are provisional and deliberately set below the lexical baseline: the
model weights cannot be downloaded in every environment (this one blocks Hugging Face), so
they were not measured before being written. CI reports the real numbers and a follow-up
commit replaces them — measure first, then choose, in that order and in that commit sequence.

## Three test tiers

| Tier | Command | Needs |
|---|---|---|
| unit + adapter | `uv run pytest` | nothing — Qdrant's embedded local mode plus a deterministic fake embedder |
| retrieval evals | `uv run pytest -m eval` | the embedding model (skips with a reason where it cannot be fetched) |
| congruence | `uv run pytest -m integration` | a real Qdrant server via `compose.yaml` |

The middle tier is the interesting one: `AsyncQdrantClient(":memory:")` runs in-process, so the
real adapter code is exercised in the default hermetic run. The third tier exists precisely
because local mode is a *polite* double — it accepts point ids a server would reject, and it
warns that it ignores payload indexes entirely.

## Self-check results

| Check | Result |
|---|---|
| Did the route, schemas, use case, or HTTP contract change? | ✅ No — the diff is one branch in `api/dependencies.py` |
| Does a fresh clone still run with no service, model, or network? | ✅ Yes — `RAG_API_RETRIEVER` defaults to `memory` |
| Does `uv run pytest` still run fully offline? | ✅ Yes — 42 tests, including real Qdrant adapter tests via local mode |
| Can the ingest pipeline run without FastAPI? | ✅ Yes — `rag-ingest`, a second composition root |
| Were retrieval-affecting thresholds changed honestly? | ✅ Measured first, changed in their own commit, reasoning in the commit body |

## Stretch, for Practice 05

Four of the 25 questions defeat word overlap entirely. Which of hybrid search, reranking, or
better chunking closes them — and what does each cost in latency and complexity per point of
recall? The gate is now sensitive enough to answer that with numbers instead of opinions.

## What I'd do differently

- The dependency additions (`qdrant-client`, `fastembed`) pull grpcio, protobuf, numpy, and
  onnxruntime into *every* CI job, including lint and type-check. An optional extra would have
  kept the lint job slim; it was left as a single dependency set for simplicity, which is a
  trade worth revisiting if CI time becomes annoying.
- Writing the golden questions before looking at the corpus would have been more honest still.
  They were paraphrased deliberately, but by the same person who wrote the documents, which is
  its own kind of bias — Practice 04's synthetic generation should help.
