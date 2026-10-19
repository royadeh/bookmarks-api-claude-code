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


## How I built this

I built this over 2 days as a practice project for working with Claude Code. I used a test-first workflow with one small step at a time, and I reviewed everything before it reached `main`. The repo ends with 78 tests across 4 pull requests.

### How I worked with Claude Code

- **Rules first.** I wrote a `CLAUDE.md` before any code: write a failing test before each feature, keep functions small with type hints, read config from environment variables, never change a test just to make it pass, and commit after each working feature.
- **Plan before code.** Claude proposed a 7-step plan and I changed it before approving it.
- **One step at a time.** Each step followed the same loop: failing test, implementation, run the tests, review the diff, commit. From step 4 on, each feature got its own branch and pull request.
- **Co-authorship is visible.** Commits Claude made carry a `Co-Authored-By` line, and commits I made myself don't.

### What I decided

- Only `http` and `https` URLs are accepted, checked with an explicit allow-list so the rule lives in my code and not in a library default.
- URLs containing a username or password are rejected, so credentials never end up in the database.
- Config is read with `os.environ`, not an extra dependency, since there's only one setting.
- Tags live in their own table with a join table, so tag search is a plain join and deletes clean up automatically.
- A duplicate URL returns `409`, but only for the unique-URL violation. Any other database error becomes a generic `500`.
- I skipped pagination, PATCH and multi-tag search on purpose to keep each step small.
- Searching with more than one `?tag=` returns `422` instead of silently using the last one.

### What I checked myself

- I read every diff before accepting it, and I wrote my own comments in each pull request.
- I confirmed each new test fails before the feature exists.
- Several times, Claude's first-draft tests passed without testing anything. For example, a "not found" test passed because FastAPI's default `404` happened to match. I had them tightened until they failed for the right reason.
- I broke the startup hook on purpose to confirm the test that checks table creation really fails without it.
- I tested the API by hand through the `/docs` page, and compared the server log with the SQLite database to check what was actually stored.
- For the `500` handler, Claude temporarily made it leak the error text to prove the test would catch a leak, then removed it. It also told me about a failed undo attempt before fixing it.

## Known limitations

- No pagination: `GET /bookmarks` returns every bookmark.
- Deleting a bookmark removes its tag links, but tag names no longer used by any bookmark stay in the `tags` table. They are not visible through the API.
- Search accepts one tag per request; there is no multi-tag filter.
- The duplicate-URL check matches SQLite's error text, so a change in that wording would turn duplicates into `500` errors. A test would catch it.
- Only `500` responses include the request ID in the body; other errors carry it in the `X-Request-ID`
  header only.
