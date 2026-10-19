# Bookmarks API

A small FastAPI service for saving bookmarks, listing them, filtering them by tag and deleting them.
Data is stored in a local SQLite database.

## Setup and run

Requires Python 3.10 or later.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install ".[dev]"
uvicorn app.main:app --reload
```

The API runs at http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

The database file defaults to `bookmarks.db` in the current directory. To use a different file, set
`BOOKMARKS_DB_PATH` in the environment (see `.env.example`). The app reads environment variables only;
it does not load `.env` files.

```sh
BOOKMARKS_DB_PATH=/path/to/bookmarks.db uvicorn app.main:app --reload
```

## Run tests

```sh
pytest -q
```

Each test uses its own temporary database, so tests never touch `bookmarks.db`.

## Endpoints

| Method | Path | Description | Status codes |
|---|---|---|---|
| `GET` | `/health` | Health check | `200` |
| `POST` | `/bookmarks` | Create a bookmark from `{"url", "title"?, "tags"?}` | `201` created, `409` URL already saved, `422` invalid body or URL |
| `GET` | `/bookmarks` | List all bookmarks, newest first | `200` |
| `GET` | `/bookmarks?tag=python` | List bookmarks with that tag (case-insensitive) | `200`, `422` blank or repeated `tag` |
| `DELETE` | `/bookmarks/{id}` | Delete a bookmark and its tag links | `204` deleted, `404` not found, `422` non-integer ID |

- URLs must use `http` or `https`, have a host, contain no username or password, and be at most 2,048 characters.
  The scheme and host are lowercased; the path and query are kept as given.
- Tags are trimmed, lowercased and de-duplicated.
- Every response has an `X-Request-ID` header. An unexpected error returns `500` with
  `{"detail": "Internal server error", "request_id": "..."}`; the full error is logged with the same ID.

## Project structure

```
app/
  main.py              create_app(), startup schema creation, error handlers
  config.py            reads BOOKMARKS_DB_PATH
  db.py                SQLite schema and connections
  errors.py            X-Request-ID middleware and generic 500 handler
  schemas.py           request/response models, tag normalization
  urls.py              URL validation and normalization
  repository.py        SQL for create, list, filter and delete
  routes/bookmarks.py  /bookmarks endpoints
tests/                 pytest suite, one file per feature
pyproject.toml         dependencies and pytest settings
.env.example           documented environment variables
```

## Known limitations

- No pagination: `GET /bookmarks` returns every bookmark.
- Deleting a bookmark removes its tag links, but tag names no longer used by any bookmark stay in the
  `tags` table. They are not visible through the API.
- Search accepts one tag per request; there is no multi-tag filter.
