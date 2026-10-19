from fastapi.testclient import TestClient


def create(client: TestClient, url: str, tags: list[str]) -> dict:
    response = client.post("/bookmarks", json={"url": url, "tags": tags})
    assert response.status_code == 201
    return response.json()


def search(client: TestClient, tag: str) -> list[dict]:
    response = client.get("/bookmarks", params={"tag": tag})
    assert response.status_code == 200
    return response.json()


def test_tag_filter_returns_only_matching_bookmarks(client: TestClient) -> None:
    python = create(client, "https://python.example.com", ["python"])
    create(client, "https://rust.example.com", ["rust"])

    assert search(client, "python") == [python]


def test_tag_filter_is_newest_first(client: TestClient) -> None:
    older = create(client, "https://one.example.com", ["python"])
    create(client, "https://two.example.com", ["rust"])
    newer = create(client, "https://three.example.com", ["python", "web"])

    assert search(client, "python") == [newer, older]


def test_tag_filter_is_case_insensitive(client: TestClient) -> None:
    created = create(client, "https://example.com", ["Python"])
    create(client, "https://other.example.com", ["rust"])

    assert search(client, "PYTHON") == [created]
    assert search(client, "python") == [created]


def test_tag_filter_ignores_surrounding_whitespace(client: TestClient) -> None:
    created = create(client, "https://example.com", ["python"])
    create(client, "https://other.example.com", ["rust"])

    assert search(client, "  python ") == [created]


def test_tag_filter_returns_all_tags_of_each_match(client: TestClient) -> None:
    create(client, "https://example.com", ["web", "python", "api"])
    create(client, "https://other.example.com", ["rust"])

    assert search(client, "python")[0]["tags"] == ["web", "python", "api"]


def test_tag_filter_with_no_match_returns_empty_list(client: TestClient) -> None:
    create(client, "https://example.com", ["python"])

    assert search(client, "rust") == []


def test_tag_filter_requires_exact_tag(client: TestClient) -> None:
    create(client, "https://example.com", ["python"])

    assert search(client, "py") == []
    assert search(client, "py%") == []


def test_tag_filter_treats_input_as_data(client: TestClient) -> None:
    create(client, "https://example.com", ["python"])

    assert search(client, "' OR 1=1 --") == []


def test_blank_tag_returns_422(client: TestClient) -> None:
    response = client.get("/bookmarks", params={"tag": "   "})

    assert response.status_code == 422


def test_repeated_tag_parameter_returns_422(client: TestClient) -> None:
    create(client, "https://example.com", ["python"])

    response = client.get("/bookmarks?tag=python&tag=secret-value")

    assert response.status_code == 422
    assert "secret-value" not in response.text


def test_same_tag_repeated_returns_422(client: TestClient) -> None:
    response = client.get("/bookmarks?tag=python&tag=python")

    assert response.status_code == 422
