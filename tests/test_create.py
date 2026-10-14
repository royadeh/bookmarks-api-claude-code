import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connect
from app.main import create_app


def bookmark_count(db_path: Path) -> int:
    with connect(str(db_path)) as conn:
        return conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]


def test_create_returns_201_with_bookmark(client: TestClient) -> None:
    response = client.post(
        "/bookmarks",
        json={"url": "https://example.com", "title": "Example", "tags": ["python"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["url"] == "https://example.com"
    assert body["title"] == "Example"
    assert body["tags"] == ["python"]
    assert body["created_at"]


def test_create_without_title_or_tags(client: TestClient) -> None:
    response = client.post("/bookmarks", json={"url": "https://example.com"})

    assert response.status_code == 201
    assert response.json()["title"] is None
    assert response.json()["tags"] == []


def test_create_normalizes_tags(client: TestClient) -> None:
    response = client.post(
        "/bookmarks",
        json={"url": "https://example.com", "tags": [" Python ", "python", "WEB", "  "]},
    )

    assert response.json()["tags"] == ["python", "web"]


@pytest.mark.parametrize(
    ("submitted", "stored"),
    [
        ("https://example.com", "https://example.com"),
        ("http://example.com/path?q=1", "http://example.com/path?q=1"),
        ("HTTPS://Example.com", "https://example.com"),
        ("  https://EXAMPLE.com/A/B?Q=C#Frag  ", "https://example.com/A/B?Q=C#Frag"),
        ("https://Example.com:8443/x", "https://example.com:8443/x"),
    ],
)
def test_create_accepts_and_normalizes_url(
    client: TestClient, submitted: str, stored: str
) -> None:
    response = client.post("/bookmarks", json={"url": submitted})

    assert response.status_code == 201
    assert response.json()["url"] == stored


REJECTED_URLS = [
    "javascript:alert(1)",
    "JavaScript:alert(1)",
    "  javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "file:///etc/passwd",
    "ftp://example.com",
    "mailto:someone@example.com",
    "https://",
    "example.com",
    "",
    "https://example.com/" + "a" * 2029,
]


@pytest.mark.parametrize("url", REJECTED_URLS)
def test_create_rejects_non_http_url(
    client: TestClient, db_path: Path, url: str
) -> None:
    response = client.post("/bookmarks", json={"url": url})

    assert response.status_code == 422
    assert bookmark_count(db_path) == 0


def test_rejected_url_is_not_echoed(client: TestClient) -> None:
    response = client.post("/bookmarks", json={"url": "javascript:alert(1)"})

    assert "alert(1)" not in response.text


def test_url_at_max_length_is_accepted(client: TestClient) -> None:
    url = "https://example.com/" + "a" * 2028

    assert len(url) == 2048
    assert client.post("/bookmarks", json={"url": url}).status_code == 201


def test_create_requires_url(client: TestClient) -> None:
    response = client.post("/bookmarks", json={"title": "No URL"})

    assert response.status_code == 422


def test_duplicate_url_returns_409(client: TestClient) -> None:
    client.post("/bookmarks", json={"url": "https://example.com"})

    response = client.post("/bookmarks", json={"url": "https://example.com"})

    assert response.status_code == 409


def test_duplicate_after_normalization_returns_409(
    client: TestClient, db_path: Path
) -> None:
    first = client.post("/bookmarks", json={"url": "HTTPS://Example.com"})
    second = client.post("/bookmarks", json={"url": "https://example.com"})

    assert first.status_code == 201
    assert second.status_code == 409
    assert bookmark_count(db_path) == 1


def test_paths_differing_in_case_are_distinct(client: TestClient) -> None:
    first = client.post("/bookmarks", json={"url": "https://example.com/A"})
    second = client.post("/bookmarks", json={"url": "https://example.com/a"})

    assert first.status_code == 201
    assert second.status_code == 201


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@example.com",
        "https://user@example.com",
        "https://:pass@example.com",
        "https://@example.com",
        "HTTP://User:Pass@Example.com/path",
    ],
)
def test_create_rejects_url_with_credentials(
    client: TestClient, db_path: Path, url: str
) -> None:
    response = client.post("/bookmarks", json={"url": url})

    assert response.status_code == 422
    assert "pass" not in response.text.lower()
    assert bookmark_count(db_path) == 0


def test_other_integrity_error_is_not_reported_as_duplicate(db_path: Path) -> None:
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        with connect(str(db_path)) as conn:
            conn.execute(
                "CREATE TRIGGER fail_tag_link BEFORE INSERT ON bookmark_tags "
                "BEGIN SELECT RAISE(ABORT, 'forced failure'); END"
            )

        response = client.post(
            "/bookmarks", json={"url": "https://example.com", "tags": ["python"]}
        )

    assert response.status_code == 500
    assert "forced failure" not in response.text
    assert bookmark_count(db_path) == 0
