"""Heading-aware markdown chunking.

Pure standard library, and deliberately boring: recursive/structural
splitting at roughly 400-500 tokens benchmarks *better* than
embedding-similarity "semantic" chunking at a fraction of the cost
(ADR-003), so the baseline stays simple. Practice 05 revisits chunking
with measurements rather than intuition.

Token budgets are approximated in characters (~4 characters per token).
The approximation is safe because the embedding model truncates at its
own sequence limit anyway, and every change here is answerable by the
eval gate.
"""

import re
from collections.abc import Iterator, Sequence

from rag_api.domain.models import DocumentChunk

DEFAULT_MAX_CHARS = 1800
DEFAULT_OVERLAP_CHARS = 200

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE = re.compile(r"^\s*(?:```|~~~)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def strip_frontmatter(text: str) -> str:
    """Drop a leading YAML frontmatter block, if present."""
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :]).lstrip("\n")
    return text


def iter_sections(text: str) -> Iterator[tuple[tuple[str, ...], str]]:
    """Yield (heading path, body) pairs, respecting fenced code blocks."""
    heading_stack: list[tuple[int, str]] = []
    body: list[str] = []
    in_fence = False

    def current_path() -> tuple[str, ...]:
        return tuple(title for _, title in heading_stack)

    for line in text.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            body.append(line)
            continue
        heading = None if in_fence else _HEADING.match(line)
        if heading is None:
            body.append(line)
            continue
        if any(part.strip() for part in body):
            yield current_path(), "\n".join(body).strip("\n")
        body = []
        level = len(heading.group(1))
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        heading_stack.append((level, heading.group(2)))

    if any(part.strip() for part in body):
        yield current_path(), "\n".join(body).strip("\n")


def _blocks(body: str) -> list[str]:
    """Split a section body into paragraph blocks, keeping fences atomic."""
    blocks: list[str] = []
    buffer: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            buffer.append(line)
            continue
        if not line.strip() and not in_fence:
            if any(part.strip() for part in buffer):
                blocks.append("\n".join(buffer).strip("\n"))
            buffer = []
            continue
        buffer.append(line)
    if any(part.strip() for part in buffer):
        blocks.append("\n".join(buffer).strip("\n"))
    return blocks


def _split_oversized(block: str, max_chars: int) -> list[str]:
    """Break a too-large prose block on sentence boundaries; never a fence."""
    if len(block) <= max_chars or _FENCE.match(block):
        return [block]
    parts: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(block):
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and len(candidate) > max_chars:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)
    return [part for part in parts if part]


def _pack(blocks: Sequence[str], max_chars: int, overlap_chars: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for block in blocks:
        if current and size + len(block) + 2 > max_chars:
            chunks.append("\n\n".join(current))
            carried: list[str] = []
            carried_size = 0
            for previous in reversed(current):
                if carried_size + len(previous) > overlap_chars:
                    break
                carried.insert(0, previous)
                carried_size += len(previous) + 2
            current = carried
            size = carried_size
        current.append(block)
        size += len(block) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def chunk_markdown(
    text: str,
    *,
    document_id: str,
    source_path: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[DocumentChunk]:
    """Split markdown into retrievable chunks that carry their heading trail."""
    chunks: list[DocumentChunk] = []
    for heading_path, body in iter_sections(strip_frontmatter(text)):
        blocks: list[str] = []
        for block in _blocks(body):
            blocks.extend(_split_oversized(block, max_chars))
        prefix = " > ".join(heading_path)
        for packed in _pack(blocks, max_chars, overlap_chars):
            chunk_text = f"{prefix}\n\n{packed}" if prefix else packed
            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    text=chunk_text,
                    source_path=source_path,
                    chunk_index=len(chunks),
                    heading_path=heading_path,
                )
            )
    return chunks
