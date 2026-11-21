"""Testy adaptera dokumentów: parsowanie, chunkowanie i magazyn w SQLite."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.adapters.real.documents import (
    CHUNK_CHARS,
    CHUNK_OVERLAP,
    PdfDocxParser,
    SqlDocumentStore,
)
from app.contracts import DocumentKind, DocumentStatus
from app.core import container
from app.core.errors import Conflict, NotFound, UnsupportedMedia
from app.core.settings import settings
from app.main import app

DOCUMENTS = settings.fixtures_dir / "documents"
STATUTES = settings.fixtures_dir / "statutes"


# ─────────────────────────────── fixtures ──────────────────────────────────
@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    return create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )


@pytest.fixture
def store(engine: Engine, tmp_path: Path) -> SqlDocumentStore:
    return SqlDocumentStore(engine=engine, upload_dir=tmp_path / "uploads")


@pytest.fixture
def client(store: SqlDocumentStore) -> Iterator[TestClient]:
    app.dependency_overrides[container.get_documents] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _upload(
    client: TestClient,
    path: Path,
    *,
    kind: str = "wniosek",
    case_id: str | None = None,
    content_type: str = "application/octet-stream",
) -> httpx.Response:
    with path.open("rb") as handle:
        data = {"kind": kind}
        if case_id is not None:
            data["case_id"] = case_id
        return client.post(
            "/api/documents",
            files={"file": (path.name, handle, content_type)},
            data=data,
        )


def _blank_pdf() -> bytes:
    """PDF bez warstwy tekstowej — odpowiednik skanu."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.rect(10, 10, 100, 100)
    return bytes(pdf.output())


def _text_pdf(pages: list[str]) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for content in pages:
        pdf.add_page()
        pdf.multi_cell(0, 8, content)
    return bytes(pdf.output())


# ──────────────────────────────── upload ───────────────────────────────────
def test_upload_pdf_indexes_polish_text(client: TestClient) -> None:
    response = _upload(client, DOCUMENTS / "wniosek-01-wynagrodzenia.pdf")
    assert response.status_code == 201
    document = response.json()
    assert document["status"] == "indexed"
    assert document["error"] is None
    assert document["kind"] == "wniosek"
    assert document["mime"] == "application/pdf"
    assert document["chunk_count"] > 0
    assert document["size_bytes"] > 0

    detail = client.get(f"/api/documents/{document['id']}").json()
    assert detail["page_count"] == 1
    assert "Bydgoszcz" in detail["text"]
    assert "Wysokości wynagrodzeń" in detail["text"]
    assert "UDOSTĘPNIENIE INFORMACJI PUBLICZNEJ" in detail["text"]

    chunks = client.get(f"/api/documents/{document['id']}/chunks").json()
    assert len(chunks) == document["chunk_count"]
    assert all(chunk["page"] == 1 for chunk in chunks)
    assert all(chunk["text"].strip() for chunk in chunks)


def test_upload_docx_indexes_text_with_section(client: TestClient) -> None:
    response = _upload(client, DOCUMENTS / "wniosek-03-wycinka-drzew.docx")
    assert response.status_code == 201
    document = response.json()
    assert document["status"] == "indexed"
    assert document["mime"].endswith("wordprocessingml.document")

    detail = client.get(f"/api/documents/{document['id']}").json()
    assert "zezwoleń na usunięcie drzew" in detail["text"]

    chunks = client.get(f"/api/documents/{document['id']}/chunks").json()
    assert chunks
    assert all(chunk["section"] for chunk in chunks)


def test_upload_txt_statute(client: TestClient) -> None:
    response = _upload(client, STATUTES / "udip.txt", kind="ustawa")
    assert response.status_code == 201
    document = response.json()
    assert document["status"] == "indexed"
    assert document["chunk_count"] > 1
    detail = client.get(f"/api/documents/{document['id']}").json()
    assert "Art. 13" in detail["text"]


def test_upload_unsupported_extension_returns_415(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("wirus.exe", b"MZ\x90\x00binarny", "application/octet-stream")},
        data={"kind": "inne"},
    )
    assert response.status_code == 415
    body = response.json()
    assert body["code"] == "unsupported_media_type"
    assert ".exe" in body["message"]
    assert "PDF" in body["message"]
    assert client.get("/api/documents").json() == []


def test_upload_pdf_with_foreign_content_returns_415(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("udawany.pdf", b"to nie jest pdf", "application/pdf")},
        data={"kind": "inne"},
    )
    assert response.status_code == 415
    assert "nie jest dokumentem PDF" in response.json()["message"]


def test_upload_pdf_without_text_layer_is_reported(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("skan.pdf", _blank_pdf(), "application/pdf")},
        data={"kind": "wniosek"},
    )
    assert response.status_code == 201
    document = response.json()
    assert document["status"] == "failed"
    assert document["chunk_count"] == 0
    assert "warstwy tekstowej" in document["error"]
    assert "OCR" in document["error"]

    detail = client.get(f"/api/documents/{document['id']}").json()
    assert detail["text"] == ""
    assert client.get(f"/api/documents/{document['id']}/chunks").json() == []


def test_upload_too_large_returns_413(client: TestClient) -> None:
    blob = b"x" * (settings.max_upload_bytes + 1)
    response = client.post(
        "/api/documents",
        files={"file": ("duzy.txt", blob, "text/plain")},
        data={"kind": "inne"},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "payload_too_large"


def test_upload_assigns_case(client: TestClient) -> None:
    case_id = str(uuid4())
    response = _upload(
        client, DOCUMENTS / "wniosek-02-najem-lokali.pdf", case_id=case_id
    )
    assert response.status_code == 201
    assert response.json()["case_id"] == case_id
    rows = client.get("/api/documents", params={"case_id": case_id}).json()
    assert len(rows) == 1
    assert client.get("/api/documents", params={"case_id": str(uuid4())}).json() == []


# ──────────────────────────────── parser ───────────────────────────────────
def test_parser_rejects_unsupported_format() -> None:
    with pytest.raises(UnsupportedMedia) as error:
        PdfDocxParser().parse(b"MZ", "program.exe")
    assert ".exe" in error.value.message
    assert "PDF" in error.value.message


def test_parser_rejects_empty_file() -> None:
    with pytest.raises(UnsupportedMedia):
        PdfDocxParser().parse(b"", "pusty.txt")


def test_parser_reports_scan_without_text_layer() -> None:
    with pytest.raises(UnsupportedMedia) as error:
        PdfDocxParser().parse(_blank_pdf(), "skan.pdf")
    assert "warstwy tekstowej" in error.value.message


def test_parser_numbers_pages() -> None:
    blob = _text_pdf(["Pierwsza strona dokumentu.", "Druga strona dokumentu."])
    text, page_count = PdfDocxParser().parse(blob, "dwustronny.pdf")
    assert page_count == 2
    assert "Pierwsza strona" in text
    assert "Druga strona" in text
    assert text.count("\f") == 2

    chunks = PdfDocxParser().chunk(text, document_id=uuid4())
    assert {chunk.page for chunk in chunks} == {1, 2}


def test_chunking_respects_size_overlap_and_offsets() -> None:
    paragraph = (
        "Informacja publiczna jest udostępniana na wniosek. "
        "Organ nie może żądać wykazania interesu prawnego. "
    )
    text = "\n\n".join(paragraph * 3 for _ in range(12))
    document_id = uuid4()
    chunks = PdfDocxParser().chunk(text, document_id=document_id)

    assert len(chunks) >= 3
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.document_id == document_id for chunk in chunks)
    assert all(len(chunk.text) <= CHUNK_CHARS for chunk in chunks)
    assert all(chunk.page is not None or chunk.section for chunk in chunks)
    assert chunks[0].text.startswith("Informacja publiczna")
    assert chunks[-1].text.endswith("interesu prawnego.")

    for previous, current in zip(chunks, chunks[1:], strict=False):
        overlap = previous.text[-CHUNK_OVERLAP:]
        assert overlap[-40:] in current.text


def test_chunking_cuts_at_paragraph_boundary() -> None:
    first = "A" * 500
    second = "B" * 500
    chunks = PdfDocxParser().chunk(f"{first}\n\n{second}", document_id=uuid4())
    assert len(chunks) == 2
    assert chunks[0].text == first
    assert chunks[1].text == second


def test_chunking_keeps_section_for_statute() -> None:
    text = (STATUTES / "udip.txt").read_text(encoding="utf-8")
    chunks = PdfDocxParser().chunk(text, document_id=uuid4())
    assert len(chunks) > 1
    assert all(chunk.section for chunk in chunks)
    assert any("Art." in (chunk.section or "") for chunk in chunks)


# ──────────────────────────────── magazyn ──────────────────────────────────
def test_delete_removes_document_chunks_and_file(
    client: TestClient, store: SqlDocumentStore
) -> None:
    document = _upload(client, DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").json()
    stored = list(store.upload_dir.iterdir())
    assert len(stored) == 1
    assert stored[0].name == f"{document['id']}.pdf"

    assert client.delete(f"/api/documents/{document['id']}").status_code == 204
    assert client.get("/api/documents").json() == []
    assert client.get(f"/api/documents/{document['id']}").status_code == 404
    assert list(store.upload_dir.iterdir()) == []


def test_delete_missing_document_returns_404(client: TestClient) -> None:
    assert client.delete(f"/api/documents/{uuid4()}").status_code == 404
    assert client.get(f"/api/documents/{uuid4()}").status_code == 404


def test_reindex_rebuilds_chunks(client: TestClient) -> None:
    document = _upload(client, DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").json()
    before = client.get(f"/api/documents/{document['id']}/chunks").json()

    response = client.post(f"/api/documents/{document['id']}/reindex")
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"
    assert response.json()["chunk_count"] == len(before)

    after = client.get(f"/api/documents/{document['id']}/chunks").json()
    assert [chunk["text"] for chunk in after] == [chunk["text"] for chunk in before]


def test_reindex_recovers_document_without_text(
    client: TestClient, store: SqlDocumentStore
) -> None:
    document = client.post(
        "/api/documents",
        files={"file": ("skan.pdf", _blank_pdf(), "application/pdf")},
        data={"kind": "wniosek"},
    ).json()
    assert document["status"] == "failed"

    # urzędnik wgrywa ten sam plik po rozpoznaniu tekstu (OCR)
    stored = store.upload_dir / f"{document['id']}.pdf"
    stored.write_bytes(_text_pdf(["Rozpoznany tekst wniosku."]))

    response = client.post(f"/api/documents/{document['id']}/reindex")
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"
    assert response.json()["error"] is None
    assert response.json()["chunk_count"] == 1
    detail = client.get(f"/api/documents/{document['id']}").json()
    assert "Rozpoznany tekst" in detail["text"]


def test_reindex_without_source_file_returns_409(
    client: TestClient, store: SqlDocumentStore
) -> None:
    document = _upload(client, DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").json()
    (store.upload_dir / f"{document['id']}.pdf").unlink()
    response = client.post(f"/api/documents/{document['id']}/reindex")
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_reindex_marks_document_failed_when_file_is_unreadable(
    client: TestClient, store: SqlDocumentStore
) -> None:
    document = _upload(client, DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").json()
    assert document["status"] == "indexed"

    (store.upload_dir / f"{document['id']}.pdf").write_bytes(_blank_pdf())
    response = client.post(f"/api/documents/{document['id']}/reindex")
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["chunk_count"] == 0
    assert "warstwy tekstowej" in response.json()["error"]
    assert client.get(f"/api/documents/{document['id']}/chunks").json() == []


def test_documents_persist_between_store_instances(
    engine: Engine, tmp_path: Path
) -> None:
    first = SqlDocumentStore(engine=engine, upload_dir=tmp_path / "uploads")
    document = first.create(
        blob=(DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").read_bytes(),
        filename="wniosek-01-wynagrodzenia.pdf",
        kind=DocumentKind.WNIOSEK,
    )

    # nowa instancja = nowy proces po odświeżeniu strony
    second = SqlDocumentStore(engine=engine, upload_dir=tmp_path / "uploads")
    rows = second.list()
    assert [row.id for row in rows] == [document.id]
    assert "Bydgoszcz" in second.get(document.id).text
    assert second.chunks(document.id)


def test_reupload_statute_replaces_entry(store: SqlDocumentStore) -> None:
    blob = (STATUTES / "udip.txt").read_bytes()
    first = store.create(blob=blob, filename="udip.txt", kind=DocumentKind.USTAWA)
    second = store.create(blob=blob, filename="udip.txt", kind=DocumentKind.USTAWA)

    assert second.id == first.id
    assert len(store.list(kind=DocumentKind.USTAWA)) == 1
    assert len(list(store.upload_dir.iterdir())) == 1
    assert len(store.chunks(second.id)) == second.chunk_count


def test_reupload_application_keeps_both_entries(store: SqlDocumentStore) -> None:
    blob = (DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").read_bytes()
    store.create(blob=blob, filename="wniosek.pdf", kind=DocumentKind.WNIOSEK)
    store.create(blob=blob, filename="wniosek.pdf", kind=DocumentKind.WNIOSEK)
    assert len(store.list()) == 2


def test_store_raises_not_found(store: SqlDocumentStore) -> None:
    missing = uuid4()
    with pytest.raises(NotFound):
        store.get(missing)
    with pytest.raises(NotFound):
        store.chunks(missing)
    with pytest.raises(NotFound):
        store.delete(missing)
    with pytest.raises(NotFound):
        store.reindex(missing)


def test_store_raises_conflict_without_source_file(store: SqlDocumentStore) -> None:
    document = store.create(
        blob=(DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").read_bytes(),
        filename="wniosek.pdf",
        kind=DocumentKind.WNIOSEK,
    )
    (store.upload_dir / f"{document.id}.pdf").unlink()
    with pytest.raises(Conflict):
        store.reindex(document.id)


def test_store_filters_by_kind_and_case(store: SqlDocumentStore) -> None:
    case_id = uuid4()
    store.create(
        blob=(DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").read_bytes(),
        filename="wniosek.pdf",
        kind=DocumentKind.WNIOSEK,
        case_id=case_id,
    )
    store.create(
        blob=(STATUTES / "kpa.txt").read_bytes(),
        filename="kpa.txt",
        kind=DocumentKind.USTAWA,
    )
    assert len(store.list()) == 2
    assert len(store.list(kind=DocumentKind.USTAWA)) == 1
    assert len(store.list(case_id=case_id)) == 1
    assert store.list(case_id=uuid4()) == []


def test_document_detail_has_utc_timestamp(store: SqlDocumentStore) -> None:
    document = store.create(
        blob=(DOCUMENTS / "wniosek-01-wynagrodzenia.pdf").read_bytes(),
        filename="wniosek.pdf",
        kind=DocumentKind.WNIOSEK,
    )
    assert document.created_at.tzinfo is not None
    assert document.status is DocumentStatus.INDEXED
    assert isinstance(document.id, UUID)


# ──────────────────────────────── kontener ─────────────────────────────────
def test_container_selects_real_adapter(
    monkeypatch: pytest.MonkeyPatch, engine: Engine, tmp_path: Path
) -> None:
    from app.core import db

    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setenv("MODULE_MODE_INGEST", "real")
    monkeypatch.setenv("MODULE_MODE_INGEST_PARSER", "real")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    container.reset()
    try:
        store = container.get_documents()
        parser = container.get_parser()
        assert isinstance(store, SqlDocumentStore)
        assert isinstance(parser, PdfDocxParser)
    finally:
        container.reset()
