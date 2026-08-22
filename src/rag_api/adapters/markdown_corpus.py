"""Filesystem corpus loading.

Reading files is infrastructure, so it lives in an adapter rather than
in the use case. Document ids are the corpus-relative path without the
extension, which keeps them unique across subdirectories and readable
when they show up in citations.
"""

from pathlib import Path

from rag_api.domain.models import SourceDocument


def load_markdown_documents(root: Path) -> list[SourceDocument]:
    """Load every markdown file under `root`, sorted for reproducibility."""
    return [
        SourceDocument(
            document_id=path.relative_to(root).with_suffix("").as_posix(),
            source_path=path.relative_to(root).as_posix(),
            text=path.read_text(encoding="utf-8"),
        )
        for path in sorted(root.rglob("*.md"))
    ]
