import logging
import re
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app

REQUEST_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
INTERNAL_DETAILS = "SELECT secret FROM users WHERE id = 1 in /Users/someone/app/db.py"


def app_with_failing_route() -> FastAPI:
    application = create_app()

    @application.get("/boom")
    def boom() -> None:
        raise RuntimeError(INTERNAL_DETAILS)

    return application


@pytest.fixture
def failing_client() -> Iterator[TestClient]:
    with TestClient(app_with_failing_route(), raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/health", None),
        ("GET", "/bookmarks", None),
        ("POST", "/bookmarks", {"url": "https://example.com"}),
        ("POST", "/bookmarks", {"url": "javascript:alert(1)"}),
        ("DELETE", "/bookmarks/999", None),
        ("GET", "/no-such-route", None),
    ],
)
def test_every_response_has_request_id(
    client: TestClient, method: str, path: str, body: dict | None
) -> None:
    response = client.request(method, path, json=body)

    assert REQUEST_ID_PATTERN.match(response.headers.get("X-Request-ID", ""))


def test_request_ids_are_unique(client: TestClient) -> None:
    first = client.get("/health").headers.get("X-Request-ID")
    second = client.get("/health").headers.get("X-Request-ID")

    assert first and second and first != second


def test_client_supplied_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "attacker\r\nvalue"})

    assert REQUEST_ID_PATTERN.match(response.headers.get("X-Request-ID", ""))


def test_internal_error_returns_generic_500_with_request_id(
    failing_client: TestClient,
) -> None:
    response = failing_client.get("/boom")

    assert response.status_code == 500
    request_id = response.headers.get("X-Request-ID", "")
    assert REQUEST_ID_PATTERN.match(request_id)
    assert response.json() == {"detail": "Internal server error", "request_id": request_id}


def test_internal_error_exposes_no_internal_details(failing_client: TestClient) -> None:
    response = failing_client.get("/boom")

    for leak in ["Traceback", "RuntimeError", "SELECT", "secret", "/Users", ".py"]:
        assert leak not in response.text


def test_internal_error_is_logged_with_request_id(
    failing_client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response = failing_client.get("/boom")

    request_id = response.headers.get("X-Request-ID", "<missing>")
    assert any(request_id in record.getMessage() for record in caplog.records)
