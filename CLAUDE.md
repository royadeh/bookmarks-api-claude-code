# Bookmarks API

FastAPI + SQLite service for saving and searching bookmarks.

## Commands
- Run: `uvicorn app.main:app --reload`
- Test: `pytest -q`

## Rules
- Write a failing test before implementing each feature.
- Keep functions small, add type hints everywhere.
- Read configuration from environment variables; never hardcode keys or commit `.env`.
- Don't change existing tests to make them pass; tell me if a test seems wrong.
- Commit after each working feature with a clear message.