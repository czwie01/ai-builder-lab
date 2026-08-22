"""The dry-run path needs no service and no model, so it is testable here."""

import pytest

from rag_api import ingest_cli


def test_dry_run_reports_chunk_counts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["rag-ingest", "--source", "evals/corpus", "--dry-run"])

    assert ingest_cli.main() == 0

    output = capsys.readouterr().out
    assert "document(s) ->" in output
    assert "dry run" in output


def test_missing_corpus_directory_is_an_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["rag-ingest", "--source", "does/not/exist"])

    assert ingest_cli.main() == 1
    assert "no such corpus directory" in capsys.readouterr().err
