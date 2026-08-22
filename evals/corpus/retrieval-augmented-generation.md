# Retrieval-augmented generation

Retrieval-augmented generation answers a question by first fetching relevant source
material and then asking a language model to compose an answer that is grounded in it.
The model supplies fluency and synthesis; the retrieved passages supply the facts.

## Why ground an answer

A model asked to answer from memory alone will confidently invent details it has no
support for. Supplying the relevant passages at answer time narrows the model's job from
recall to reading comprehension, and it gives the reader something to check.

## Chunks

Source documents are split into chunks before indexing, because whole documents are too
coarse to retrieve precisely and single sentences are too small to carry context. Each
chunk is stored with the identifier of the document it came from, so an answer can point
back at its source.

## Citations

Citations reference document identifiers and relevance scores rather than exposing raw
chunk text to callers. Returning pointers instead of payload keeps the API contract small,
avoids leaking source material to clients that should not have it, and lets the caller
decide how much of the original to display.

## The limits of retrieval

Retrieval quality bounds answer quality: a passage that was never fetched cannot be used,
no matter how capable the model is. That is why retrieval is measured on its own, before
any generation quality is assessed.
