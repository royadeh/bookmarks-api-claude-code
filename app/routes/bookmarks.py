import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_connection
from app.repository import DuplicateURLError, insert_bookmark, list_bookmarks
from app.schemas import BookmarkCreate, BookmarkOut

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
def get_bookmarks(conn: sqlite3.Connection = Depends(get_connection)) -> list[BookmarkOut]:
    return list_bookmarks(conn)
