import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_connection
from app.repository import DuplicateURLError, insert_bookmark, list_bookmarks
from app.schemas import BookmarkCreate, BookmarkOut, normalize_tag

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_bookmark(
    data: BookmarkCreate, conn: sqlite3.Connection = Depends(get_connection)
) -> BookmarkOut:
    try:
        return insert_bookmark(conn, data)
    except DuplicateURLError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Bookmark already exists") from None


@router.get("")
def get_bookmarks(
    tag: str | None = None, conn: sqlite3.Connection = Depends(get_connection)
) -> list[BookmarkOut]:
    if tag is None:
        return list_bookmarks(conn)
    normalized = normalize_tag(tag)
    if not normalized:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "tag must not be blank")
    return list_bookmarks(conn, normalized)
