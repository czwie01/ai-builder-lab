# ADR-004: Vector retrieval with Qdrant and fastembed

- Status: accepted
- Date: 2026-08-20
- Practice: 02

## Context

Practice 01 left a `Retriever` port with a term-overlap implementation over four hardcoded
strings. Practice 02 replaces it with real dense vector search without changing the HTTP
contract, which means choosing a vector database, an embedding model, a chunking strategy, and
— crucially — a way to test all three without making the default test run depend on services,
model downloads, or the network.

ADR-003 pre-selected the technologies (Qdrant, fastembed, structure-aware chunking). This ADR
records the decisions made while implementing them, several of which came from behaviour that
only shows up once the libraries are actually in the repo.

## Decisions

### Dependencies: `qdrant-client` and `fastembed` as separate, ordinary dependencies

The `qdrant-client[fastembed]` extra exists, but its convenience API (`add`, `query`,
`set_model`) was removed from the client, so the extra buys nothing here — the embedder is its
own adapter behind its own port. Both are in the main dependency set rather than an optional
extra, because the adapters import them at module level and `mypy --strict` type-checks
`src/`.

**Consequence (accepted):** grpcio, protobuf, numpy, and onnxruntime now install in every CI
job, including lint and type-check. An optional extra would keep those jobs slim at the cost of
conditional imports; revisit if CI time becomes annoying.

### Embedding: `BAAI/bge-small-en-v1.5` via fastembed, behind a `TextEmbedder` port

384 dimensions, ~67 MB of ONNX weights, CPU-only, no torch. Two behaviours shaped the adapter:

- Constructing `TextEmbedding` **downloads the weights**, even with `lazy_load=True` (which
  only defers the ONNX session). So the embedder is built by an explicit factory call — never
  at import or test-collection time — and the API builds it in the lifespan so a missing model
  fails at boot rather than on the first question.
- `query_embed()` does **not** apply BGE's query instruction; it simply calls `embed()`. The
  prefix is therefore applied in the adapter, which is the only way ingest, serving, and evals
  can be guaranteed to agree.

Vectors cross the port boundary as plain sequences of floats, because the domain may not import
numpy any more than it may import FastAPI.

### Point ids: `uuid5(namespace, "document_id:chunk_index")`

A real Qdrant server accepts only unsigned integers or UUIDs as point ids; local mode accepts
anything. A readable id like `hexagonal#3` would therefore pass every hermetic test and fail in
production. Deriving a uuid5 from the document id and chunk index avoids that trap and makes
re-ingest idempotent: the same chunk always lands on the same point.

### The retriever imposes its own total order

Qdrant's local mode ranks with a bare `numpy.argsort`, which is quicksort and **not stable**, so
equally scored points come back in an unspecified order that carries no cross-version or
cross-CPU contract. `InMemoryRetriever` already guaranteed `(-score, document_id)`, and losing
that guarantee silently on the swap would have been a real regression. `QdrantRetriever`
re-sorts by `(-score, document_id, chunk_index)` after querying.

### Testing: three tiers, and local mode is a *polite* double

| Tier | Command | Needs |
|---|---|---|
| unit + adapter | `uv run pytest` | nothing — embedded local mode plus a deterministic fake embedder |
| retrieval evals | `uv run pytest -m eval` | the embedding model |
| congruence | `uv run pytest -m integration` | a real Qdrant server (`compose.yaml`) |

`AsyncQdrantClient(":memory:")` runs in-process, so the real adapter code is exercised in the
default hermetic run — a genuinely strong position. But local mode is *polite* about two
things it cannot do: it accepts point ids a server rejects, and `create_payload_index` warns
that it has no effect. The integration tier exists for exactly those, and local mode's exact
brute-force scan also means it cannot validate approximate-index recall.

The fake embedder used in tests hashes tokens with `hashlib` (not the salted builtin `hash`) so
it is deterministic across processes, and adds a tiny per-text component so two texts can never
produce exactly equal scores — which would otherwise land on local mode's undefined tie order.

### Default retriever: `memory`

`RAG_API_RETRIEVER` selects the adapter and defaults to `memory`, so a fresh clone runs with no
service, no model download, and no network. Choosing `qdrant` opts into the real pipeline.

### The eval corpus is frozen, and separate from the demo corpus

`evals/corpus/` holds six version-controlled markdown documents; the gate measures those, so a
score moves only when retrieval moves. The repo's own `docs/` tree can be ingested
(`rag-ingest --source docs`) for a self-referential demo, but making it the eval corpus would
mean every documentation edit silently rewrote the baseline.

### Two composition roots, not one

HTTP wiring lives in `api/dependencies.py` (with `api/lifespan.py` owning the client, since it
has no async context manager and must be closed explicitly). The CLIs are a second root by
necessity: their whole point is running the core without FastAPI, and `api/dependencies.py`
imports it. Both read the same `Settings`, so they cannot drift on *which* adapter is chosen.

## Consequences

- Swapping retrieval implementations is one branch in the composition root; the route, schemas,
  use case, and domain models were untouched, which is the claim ADR-001 made and this practice
  tested.
- Ingest is a batch concern with its own entry point rather than an HTTP endpoint, so the
  serving path has no ability to mutate the index.
- Practice 05 inherits the seams it needs: named vectors for hybrid search, payload fields
  already stored and indexed for filtering, and an eval gate sensitive enough to price each
  upgrade in recall.
