"""Testy wniosków i maszyny stanów."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_returns_fixtures(client: TestClient) -> None:
    rows = client.get("/api/cases").json()
    assert len(rows) == 10
    assert rows[0]["case_number"].startswith("UDIP.1435.")


def test_urgency_covers_all_states(client: TestClient) -> None:
    rows = client.get("/api/cases").json()
    assert {"overdue", "today", "tomorrow", "soon", "normal", "closed"} <= {
        r["urgency"] for r in rows
    }


def test_sort_deadline_asc(client: TestClient) -> None:
    rows = client.get("/api/cases", params={"sort": "deadline_asc"}).json()
    deadlines = [r["deadline"] for r in rows]
    assert deadlines == sorted(deadlines)


def test_filter_by_status(client: TestClient) -> None:
    rows = client.get("/api/cases", params={"status": "nowy"}).json()
    assert rows and all(r["status"] == "nowy" for r in rows)


def test_search(client: TestClient) -> None:
    rows = client.get("/api/cases", params={"q": "wynagrodze"}).json()
    assert rows


def test_detail_and_history(client: TestClient) -> None:
    case_id = client.get("/api/cases").json()[0]["id"]
    detail = client.get(f"/api/cases/{case_id}").json()
    assert detail["id"] == case_id
    assert isinstance(client.get(f"/api/cases/{case_id}/history").json(), list)


def test_missing_case_returns_envelope(client: TestClient) -> None:
    resp = client.get("/api/cases/00000000-0000-4000-8000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


def test_transition_forward(client: TestClient) -> None:
    case_id = client.get("/api/cases", params={"status": "nowy"}).json()[0]["id"]
    resp = client.post(
        f"/api/cases/{case_id}/transition", json={"to": "zapytania_wyslane"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "zapytania_wyslane"


def test_transition_backward_requires_note(client: TestClient) -> None:
    case_id = client.get("/api/cases", params={"status": "nowy"}).json()[0]["id"]
    client.post(f"/api/cases/{case_id}/transition", json={"to": "zapytania_wyslane"})
    resp = client.post(f"/api/cases/{case_id}/transition", json={"to": "nowy"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_transition"


def test_create_case(client: TestClient) -> None:
    resp = client.post(
        "/api/cases",
        json={
            "case_number": "UDIP.1435.99.2026",
            "subject": "Wniosek testowy",
            "inflow_date": "2026-03-16",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "nowy"
    assert body["deadline"] == "2026-03-30"
