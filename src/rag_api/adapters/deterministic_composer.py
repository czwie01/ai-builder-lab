"""Deterministic answer composer — Practice 01's stand-in for an LLM.

Assembles a grounded answer from the retrieved chunks so the endpoint's
contract is real end to end while staying offline and exactly testable.
"""

from collections.abc import Sequence

from rag_api.domain.models import RetrievedChunk


class DeterministicComposer:
    async def compose(self, question: str, chunks: Sequence[RetrievedChunk]) -> str:
        if not chunks:
            return "No relevant sources were found for this question."
        lead_sentence = chunks[0].text.split(". ")[0].rstrip(".")
        sources = ", ".join(chunk.document_id for chunk in chunks)
        return f"{lead_sentence}. (Based on {len(chunks)} source(s): {sources}.)"
