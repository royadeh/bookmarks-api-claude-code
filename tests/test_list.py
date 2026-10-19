from pathlib import Path

from fastapi.testclient import TestClient

from app.db import connect


def create(client: TestClient, url: str, tags: list[str] | None = None) -> dict:
    response = client.post("/bookmarks", json={"url": url, "tags": tags or []})
    assert response.status_code == 201
    return response.json()


def test_list_is_empty_initially(client: TestClient) -> None:
    response = client.get("/bookmarks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_bookmark_with_tags(client: TestClient) -> None:
    created = create(client, "https://example.com", ["web", "python"])

    assert client.get("/bookmarks").json() == [created]


def test_list_shows_empty_tags_for_untagged_bookmark(client: TestClient) -> None:
    create(client, "https://example.com")

    assert client.get("/bookmarks").json()[0]["tags"] == []


def test_list_is_newest_first(client: TestClient) -> None:
    first = create(client, "https://one.example.com", ["a"])
    second = create(client, "https://two.example.com")
    third = create(client, "https://three.example.com", ["b", "c"])

    assert client.get("/bookmarks").json() == [third, second, first]


def test_list_orders_by_created_at(client: TestClient, db_path: Path) -> None:
    with connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO bookmarks (id, url, created_at) VALUES "
            "(1, 'https://newer.example.com', '2026-02-01T00:00:00+00:00'), "
            "(2, 'https://older.example.com', '2026-01-01T00:00:00+00:00')"
        )

    urls = [item["url"] for item in client.get("/bookmarks").json()]

    assert urls == ["https://newer.example.com", "https://older.example.com"]


def test_list_keeps_tags_with_their_bookmark(client: TestClient) -> None:
    create(client, "https://one.example.com", ["shared", "only-one"])
    create(client, "https://two.example.com", ["shared"])

    tags_by_url = {item["url"]: item["tags"] for item in client.get("/bookmarks").json()}

    assert tags_by_url == {
        "https://one.example.com": ["shared", "only-one"],
        "https://two.example.com": ["shared"],
    }
