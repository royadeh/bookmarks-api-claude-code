import os

DEFAULT_DB_PATH = "bookmarks.db"


def get_db_path() -> str:
    return os.environ.get("BOOKMARKS_DB_PATH") or DEFAULT_DB_PATH
