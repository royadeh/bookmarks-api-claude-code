import pytest

from app.config import DEFAULT_DB_PATH, get_db_path


def test_db_path_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKMARKS_DB_PATH", "/tmp/custom.db")

    assert get_db_path() == "/tmp/custom.db"


def test_db_path_defaults_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BOOKMARKS_DB_PATH", raising=False)

    assert get_db_path() == DEFAULT_DB_PATH


def test_db_path_defaults_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOOKMARKS_DB_PATH", "")

    assert get_db_path() == DEFAULT_DB_PATH
