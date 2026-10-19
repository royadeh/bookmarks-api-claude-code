import sqlite3
from datetime import datetime, timezone

from app.schemas import BookmarkCreate, BookmarkOut


UNIQUE_URL_VIOLATION = "UNIQUE constraint failed: bookmarks.url"


class DuplicateURLError(Exception):
    pass


def insert_bookmark(conn: sqlite3.Connection, data: BookmarkCreate) -> BookmarkOut:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with conn:
            bookmark_id = _insert_row(conn, data, created_at)
            for name in data.tags:
                _link_tag(conn, bookmark_id, name)
    except sqlite3.IntegrityError as error:
        if UNIQUE_URL_VIOLATION in str(error):
            raise DuplicateURLError from error
        raise
    return BookmarkOut(id=bookmark_id, created_at=created_at, **data.model_dump())


def _insert_row(conn: sqlite3.Connection, data: BookmarkCreate, created_at: str) -> int:
    cursor = conn.execute(
        "INSERT INTO bookmarks (url, title, created_at) VALUES (?, ?, ?)",
        (data.url, data.title, created_at),
    )
    return int(cursor.lastrowid)


def _link_tag(conn: sqlite3.Connection, bookmark_id: int, name: str) -> None:
    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
    conn.execute(
        "INSERT INTO bookmark_tags (bookmark_id, tag_id) "
        "SELECT ?, id FROM tags WHERE name = ?",
        (bookmark_id, name),
    )


LIST_SQL = "SELECT id, url, title, created_at FROM bookmarks"
TAG_FILTER_SQL = (
    " WHERE id IN (SELECT bt.bookmark_id FROM bookmark_tags bt"
    " JOIN tags t ON t.id = bt.tag_id WHERE t.name = ?)"
)
NEWEST_FIRST_SQL = " ORDER BY created_at DESC, id DESC"


def list_bookmarks(conn: sqlite3.Connection, tag: str | None = None) -> list[BookmarkOut]:
    if tag is None:
        rows = conn.execute(LIST_SQL + NEWEST_FIRST_SQL).fetchall()
    else:
        rows = conn.execute(LIST_SQL + TAG_FILTER_SQL + NEWEST_FIRST_SQL, (tag,)).fetchall()
    tags = _tags_by_bookmark(conn)
    return [BookmarkOut(**dict(row), tags=tags.get(row["id"], [])) for row in rows]


def _tags_by_bookmark(conn: sqlite3.Connection) -> dict[int, list[str]]:
    rows = conn.execute(
        "SELECT bt.bookmark_id, t.name FROM bookmark_tags bt "
        "JOIN tags t ON t.id = bt.tag_id ORDER BY bt.rowid"
    )
    tags: dict[int, list[str]] = {}
    for bookmark_id, name in rows:
        tags.setdefault(bookmark_id, []).append(name)
    return tags
