"""Testy powierzchni systemowej."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert set(body["modules"]) == {
        "cases",
        "ingest",
        "archive",
        "routing",
        "drafting",
        "anonymize",
        "inference",
        "audit",
    }


def test_meta(client: TestClient) -> None:
    body = client.get("/api/meta").json()
    assert body["offline"] is False
    assert body["module_modes"]["cases"] == "fake"


def test_openapi_available(client: TestClient) -> None:
    assert client.get("/api/openapi.json").status_code == 200
