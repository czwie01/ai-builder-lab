"""The model-metadata path is hermetic; the model itself is not.

`embedding_dimension` reads fastembed's static registry, so it needs no
download. Anything that constructs `FastEmbedEmbedder` does download
weights, which is why those tests live behind the eval/integration
markers instead.
"""

import pytest

from rag_api.adapters.fastembed_embedder import DEFAULT_MODEL, embedding_dimension


def test_reads_the_dimension_of_the_default_model() -> None:
    assert embedding_dimension(DEFAULT_MODEL) == 384


def test_unknown_model_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown embedding model"):
        embedding_dimension("nope/not-a-real-model")
