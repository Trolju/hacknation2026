# Podłączenie dziennika audytu do operacji zapisu

Dokument dla agentów WS1 (`cases`), WS2 (`ingest`) i WS5 (`drafting`).
Moduł `audit` jest gotowy: adapter `SqlAuditLog`, endpoint `GET /api/audit`
i warstwa serwisowa `app/modules/audit/service.py`.

**Czego nie trzeba robić:** nic nie rejestrujemy centralnie. Router modułu
dostaje port przez `Depends` i woła `record(...)` po udanej operacji zapisu.

---

## 1. Wzorzec

```python
from app.modules.audit.service import AuditAction, AuditEntity, AuditRecorder, audit_recorder

@router.post("", response_model=Case, status_code=201)
def create_case(
    data: CaseCreate,
    repo: CaseRepositoryPort = Depends(container.get_cases),
    audit: AuditRecorder = Depends(audit_recorder),   # <-- dodane
) -> Case:
    case = CaseService(repo).create(data)
    audit.record(                                     # <-- dodane
        action=AuditAction.CASE_CREATED,
        entity_type=AuditEntity.CASE,
        entity_id=case.id,
        case_id=case.id,
        payload={"case_number": case.case_number, "subject": case.subject},
    )
    return case
```

Zasady:

- `record(...)` **nigdy nie rzuca wyjątku** — błąd zapisu do dziennika trafia
  do logu jako `audit_record_failed` i nie przewraca operacji biznesowej.
- Wołamy po udanej operacji, przed `return`. Jeśli serwis rzuci wyjątek,
  wpisu nie ma — i tak ma być.
- `payload` to mały słownik z faktami, nie kopia całego obiektu. Bez danych
  osobowych: identyfikatory, nazwy akcji, numery spraw, statusy.
- `actor` domyślnie `"urzędnik"`. Jeśli żądanie niesie aktora
  (`TransitionRequest.actor`), przekaż go jawnie.

---

## 2. Miejsca do podłączenia

### 2.1. `backend/app/modules/cases/router.py`

| Endpoint | `action` | `entity_type` | `case_id` | `payload` |
| --- | --- | --- | --- | --- |
| `POST /api/cases` | `case.created` | `case` | `case.id` | `case_number`, `subject`, `inflow_date` |
| `PATCH /api/cases/{case_id}` | `case.updated` | `case` | `case_id` | `changed_fields(patch)` |
| `POST /api/cases/{case_id}/transition` | `case.transitioned` | `case` | `case_id` | `from`, `to`, `note` |

```python
# PATCH — zapisujemy tylko pola faktycznie podane w żądaniu
from app.modules.audit.service import changed_fields

@router.patch("/{case_id}", response_model=Case)
def patch_case(
    case_id: UUID,
    patch: CasePatch,
    repo: CaseRepositoryPort = Depends(container.get_cases),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Case:
    case = CaseService(repo).update(case_id, patch)
    audit.record(
        action=AuditAction.CASE_UPDATED,
        entity_type=AuditEntity.CASE,
        entity_id=case_id,
        case_id=case_id,
        payload=changed_fields(patch),
    )
    return case
```

```python
# Przejście stanu — aktor i notatka pochodzą z żądania
@router.post("/{case_id}/transition", response_model=Case)
def transition_case(
    case_id: UUID,
    body: TransitionRequest,
    repo: CaseRepositoryPort = Depends(container.get_cases),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Case:
    before = CaseService(repo).get(case_id)
    case = CaseService(repo).transition(case_id, body)
    audit.record(
        action=AuditAction.CASE_TRANSITIONED,
        entity_type=AuditEntity.CASE,
        entity_id=case_id,
        case_id=case_id,
        actor=body.actor,
        payload={"from": str(before.status), "to": str(case.status), "note": body.note},
    )
    return case
```

### 2.2. `backend/app/modules/ingest/router.py`

| Endpoint | `action` | `entity_type` | `case_id` | `payload` |
| --- | --- | --- | --- | --- |
| `POST /api/documents` | `document.uploaded` | `document` | `case_id` z formularza | `filename`, `kind`, `size_bytes` |
| `DELETE /api/documents/{document_id}` | `document.deleted` | `document` | `document.case_id` | `filename`, `kind` |

```python
@router.post("", response_model=Document, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    kind: DocumentKind = Form(DocumentKind.INNE),
    case_id: UUID | None = Form(None),
    title: str | None = Form(None),
    store: DocumentStorePort = Depends(container.get_documents),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Document:
    blob = await file.read()
    if len(blob) > settings.max_upload_bytes:
        raise PayloadTooLarge(...)
    document = store.create(
        blob=blob, filename=file.filename or "plik", kind=kind, case_id=case_id, title=title
    )
    audit.record(
        action=AuditAction.DOCUMENT_UPLOADED,
        entity_type=AuditEntity.DOCUMENT,
        entity_id=document.id,
        case_id=case_id,
        payload={"filename": document.filename, "kind": str(document.kind),
                 "size_bytes": document.size_bytes},
    )
    return document
```

```python
@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    store: DocumentStorePort = Depends(container.get_documents),
    audit: AuditRecorder = Depends(audit_recorder),
) -> None:
    document = store.get(document_id)   # potrzebne, żeby znać case_id i nazwę pliku
    store.delete(document_id)
    audit.record(
        action=AuditAction.DOCUMENT_DELETED,
        entity_type=AuditEntity.DOCUMENT,
        entity_id=document_id,
        case_id=document.case_id,
        payload={"filename": document.filename, "kind": str(document.kind)},
    )
```

### 2.3. `backend/app/modules/drafting/router.py`

| Endpoint | `action` | `entity_type` | `case_id` | `payload` |
| --- | --- | --- | --- | --- |
| `POST /api/drafting/draft` | `draft.generated` | `draft` | `req.case_id` | `draft_id`, `citations_count`, `unsupported_count` |
| `PATCH /api/drafting/{draft_id}` | `draft.saved` | `draft` | `draft.case_id` | `title`, `body_length` |
| `GET /api/drafting/{draft_id}/export` | `draft.exported` | `draft` | `draft.case_id` | `format`, `anonymized` |

```python
@router.post("/draft", response_model=Draft)
def create_draft(
    req: DraftRequest,
    service: DraftingPort = Depends(container.get_drafting),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Draft:
    draft = service.draft(req)
    audit.record(
        action=AuditAction.DRAFT_GENERATED,
        entity_type=AuditEntity.DRAFT,
        entity_id=draft.id,
        case_id=draft.case_id,
        payload={"citations": len(draft.citations), "unsupported": len(draft.unsupported)},
    )
    return draft
```

```python
@router.get("/{draft_id}/export")
def export_draft(
    draft_id: UUID,
    fmt: str = Query("docx", pattern="^(docx|pdf|md)$"),
    anonymized: bool = False,
    service: DraftingPort = Depends(container.get_drafting),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Response:
    draft = service.get_by_id(draft_id)          # jeśli port nie ma takiej metody,
    blob, filename = service.export(draft_id, fmt=fmt, anonymized=anonymized)  # pomiń case_id
    audit.record(
        action=AuditAction.DRAFT_EXPORTED,
        entity_type=AuditEntity.DRAFT,
        entity_id=draft_id,
        case_id=draft.case_id,
        payload={"format": fmt, "anonymized": anonymized},
    )
    return Response(...)
```

---

## 3. Czego nie podłączać

- Odczyty (`GET`) — dziennik ma rejestrować mutacje, nie przeglądanie.
- `POST /api/documents/{id}/reindex` — operacja techniczna, nie zmienia treści
  sprawy. Jeśli ktoś chce ją widzieć w audycie, wystarczy
  `action="document.reindexed"` dopisane do `AuditAction`.
- Wnioski odrzucone walidacją — nie ma czego audytować, nic się nie zmieniło.

---

## 4. Weryfikacja

```bash
cd backend
MODULE_MODE_AUDIT=real .venv/bin/python -m pytest app/modules/audit -q
```

Po podłączeniu w module:

```bash
MODULE_MODE_AUDIT=real scripts/start-local.sh --backend-only
curl -s -X POST http://127.0.0.1:8000/api/cases -H 'Content-Type: application/json' \
  -d '{"case_number":"BKS.IV.1431.99.2026","subject":"Test","inflow_date":"2026-03-16"}'
curl -s http://127.0.0.1:8000/api/audit | python3 -m json.tool
```

Oczekiwany wynik: jeden wpis z `"action": "case.created"`.

---

## 5. Nazwy akcji

Stałe są w `AuditAction` (`app/modules/audit/service.py`). Nową akcję dodaje
się tam — nie wpisujemy stringów w routerach.

| Stała | Wartość |
| --- | --- |
| `CASE_CREATED` | `case.created` |
| `CASE_UPDATED` | `case.updated` |
| `CASE_TRANSITIONED` | `case.transitioned` |
| `DOCUMENT_UPLOADED` | `document.uploaded` |
| `DOCUMENT_DELETED` | `document.deleted` |
| `DRAFT_GENERATED` | `draft.generated` |
| `DRAFT_SAVED` | `draft.saved` |
| `DRAFT_EXPORTED` | `draft.exported` |
