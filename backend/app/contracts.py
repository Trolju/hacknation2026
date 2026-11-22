"""DTO — lustro `contracts/openapi.yaml`.

**ZAMROŻONE po Fali 0.** Zmiana wymaga PR-a `contract: <opis>`.

Konwencja: pola w `snake_case` (bez transformacji po stronie frontendu),
daty jako `date`, znaczniki czasu jako `datetime` UTC.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─────────────────────────────── system ────────────────────────────────
class Error(Base):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class Health(Base):
    status: Literal["ok", "degraded"]
    version: str
    modules: dict[str, Literal["fake", "real", "error"]]


class AppMeta(Base):
    name: str
    version: str
    offline: bool
    module_modes: dict[str, Literal["fake", "real"]]


# ──────────────────────────────── cases ────────────────────────────────
class CaseStatus(StrEnum):
    """Maszyna stanów a–e (W12)."""

    NOWY = "nowy"  # a
    ZAPYTANIA_WYSLANE = "zapytania_wyslane"  # b
    KWERENDA = "kwerenda"  # c
    PRZYGOTOWANA_ODPOWIEDZ = "przygotowana_odpowiedz"  # d
    ODPOWIEDZ_WYSLANA = "odpowiedz_wyslana"  # e


STATUS_ORDER: tuple[CaseStatus, ...] = (
    CaseStatus.NOWY,
    CaseStatus.ZAPYTANIA_WYSLANE,
    CaseStatus.KWERENDA,
    CaseStatus.PRZYGOTOWANA_ODPOWIEDZ,
    CaseStatus.ODPOWIEDZ_WYSLANA,
)

STATUS_CODE: dict[CaseStatus, str] = {
    CaseStatus.NOWY: "a",
    CaseStatus.ZAPYTANIA_WYSLANE: "b",
    CaseStatus.KWERENDA: "c",
    CaseStatus.PRZYGOTOWANA_ODPOWIEDZ: "d",
    CaseStatus.ODPOWIEDZ_WYSLANA: "e",
}


class Urgency(StrEnum):
    OVERDUE = "overdue"
    TODAY = "today"
    TOMORROW = "tomorrow"
    SOON = "soon"
    NORMAL = "normal"
    CLOSED = "closed"


class ApplicantType(StrEnum):
    OSOBA_FIZYCZNA = "osoba_fizyczna"
    ORGANIZACJA = "organizacja"
    MEDIA = "media"
    INNE = "inne"


#: Górna granica przedłużenia terminu w kwerendzie. Ustawa o dostępie do
#: informacji publicznej nie przewiduje kwerendy, ale praktyka urzędowa
#: dopuszcza przedłużenie o czas potrzebny na ustalenie danych — przyjmujemy
#: 60 dni jako bezpieczny sufit, żeby literówka nie przesunęła terminu o lata.
MAX_KWERENDA_DAYS = 60


class Case(Base):
    id: UUID
    case_number: str
    ordinal: int
    subject: str
    #: Wnioskodawca w postaci z pisma — nazwisko, nazwa organizacji albo e-mail.
    #: Puste, gdy pismo nie pozwala go ustalić.
    applicant: str = ""
    inflow_date: date
    deadline: date
    response_date: date | None = None
    handler_initials: str = ""
    status: CaseStatus
    year: int
    days_remaining: int
    urgency: Urgency
    applicant_type: ApplicantType = ApplicantType.INNE
    source_document_id: UUID | None = None
    #: O ile dni przedłużono termin w kwerendzie (W12: „kwerenda + liczba dni”).
    #: `None` znaczy, że sprawa nigdy nie była w kwerendzie.
    kwerenda_days: int | None = None
    created_at: datetime
    updated_at: datetime


class CaseDetail(Case):
    notes: str | None = None
    department_ids: list[str] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)


class CaseCreate(Base):
    case_number: str
    subject: str
    applicant: str = ""
    inflow_date: date
    deadline: date | None = None
    handler_initials: str = ""
    applicant_type: ApplicantType = ApplicantType.INNE
    source_document_id: UUID | None = None


class CasePatch(Base):
    subject: str | None = None
    applicant: str | None = None
    deadline: date | None = None
    response_date: date | None = None
    handler_initials: str | None = None
    applicant_type: ApplicantType | None = None
    notes: str | None = None
    department_ids: list[str] | None = None


class TransitionRequest(Base):
    to: CaseStatus
    actor: str = "urzędnik"
    note: str | None = None
    #: Liczba dni przedłużenia terminu — sensowna tylko przy przejściu do
    #: `kwerenda`. Termin odpowiedzi przesuwa się o tę wartość.
    kwerenda_days: int | None = Field(default=None, ge=1, le=MAX_KWERENDA_DAYS)


class HistoryEntry(Base):
    id: UUID
    case_id: UUID
    at: datetime
    actor: str
    action: str
    from_value: str | None = None
    to_value: str | None = None
    note: str | None = None


# ────────────────────────────── documents ──────────────────────────────
class DocumentKind(StrEnum):
    WNIOSEK = "wniosek"
    ODPOWIEDZ_WYDZIALU = "odpowiedz_wydzialu"
    ARCHIWUM = "archiwum"
    USTAWA = "ustawa"
    ZARZADZENIE = "zarzadzenie"
    INNE = "inne"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PARSED = "parsed"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(Base):
    id: UUID
    kind: DocumentKind
    filename: str
    title: str | None = None
    mime: str
    size_bytes: int
    status: DocumentStatus
    error: str | None = None
    case_id: UUID | None = None
    chunk_count: int = 0
    created_at: datetime


class DocumentDetail(Document):
    text: str = ""
    page_count: int = 0


class Chunk(Base):
    id: str
    document_id: UUID
    index: int
    text: str
    page: int | None = None
    section: str | None = None


# ─────────────────────────────── archive ───────────────────────────────
class SimilarRequest(Base):
    text: str
    k: int = Field(default=5, ge=1, le=20)
    year_from: int | None = None
    exclude_case_id: UUID | None = None


class SimilarCase(Base):
    archive_id: str
    case_number: str
    subject: str
    year: int | None = None
    score: float = Field(ge=0.0, le=1.0)
    snippet: str = ""
    matched_terms: list[str] = Field(default_factory=list)
    response_excerpt: str = ""


class ArchiveCase(Base):
    archive_id: str
    case_number: str
    subject: str
    year: int
    request_text: str
    response_text: str
    departments: list[str] = Field(default_factory=list)


# ─────────────────────────────── routing ───────────────────────────────
class DepartmentKind(StrEnum):
    WYDZIAL = "wydzial"
    BIURO = "biuro"
    REFERAT = "referat"


class Department(Base):
    id: str
    name: str
    kind: DepartmentKind
    keywords: list[str] = Field(default_factory=list)
    url: str | None = None


class SuggestRequest(Base):
    text: str
    k: int = Field(default=3, ge=1, le=10)


class DepartmentSuggestion(Base):
    department_id: str
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    matched_terms: list[str] = Field(default_factory=list)


class InquiryRequest(Base):
    case_id: UUID
    department_ids: list[str]


class GeneratedLetter(Base):
    title: str
    body: str
    addressees: list[str] = Field(default_factory=list)


# ────────────────────────────── drafting ───────────────────────────────
class DraftRequest(Base):
    case_id: UUID
    department_reply_ids: list[UUID] = Field(default_factory=list)
    use_archive: bool = True
    use_statutes: bool = True
    tone: Literal["formalny", "uprzejmy"] = "formalny"


class Citation(Base):
    ref: int
    source_type: Literal["document", "archive", "statute", "department_reply"]
    source_id: str
    label: str
    excerpt: str = ""


class Draft(Base):
    id: UUID
    case_id: UUID
    title: str
    body: str
    citations: list[Citation] = Field(default_factory=list)
    unsupported: list[str] = Field(default_factory=list)
    #: Projekt powstał z szablonu, bo model nie dostarczył użytecznej treści.
    #: Osobne pole, bo to komunikat systemowy, a nie twierdzenie merytoryczne —
    #: w `unsupported` urzędnik dostawał polecenie uzupełnienia czegoś, czego
    #: uzupełnić nie może.
    degraded: bool = False
    degraded_reason: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DraftPatch(Base):
    body: str
    title: str | None = None


# ────────────────────────────── anonymize ──────────────────────────────
class SpanCategory(StrEnum):
    """Kategorie danych podlegających anonimizacji.

    Lista odwzorowuje „Dane podlegające anonimizacji” Urzędu Miasta Bydgoszczy.
    Pierwsza grupa to identyfikatory rozpoznawalne regułowo, druga — dane
    semantyczne, które oznacza dopiero model językowy lub urzędnik ręcznie.
    """

    # identyfikatory — reguły wystarczają
    PESEL = "pesel"
    NIP = "nip"
    REGON = "regon"
    DOWOD = "dowod"
    PASZPORT = "paszport"
    TELEFON = "telefon"
    EMAIL = "email"
    IBAN = "iban"
    ADRES = "adres"
    IMIE_NAZWISKO = "imie_nazwisko"
    DATA_URODZENIA = "data_urodzenia"
    MIEJSCE_URODZENIA = "miejsce_urodzenia"
    PODPIS = "podpis"
    KSIEGA_WIECZYSTA = "ksiega_wieczysta"
    DZIALKA = "dzialka"
    REJESTRACJA = "rejestracja"
    # dane semantyczne — wymagają modelu albo decyzji urzędnika
    WIZERUNEK = "wizerunek"
    STAN_CYWILNY = "stan_cywilny"
    ZDROWIE = "zdrowie"
    MAJATEK = "majatek"
    POMOC_SPOLECZNA = "pomoc_spoleczna"
    POGLADY = "poglady"
    PRZYNALEZNOSC = "przynaleznosc"
    POCHODZENIE = "pochodzenie"
    ORIENTACJA = "orientacja"
    KARALNOSC = "karalnosc"
    INNE = "inne"


class ExclusionGround(StrEnum):
    """Przesłanki wyłączenia jawności — nie anonimizacja, lecz podstawa odmowy.

    Zarządzenie Prezydenta Miasta Bydgoszczy Nr 536/2024 §11 ust. 9 nakazuje
    w takich sprawach przygotować projekt decyzji administracyjnej o odmowie
    udostępnienia informacji publicznej.
    """

    TAJEMNICA_PRZEDSIEBIORSTWA = "tajemnica_przedsiebiorstwa"
    TAJEMNICA_SKARBOWA = "tajemnica_skarbowa"
    TAJEMNICA_BANKOWA = "tajemnica_bankowa"
    TAJEMNICA_ZAWODOWA = "tajemnica_zawodowa"
    INFORMACJE_NIEJAWNE = "informacje_niejawne"
    OCHRONA_DANYCH_OSOBOWYCH = "ochrona_danych_osobowych"
    INFORMACJA_PRZETWORZONA = "informacja_przetworzona"


class Span(Base):
    start: int
    end: int
    text: str
    category: SpanCategory
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["regex", "ner", "llm"]


class DetectRequest(Base):
    text: str
    categories: list[SpanCategory] | None = None


class ApplyRequest(Base):
    text: str
    spans: list[Span]
    placeholder: str = "[USUNIĘTO]"


class ApplyResult(Base):
    text: str
    removed_count: int


class CategoryMetrics(Base):
    precision: float
    recall: float
    support: int


class AnonymizerMetrics(Base):
    precision: float
    recall: float
    f1: float
    per_category: dict[str, CategoryMetrics] = Field(default_factory=dict)


# ────────────────────────────── inference ──────────────────────────────
class InferenceHealth(Base):
    provider: Literal["fake", "openai", "mistral", "llamacpp", "ollama"]
    model: str
    status: Literal["ok", "degraded", "down"]
    offline: bool
    latency_ms: float | None = None
    message: str | None = None


class ModelInfo(Base):
    id: str
    label: str
    provider: str
    local: bool
    size_gb: float | None = None
    recommended: bool = False


class InferenceTestResult(Base):
    ok: bool
    latency_ms: float
    output: str
    error: str | None = None


# ──────────────────────────────── audit ────────────────────────────────
class AuditEntry(Base):
    id: UUID
    at: datetime
    actor: str
    action: str
    entity_type: str
    entity_id: str
    case_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
