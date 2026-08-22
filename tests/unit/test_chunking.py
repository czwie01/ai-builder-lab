from rag_api.application.chunking import chunk_markdown, strip_frontmatter

DOC = """---
title: Sample
---

# Hexagonal architecture

A port is an interface the core depends on.

## Adapters

An adapter implements a port from the outside.

```python
class QdrantRetriever:
    pass
```
"""


def test_strips_frontmatter() -> None:
    assert strip_frontmatter(DOC).startswith("# Hexagonal architecture")


def test_splits_on_headings_and_carries_the_heading_trail() -> None:
    chunks = chunk_markdown(DOC, document_id="doc-a", source_path="a.md")

    assert [chunk.heading_path for chunk in chunks] == [
        ("Hexagonal architecture",),
        ("Hexagonal architecture", "Adapters"),
    ]
    assert chunks[1].text.startswith("Hexagonal architecture > Adapters")


def test_chunk_indexes_increment_within_a_document() -> None:
    chunks = chunk_markdown(DOC, document_id="doc-a", source_path="a.md")

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert {chunk.document_id for chunk in chunks} == {"doc-a"}


def test_keeps_fenced_code_blocks_intact() -> None:
    chunks = chunk_markdown(DOC, document_id="doc-a", source_path="a.md")

    code_chunks = [chunk for chunk in chunks if "class QdrantRetriever" in chunk.text]
    assert len(code_chunks) == 1
    assert code_chunks[0].text.count("```") == 2


def test_headings_inside_fences_are_not_treated_as_headings() -> None:
    text = "# Real\n\n```\n# not a heading\n```\n"

    chunks = chunk_markdown(text, document_id="doc-a", source_path="a.md")

    assert len(chunks) == 1
    assert chunks[0].heading_path == ("Real",)


def test_long_sections_are_split_with_overlap() -> None:
    paragraphs = "\n\n".join(
        f"Paragraph number {index} about retrieval." * 3 for index in range(40)
    )
    text = f"# Long\n\n{paragraphs}\n"

    chunks = chunk_markdown(text, document_id="doc-a", source_path="a.md", max_chars=600)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 900 for chunk in chunks)
    first_tail = chunks[0].text.rsplit("\n\n", maxsplit=1)[-1]
    assert first_tail in chunks[1].text


def test_empty_document_yields_no_chunks() -> None:
    assert chunk_markdown("   \n\n  ", document_id="doc-a", source_path="a.md") == []
