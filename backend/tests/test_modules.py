"""Testy modułów delegujących do portów."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_departments(client: TestClient) -> None:
    rows = client.get("/api/routing/departments").json()
    assert len(rows) == 26
    assert all(r["id"] and r["name"] for r in rows)


def test_suggest(client: TestClient) -> None:
    rows = client.post(
        "/api/routing/suggest", json={"text": "wynagrodzenia pracowników", "k": 3}
    ).json()
    assert rows and rows[0]["confidence"] <= 1.0


def test_suggest_wskazuje_wydzial_organizacji_i_kadr(client: TestClient) -> None:
    """Atrapa routingu musi podpowiadać właściwą komórkę — to widać w demo.

    Wcześniej ogólne słowo „miasta” wygrywało z „wynagrodzenie” i pierwsza
    sugestia wskazywała Wydział Finansów.
    """
    rows = client.post(
        "/api/routing/suggest",
        json={"text": "Wynagrodzenia pracowników Urzędu Miasta w 2025 r.", "k": 3},
    ).json()
    assert rows[0]["department_id"] == "wok"
    assert rows[0]["confidence"] == max(row["confidence"] for row in rows)


def test_inquiry(client: TestClient) -> None:
    case = client.get("/api/cases").json()[0]
    body = client.post(
        "/api/routing/inquiry",
        json={"case_id": case["id"], "department_ids": ["wfin"]},
    ).json()
    assert body["addressees"]
    # Zapytanie powstaje z danych sprawy, nie ze stałego szablonu.
    assert case["case_number"] in body["body"]
    assert case["case_number"] in body["title"]


def test_archive_similar(client: TestClient) -> None:
    rows = client.post(
        "/api/archive/similar", json={"text": "wynagrodzenia nauczycieli", "k": 3}
    ).json()
    assert rows and rows[0]["score"] >= rows[-1]["score"]


def test_archive_detail(client: TestClient) -> None:
    body = client.get("/api/archive/a0001").json()
    assert body["archive_id"] == "a0001"


def test_anonymize_detect_and_apply(client: TestClient) -> None:
    text = "Jan Kowalski, PESEL 85041212345, tel. +48 601 234 567."
    spans = client.post("/api/anonymize/detect", json={"text": text}).json()
    assert spans
    result = client.post(
        "/api/anonymize/apply", json={"text": text, "spans": spans}
    ).json()
    assert "Kowalski" not in result["text"]
    assert result["removed_count"] == len(spans)


def test_anonymize_evaluate(client: TestClient) -> None:
    body = client.get("/api/anonymize/evaluate").json()
    assert 0.0 <= body["f1"] <= 1.0
    assert body["per_category"]


def test_inference(client: TestClient) -> None:
    assert client.get("/api/inference/health").json()["status"] == "ok"
    assert client.get("/api/inference/models").json()
    assert client.post("/api/inference/test").json()["ok"] is True


def test_drafting_flow(client: TestClient) -> None:
    case_id = client.get("/api/cases").json()[0]["id"]
    draft = client.post("/api/drafting/draft", json={"case_id": case_id}).json()
    assert draft["body"]
    assert client.get(f"/api/drafting/{case_id}").json()["id"] == draft["id"]
    patched = client.patch(
        f"/api/drafting/{draft['id']}", json={"body": "Nowa treść"}
    ).json()
    assert patched["body"] == "Nowa treść"
    export = client.get(f"/api/drafting/{draft['id']}/export", params={"fmt": "docx"})
    assert export.status_code == 200
    assert export.content[:2] == b"PK"


def test_documents_upload_and_parse(client: TestClient) -> None:

    from app.core.settings import settings

    path = settings.fixtures_dir / "documents" / "wniosek-01-wynagrodzenia.pdf"
    with path.open("rb") as handle:
        resp = client.post(
            "/api/documents",
            files={"file": (path.name, handle, "application/pdf")},
            data={"kind": "wniosek"},
        )
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["status"] == "indexed"
    assert doc["chunk_count"] > 0
    detail = client.get(f"/api/documents/{doc['id']}").json()
    assert "Bydgoszcz" in detail["text"]
    assert client.get(f"/api/documents/{doc['id']}/chunks").json()


def test_audit_empty(client: TestClient) -> None:
    assert client.get("/api/audit").json() == []
