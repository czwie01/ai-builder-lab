# Vector search

Vector search finds material by meaning rather than by matching words. Text is converted
into a numeric vector, and passages whose vectors lie close to the query's vector are
returned as candidates.

## Embeddings

An embedding model maps a piece of text to a fixed-length array of numbers, positioning
texts that mean similar things near one another. Because the mapping is learned rather
than lexical, a question and a passage can match even when they share no vocabulary,
which is exactly where keyword matching fails.

## Cosine similarity

Closeness is usually measured as the cosine of the angle between two vectors. When the
model already returns unit-length vectors, the cosine reduces to a dot product, so the
choice of distance metric must match how the model normalises its output or the ranking
comes out inverted.

## Vector databases

A vector database stores vectors alongside a payload of metadata and answers
nearest-neighbour queries over them. Approximate indexes trade a little accuracy for a
large speed gain on big collections; an exact scan is fine for small ones and is what
embedded test modes typically do.

## Keyword search still matters

Dense retrieval is weak exactly where lexical matching is strong: rare identifiers, exact
names, product codes. Running both and fusing their rankings recovers what either misses
on its own, which is why hybrid search is usually the first upgrade after a dense
baseline, ahead of any reranking stage.
