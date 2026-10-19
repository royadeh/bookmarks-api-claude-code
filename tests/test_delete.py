from pathlib import Path

from fastapi.testclient import TestClient

from app.db import connect


def create(client: TestClient, url: str, tags: list[str] | None = None) -> dict:
    response = client.post("/bookmarks", json={"url": url, "tags": tags or []})
    assert response.status_code == 201
    return response.json()


def tag_link_count(db_path: Path, bookmark_id: int) -> int:
    with connect(str(db_path)) as conn:
        query = "SELECT COUNT(*) FROM bookmark_tags WHERE bookmark_id = ?"
        return conn.execute(query, (bookmark_id,)).fetchone()[0]


def test_delete_returns_204_with_empty_body(client: TestClient) -> None:
    bookmark = create(client, "https://example.com")

    response = client.delete(f"/bookmarks/{bookmark['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_deleted_bookmark_disappears_from_list(client: TestClient) -> None:
    kept = create(client, "https://kept.example.com")
    removed = create(client, "https://removed.example.com")

    client.delete(f"/bookmarks/{removed['id']}")

    assert client.get("/bookmarks").json() == [kept]


def test_delete_removes_only_its_tag_links(client: TestClient, db_path: Path) -> None:
    kept = create(client, "https://kept.example.com", ["python"])
    removed = create(client, "https://removed.example.com", ["python", "web"])

    client.delete(f"/bookmarks/{removed['id']}")

    assert tag_link_count(db_path, removed["id"]) == 0
    assert tag_link_count(db_path, kept["id"]) == 1


def test_deleted_bookmark_disappears_from_tag_search(client: TestClient) -> None:
    kept = create(client, "https://kept.example.com", ["python"])
    removed = create(client, "https://removed.example.com", ["python"])

    client.delete(f"/bookmarks/{removed['id']}")

    assert client.get("/bookmarks", params={"tag": "python"}).json() == [kept]


def test_delete_missing_id_returns_404(client: TestClient) -> None:
    response = client.delete("/bookmarks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Bookmark not found"}


def test_delete_twice_returns_404(client: TestClient) -> None:
    bookmark = create(client, "https://example.com")
    client.delete(f"/bookmarks/{bookmark['id']}")

    response = client.delete(f"/bookmarks/{bookmark['id']}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Bookmark not found"}


def test_delete_non_integer_id_returns_422(client: TestClient) -> None:
    response = client.delete("/bookmarks/not-a-number")

    assert response.status_code == 422
    assert "not-a-number" not in response.text


def test_url_can_be_saved_again_after_delete(client: TestClient) -> None:
    bookmark = create(client, "https://example.com")
    client.delete(f"/bookmarks/{bookmark['id']}")

    response = client.post("/bookmarks", json={"url": "https://example.com"})

    assert response.status_code == 201
