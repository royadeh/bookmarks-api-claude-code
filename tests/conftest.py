from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(autouse=True)
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "test.db"
    monkeypatch.setenv("BOOKMARKS_DB_PATH", str(path))
    return path


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Entering the context manager runs the app's lifespan, which creates the schema.
    with TestClient(create_app()) as test_client:
        yield test_client
