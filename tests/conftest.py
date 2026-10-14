from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "test.db"
    monkeypatch.setenv("BOOKMARKS_DB_PATH", str(path))
    return path
