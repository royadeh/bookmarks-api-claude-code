import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connect, init_schema
from app.main import create_app

EXPECTED_TABLES = {"bookmarks", "tags", "bookmark_tags"}


def table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {row[0] for row in rows}


def test_init_schema_creates_tables(db_path: Path) -> None:
    with connect(str(db_path)) as conn:
        init_schema(conn)

        assert EXPECTED_TABLES <= table_names(conn)


def test_init_schema_is_idempotent(db_path: Path) -> None:
    with connect(str(db_path)) as conn:
        init_schema(conn)
        init_schema(conn)

        assert EXPECTED_TABLES <= table_names(conn)


def test_connect_enables_foreign_keys(db_path: Path) -> None:
    with connect(str(db_path)) as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_bookmark_url_is_unique(db_path: Path) -> None:
    with connect(str(db_path)) as conn:
        init_schema(conn)
        insert = "INSERT INTO bookmarks (url, created_at) VALUES (?, ?)"
        conn.execute(insert, ("https://example.com", "2026-01-01T00:00:00Z"))

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(insert, ("https://example.com", "2026-01-01T00:00:00Z"))


def test_deleting_bookmark_removes_its_tag_links(db_path: Path) -> None:
    with connect(str(db_path)) as conn:
        init_schema(conn)
        conn.execute(
            "INSERT INTO bookmarks (id, url, created_at) VALUES (1, 'https://example.com', 'now')"
        )
        conn.execute("INSERT INTO tags (id, name) VALUES (1, 'python')")
        conn.execute("INSERT INTO bookmark_tags (bookmark_id, tag_id) VALUES (1, 1)")

        conn.execute("DELETE FROM bookmarks WHERE id = 1")

        assert conn.execute("SELECT COUNT(*) FROM bookmark_tags").fetchone()[0] == 0


def test_app_startup_creates_schema_at_env_path(db_path: Path) -> None:
    with TestClient(create_app()):
        pass

    with connect(str(db_path)) as conn:
        assert EXPECTED_TABLES <= table_names(conn)
