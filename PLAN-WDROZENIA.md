# Plan wdrożenia — Inteligentny asystent urzędnika

**HackNation 2026 · Miasto Bydgoszcz**

Dokument opisuje architekturę, podział pracy i kolejność wdrożenia prototypu.
Zakres merytoryczny: [ZADANIE-KONKURSOWE.md](./ZADANIE-KONKURSOWE.md).
Poza zakresem tego planu: film (≤ 3 min) i prezentacja (≤ 10 slajdów) — zgodnie z ustaleniem.

---

## 1. Założenia

| Parametr | Przyjęta wartość | Uzasadnienie |
|---|---|---|
| Czas | ~36 h, plan na ~26 h ścieżki krytycznej | bufor na integrację i demo |
| Zespół | 5–6 agentów równolegle | plan zoptymalizowany pod równoległość |
| Forma | lokalna aplikacja webowa (Docker Compose) | najniższy próg wejścia dla urzędnika: przeglądarka, zero instalacji per-stanowisko |
| Język UI | polski | użytkownik to urzędnik UMB |
| Język kodu | angielski (identyfikatory), komentarze tylko gdzie konieczne | standard, czytelność dla agentów |
| Dane | wyłącznie fixtures, zero danych rzeczywistych | T6 |
| Tryb AI | dev: API (dozwolone), demo: model lokalny | T1, T6 |

**Świadome odejście od „jednej aplikacji desktopowej".** Tauri/Electron dałby ładniejszy instalator, ale wymaga buildu per-platforma i komplikuje pracę równoległą. Docker Compose + przeglądarka jest wdrażalne w 10 minut i testowalne przez jury bez instalacji.

---

## 2. Decyzje architektoniczne

### 2.1 Stack

| Warstwa | Wybór | Dlaczego |
|---|---|---|
| Backend | Python 3.12 + FastAPI + Pydantic v2 | najlepszy ekosystem do PDF/DOCX, NER i modeli lokalnych |
| ORM / DB | SQLAlchemy 2.0 + SQLite | zero konfiguracji, jeden plik, łatwy backup |
| Wektory | `sqlite-vec` (fallback: numpy brute-force) | brak osobnego serwisu, skaluje do setek dokumentów |
| LLM lokalny | llama-cpp-python (GGUF) lub Ollama | abstrakcja pozwala wybrać na demo |
| LLM dev | dowolny OpenAI-compatible | dozwolone w trakcie hackathonu |
| NER | spaCy `pl_core_news_lg` | gotowy polski model, offline |
| Embeddings | `BGE-m3` lub `paraphrase-multilingual-mpnet-base-v2` | wielojęzyczne, dobre na tekstach prawnych |
| Frontend | React 18 + TypeScript + Vite | standard, szybki HMR, dobre wsparcie agentów |
| Styl | Tailwind CSS + **shadcn/ui** (Radix) | sprawdzone, dostępne, komponenty kopiowane do repo — brak lock-inu wersji |
| Tabele | **TanStack Table v8** | headless, pełna kontrola nad komórkami kalendarza |
| Stan serwera | **TanStack Query v5** | cache, optimistic updates, retry |
| Formularze | **React Hook Form + Zod** | walidacja współdzielona z kontraktem |
| Edytor | **TipTap** (ProseMirror) | custom marks = podświetlanie anonimizacji |
| Daty | **date-fns** z locale `pl` | liczenie terminów, formatowanie |
| Wykresy | **Recharts** | mały dashboard terminów |
| Toasty | **sonner** | |
| Ikony | **lucide-react** | |
| Command palette | **cmdk** | skrót Cmd+K dla wprawnych urzędników |
| Testy | pytest + httpx, Vitest, Playwright | |

**Dlaczego shadcn/ui, a nie MUI/AntD.** Komponenty są kopiowane do `components/ui/`, więc agent pracujący nad modułem nie może zepsuć globalnego motywu ani wersji biblioteki. To bezpośrednio przekłada się na niezależność pracy. Radix pod spodem daje dostępność (WCAG) bez własnej implementacji.

### 2.2 Wzorzec: ports-and-adapters

Rdzeń niezależności agentów. Każdy moduł to **port** (protokół) + dwa adaptery: `fake` (fixtures, deterministyczny) i `real` (implementacja).

```python
# backend/app/ports/archive.py
class ArchiveSearchPort(Protocol):
    def similar(self, text: str, *, k: int = 5, year_from: int | None = None) -> list[SimilarCase]: ...
```

```python
# backend/app/core/container.py  (własność WS0)
def get_archive_search() -> ArchiveSearchPort:
    if settings.module_mode("archive") == "fake":
        return FakeArchiveSearch()
    return SqliteArchiveSearch()
```

Przełączanie: `MODULE_MODE_ARCHIVE=fake|real`. Dzięki temu agent WS5 (generator) buduje cały przepływ, zanim WS3 (archiwum) istnieje — i odwrotnie.

### 2.3 Auto-discovery zamiast rejestrów

Jedyny realny powód konfliktów w pracy równoległej to wspólne pliki rejestrujące. Rozwiązanie: **nikt nie edytuje rejestru**.

Backend — `main.py` (WS0, zamrożony) skanuje katalog:

```python
for path in sorted(Path(__file__).parent.joinpath("modules").glob("*/router.py")):
    module = importlib.import_module(f"app.modules.{path.parent.name}.router")
    app.include_router(module.router)
```

Frontend — Vite `import.meta.glob`:

```ts
// features/registry.ts  (WS0, zamrożony)
const manifests = import.meta.glob('./*/manifest.ts', { eager: true })
export const features = Object.values(manifests).map(m => m.default)
```

Agent dodaje `features/calendar/manifest.ts` i nic więcej nie musi rejestrować. Zero merge'y w plikach współdzielonych.

### 2.4 Kontrakt jako jedyne źródło prawdy

`contracts/openapi.yaml` jest generowane raz w Fali 0 i **zamrożone**. Z niego powstaje:
- klient TypeScript (`openapi-typescript`) → `frontend/src/lib/api/schema.d.ts`
- walidacja odpowiedzi w testach kontraktowych
- mock server dla frontendu (`prism` lub `msw`)

Zmiana kontraktu = osobny PR z wpisem w `contracts/CHANGELOG.md`. Agent, który potrzebuje zmiany, **zgłasza ją, nie edytuje pliku**.

---

## 3. Struktura repozytorium

```
/
├── contracts/                      # WS0 — ZAMROŻONE po Fali 0
│   ├── openapi.yaml
│   ├── domain.md                   # maszyna stanów, polityka terminów, słownik pól
│   ├── CHANGELOG.md
│   └── schemas/*.json
├── fixtures/                       # WS0 — ZAMROŻONE, read-only dla wszystkich
│   ├── cases/*.json                # 10 wniosków testowych
│   ├── archive/*.json              # ~60 archiwalnych odpowiedzi
│   ├── statutes/*.txt              # KPA, UDIP, wyciągi
│   ├── documents/*.pdf|docx        # 6 plików do testów wgrywania
│   └── anonymization/labeled.jsonl # zbiór z etykietami (golden test)
├── backend/
│   ├── app/
│   │   ├── main.py                 # WS0 — auto-discovery
│   │   ├── core/                   # WS0 — settings, db, logging, errors, container
│   │   ├── ports/                  # WS0 — wszystkie protokoły
│   │   ├── adapters/fakes/         # WS0 — deterministyczne atrapy
│   │   └── modules/
│   │       ├── cases/              # WS1
│   │       ├── ingest/             # WS2
│   │       ├── archive/            # WS3
│   │       ├── routing/            # WS4
│   │       ├── drafting/           # WS5
│   │       ├── anonymize/          # WS6
│   │       ├── inference/          # WS7
│   │       └── audit/              # WS8
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/                    # WS0 — shell, layout, router
│       ├── components/ui/          # WS0 — shadcn primitives
│       ├── lib/                    # WS0 — api client, query client, utils
│       └── features/
│           ├── calendar/           # WS1
│           ├── ingest/             # WS2
│           ├── archive/            # WS3
│           ├── routing/            # WS4
│           ├── drafting/           # WS5
│           ├── anonymize/          # WS6
│           └── settings/           # WS7
├── deploy/                         # WS8
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AGENTS.md                   # zasady pracy równoległej
│   └── INSTALL.md                  # po polsku, dla IT miasta
└── Makefile
```

**Reguła:** jeden agent = jeden katalog `modules/<x>/` + `features/<x>/`. Wyjątki wymagają zgłoszenia.

---

## 4. Workstreamy

### WS0 — Fundament (blokujący, 1 agent, ~3 h)

Wszystko, co musi istnieć, zanim ruszy równoległość.

- Monorepo, `pyproject.toml` (uv), `package.json` (pnpm), `Makefile`, pre-commit
- CI: lint + typecheck + test
- `contracts/openapi.yaml` — **pełna powierzchnia API**, wszystkie endpointy jako stuby
- `contracts/domain.md` — maszyna stanów a–e, polityka terminów, słownik pól (W3)
- `fixtures/` — 10 wniosków, 60 odpowiedzi archiwalnych, ustawy, 6 dokumentów, zbiór etykietowany
- `core/` — settings, SQLite, logging strukturalny, envelope błędów, kontener DI
- `ports/` — wszystkie protokoły
- `adapters/fakes/` — deterministyczne atrapy (ten sam input → ten sam output)
- `main.py` — auto-discovery routerów
- Frontend: shell, layout, sidebar, router z **wszystkimi trasami → stubowe strony**
- `components/ui/` — shadcn zainstalowany (button, table, dialog, drawer, tabs, badge, input, select, toast, tooltip, command)
- `lib/` — wygenerowany klient API, query client, formatery dat
- `features/*/manifest.ts` — stuby, żeby build był zielony od pierwszej minuty
- `docs/AGENTS.md`

**DoD:** `make dev` uruchamia oba serwisy; aplikacja ładuje się ze stubami; `make check` zielony; OpenAPI waliduje się; każda atrapa zwraca fixtures.

> To jedyny etap sekwencyjny. Reszta idzie równolegle.

---

### WS1 — Kalendarz wniosków (W1, W2, W3, W12)

**Backend** `modules/cases/`: repozytorium, serwis, router, maszyna stanów, kalkulator terminów.
**Frontend** `features/calendar/`: TanStack Table, filtry, kolorowanie wierszy, edytor statusu, szkielet szuflady sprawy.

- Sortowanie rosnące po terminie (W1 — uwaga: źródło mówi „od najstarszych", co jest odwrotnością intuicji UX; sortujemy po terminie, nie po dacie wpływu)
- Kolumna „dni do terminu" z licznikiem
- Wyróżnienia: przekroczony (czerwony), dziś (bursztynowy), jutro (żółty), zamknięty (szary)
- Filtr roku, filtra statusu, wyszukiwanie po numerze i temacie
- Przejścia statusu a→e z zapisem do audytu
- Nawigacja klawiaturą, pusty stan, skeleton loading

**DoD:** 10 fixtures renderuje się poprawnie; każdy wiersz ma policzone dni; przejście statusu jest nieodwracalne tylko przez jawne cofnięcie; tabela działa przy 500 wierszach (wirtualizacja).

---

### WS2 — Wgrywanie i przetwarzanie dokumentów (W5, W8)

**Backend** `modules/ingest/`: upload, parsowanie PDF (`pdfplumber`) i DOCX (`python-docx`), normalizacja tekstu, chunking, embedding, indeks wektorowy, CRUD bazy wiedzy.
**Frontend** `features/ingest/`: dropzone, postęp, lista dokumentów, podgląd, podgląd chunków.

- Zachowanie offsetów (strona / sekcja) przy ekstrakcji — krytyczne dla cytowań w WS5
- Reindeksacja przy aktualizacji ustawy
- Walidacja MIME przez sniffing, nie przez rozszerzenie
- Limit 10 MB, czytelne błędy po polsku

**DoD:** PDF i DOCX parsują się z offsetami; chunki trafiają do indeksu; ponowny upload tej samej ustawy nadpisuje, nie duplikuje; błąd parsowania pokazuje się użytkownikowi, nie w logach.

---

### WS3 — Wyszukiwanie archiwalne (W9)

**Backend** `modules/archive/`: wyszukiwanie hybrydowe (BM25 + wektory), rerank, wyjaśnienie podobieństwa, filtr roku.
**Frontend** `features/archive/`: panel podobnych spraw z oceną i snippetem, „otwórz sprawę".

**DoD:** top-5 dla każdego fixture jest merytorycznie sensowne; latencja < 500 ms przy 500 dokumentach; ocena podobieństwa widoczna; pusty stan z podpowiedzią.

---

### WS4 — Routing wydziałowy (W10)

**Backend** `modules/routing/`: taksonomia wydziałów (zaseedowana z BIP), klasyfikator keyword + embedding, tie-break przez LLM, confidence.
**Frontend** `features/routing/`: lista sugestii z paskami pewności, ręczne nadpisanie, „generuj zapytanie do wydziału" (tylko projekt pisma — O1: nic nie wysyłamy).

**DoD:** taksonomia pokrywa wszystkie wydziały UMB; top-3 z pewnością; nadpisanie trwałe; wygenerowane zapytanie pobieralne jako DOCX.

---

### WS5 — Generator odpowiedzi (W4, W11)

**Backend** `modules/drafting/`: składanie promptu, retrieval, generacja, mapowanie cytowań, flagowanie twierdzeń bez źródła, eksport DOCX/TXT.
**Frontend** `features/drafting/`: edytor TipTap, panel źródeł, cytowania na hover, akceptacja/odrzucenie, eksport.

- Każde twierdzenie faktyczne musi wskazywać chunk źródłowy
- Zdania bez pokrycia → oznaczone, nie usunięte (W4: „wykluczyć błędy i halucynacje")
- Eksport DOCX z szablonem pisma urzędowego

**DoD:** projekt powstaje z wniosku + odpowiedzi wydziałów + archiwum + ustaw; każde zdanie ma referencję albo flagę; eksport DOCX otwiera się w Wordzie z zachowanym formatowaniem.

---

### WS6 — Anonimizacja (W6, W7)

**Backend** `modules/anonymize/`: detektory regex (PESEL, NIP, REGON, dowód, paszport, telefon, e-mail, IBAN, adres), NER spaCy, przebieg kontekstowy LLM, scalanie spanów, apply/redact.
**Frontend** `features/anonymize/`: marki TipTap (szary = sugestia, czarny = zaakceptowane), klik-przełącznik, legenda kategorii, „akceptuj wszystko", „anonimizuj automatycznie", podgląd zredagowany.

- Model spanu: `{start, end, text, category, confidence, source}`
- Priorytet: regex > NER > LLM (regex ma najwyższą precyzję na numerach)
- Zero fałszywych trafień na numerach spraw — to najczęstszy błąd

**DoD:** na zbiorze etykietowanym recall ≥ 95% dla PESEL/NIP/telefon/e-mail, ≥ 85% dla nazwisk; zero FP na numerach wniosków; przełączanie spanu działa; eksport zredagowany.

> To moduł, który jury testuje w punkcie 3. Warto go dowieźć wcześnie i dobrze.

---

### WS7 — Warstwa inference (T1, T6)

**Backend** `modules/inference/`: adaptery `LLMPort` i `EmbeddingPort` (OpenAI-compatible, llama.cpp, Ollama, fake), rejestr modeli, health check, timeout/retry, licznik tokenów, **egress guard**.
**Frontend** `features/settings/`: wybór modelu, test połączenia, wskaźnik trybu (dev / lokalny).

- `OFFLINE=1` blokuje jakiekolwiek wyjście do sieci — weryfikowalne testem
- Degradacja do `fake` przy braku modelu, z komunikatem, nie wyjątkiem
- Rekomendacja modelu do środowiska zamkniętego: **Bielik-11B-v2.3-Instruct Q4_K_M** (polski, trenowany na tekstach urzędowych); alternatywa lżejsza: Qwen2.5-7B-Instruct

**DoD:** przełączenie providera env-em; `/health` raportuje stan; `OFFLINE=1` nie wykonuje żadnego żądania zewnętrznego (test); rekomendacja modelu w `docs/`.

---

### WS8 — Bezpieczeństwo i wdrożenie (T2, T3)

**Backend** `modules/audit/`: log audytowy każdej mutacji, logowanie bez PII, walidacja plików.
**Deploy**: Dockerfile multi-stage, `docker-compose.yml`, nginx, `start.sh`, seed, backup/restore, healthchecki.
**Docs**: `INSTALL.md` po polsku dla IT miasta, `OPERATIONS.md`.

**DoD:** `docker compose up` na czystej maszynie → działająca aplikacja na `localhost`; seed ładuje fixtures; audyt zapisuje każdą zmianę; brak sekretów w obrazie; obraz < 1,5 GB.

---

### WS9 — UX, dostępność, integracja (2 agentów, Fala 3)

- Onboarding przy pierwszym uruchomieniu, tryb demo, podpowiedzi „co dalej?"
- Audyt WCAG 2.1 AA: focus, aria, kontrast, obsługa klawiaturą
- Przegląd polskich tekstów (urzedniczy, ale zrozumiały)
- E2E Playwright: jedna ścieżka szczęśliwa od uploadu do eksportu
- Skrypt demo (patrz §8)

---

## 5. Graf zależności i fale

```
FALA 0  (1 agent, ~3 h)
  WS0 ──────────────────────────────────────────────┐
                                                     │
FALA 1  (5 agentów równolegle, ~8 h)                 │
  WS1 kalendarz ─────────────────────────────────┐   │
  WS2 ingest ──────────────┐                     │   │
  WS6 anonimizacja ────────┤                     │   │
  WS7 inference ───────────┤                     │   │
  WS8 deploy ──────────────┤                     │   │
                           │                     │   │
FALA 2  (4 agentów, ~8 h)  │                     │   │
  WS3 archiwum ◄───────────┘                     │   │
  WS4 routing ◄────────────┘                     │   │
  WS5 generator ◄──────────┴─────────────────────┘   │
  WS9a UX ◄──────────────────────────────────────────┘
                                                     │
FALA 3  (2 agentów, ~6 h)                            │
  WS9b integracja + E2E + demo ◄─────────────────────┘
```

**Ścieżka krytyczna:** WS0 → WS7 → WS2 → WS3 → WS5 → WS9b ≈ 26 h.

**Dlaczego WS5 może startować w Fali 2, a nie 3:** dzięki portom z atrapami. Agent WS5 dostaje `FakeArchiveSearch` i `FakeDepartmentRouter` zwracające fixtures, więc buduje cały przepływ generowania, zanim WS3 i WS4 dowiozą implementacje. Podmiana to jedna zmienna env.

---

## 6. Zasady pracy równoległej

Do `docs/AGENTS.md`, wiążące dla każdego agenta:

1. **Kontrakty są zamrożone.** `contracts/` i `fixtures/` są read-only. Potrzebujesz zmiany — zgłoś, nie edytuj.
2. **Jeden agent = jeden katalog.** `backend/app/modules/<x>/` + `frontend/src/features/<x>/`. Nic poza tym.
3. **Zero plików rejestrujących.** Auto-discovery. Jeśli musisz coś zarejestrować, to znaczy, że robisz to źle.
4. **Atrapa najpierw.** Każdy moduł ma adapter `fake` zanim powstanie `real`. Testy używają `fake`.
5. **Nie dotykaj `core/`, `components/ui/`, `lib/`.** To własność WS0. Potrzebujesz zmiany — zgłoś.
6. **Testy w katalogu modułu.** `modules/<x>/tests/`, `features/<x>/*.test.tsx`. Nie dopisuj do globalnego suite'a.
7. **Każdy commit zielony na `make check`.** Lint + typecheck + testy modułu.
8. **Deterministyczne fixtures.** Ten sam input → ten sam output. Żadnych `random`, żadnych dat bieżących w fixtures.
9. **Nazewnictwo:** `snake_case` w Pythonie, `camelCase` w TS, teksty UI po polsku w `i18n/pl.ts` modułu.
10. **Nie refaktoryzuj cudzych modułów.** Zauważyłeś problem — zgłoś, nie poprawiaj.

**Protokół zmiany kontraktu:** PR tytułowany `contract: <opis>`, zmiana w `openapi.yaml` + wpis w `CHANGELOG.md` + regeneracja klienta. Merguje WS0. Blokuje wszystkich na czas regeneracji — dlatego wszystkie pola potrzebne modułom muszą być przewidziane w Fali 0.

---

## 7. Pokrycie wymagań

| Wymaganie | Workstream |
|---|---|
| W1 tabela + kalendarz | WS1 |
| W2 wyróżnianie terminów | WS1 |
| W3 pola rekordu | WS0 (słownik) + WS1 |
| W4 projekt odpowiedzi | WS5 |
| W5 wgrywanie plików | WS2 |
| W6 sugerowanie anonimizacji | WS6 |
| W7 automatyczna anonimizacja | WS6 |
| W8 uczenie na danych | WS2 + WS7 |
| W9 przeszukiwanie archiwum | WS3 |
| W10 wskazywanie ścieżki | WS4 |
| W11 automatyzacja | WS5 + WS1 |
| W12 statusy a–e | WS1 |
| T1 model lokalny | WS7 |
| T2 bezpieczeństwo, wdrażalność | WS8 |
| T3 skalowalność | WS2 + WS3 |
| T4 użyteczność | WS9 |
| T5 stabilność | wszystkie (DoD) |
| T6 dane testowe | WS0 (fixtures) |
| O1 brak wysyłki | WS4 (tylko projekt pisma) |
| O2 brak integracji | architektura (brak konektorów) |
| O3 decyzja u urzędnika | WS5 (akceptacja) + WS6 (akceptacja) |
| O4 dowolna technologia | — |

---

## 8. Skrypt demo (5 minut, mapowany na testy jury)

| Czas | Scenariusz | Test jury |
|---|---|---|
| 0:00 | Kalendarz: 10 wniosków, czerwony wiersz po terminie, bursztynowy na dziś | 5 |
| 0:40 | Wgranie `fixtures/documents/wniosek-01.pdf` → ekstrakcja, sprawa utworzona | 1 |
| 1:20 | Panel „Archiwum": 5 podobnych spraw z oceną podobieństwa | 1 |
| 1:50 | Panel „Wydziały": 3 sugestie z pewnością, generacja zapytania | — |
| 2:20 | Wgranie odpowiedzi z wydziału → projekt pisma z cytowaniami | 2 |
| 3:20 | Anonimizacja: szare spany, akceptacja, czarne, eksport zredagowany | 3 |
| 4:20 | Eksport DOCX, otwarcie w Wordzie | 4 |
| 4:40 | Ustawienia: przełączenie na model lokalny, `OFFLINE=1`, test połączenia | 4, 6 |

Demo musi działać **bez sieci** od początku do końca. To jednocześnie test T1.

---

## 9. Strategia testów

| Poziom | Narzędzie | Zakres |
|---|---|---|
| Jednostkowe | pytest / Vitest | logika modułu, w izolacji, na atrapach |
| Kontraktowe | schemat OpenAPI | każdy endpoint zwraca zgodny kształt |
| Golden — anonimizacja | `fixtures/anonymization/labeled.jsonl` | precision/recall per kategoria |
| Golden — generowanie | `FakeLLM` + snapshot | stabilność promptu i struktury wyjścia |
| E2E | Playwright | jedna ścieżka: upload → archiwum → draft → anonimizacja → eksport |
| Bezpieczeństwo | pytest | `OFFLINE=1` nie wychodzi do sieci; brak PII w logach |

**Bramka jakości:** `make check` = lint + typecheck + testy jednostkowe + kontraktowe. Musi być zielone przed każdym mergem.

---

## 10. Ryzyka

| Ryzyko | Wpływ | Mitygacja |
|---|---|---|
| Model lokalny za wolny na demo | wysokie | profil „demo" z krótkim promptem; streaming; cache odpowiedzi; fallback na mniejszy model |
| Anonimizacja gubi dane → jury test 3 nie przechodzi | wysokie | regex przed NER; zbiór etykietowany od Fali 0; próg recall w DoD |
| Agenci rozjeżdżają się na kontrakcie | wysokie | pełne OpenAPI w Fali 0; protokół zmian; mock server |
| PDF-y urzędowe nie parsują się (skany) | średnie | fixtures zawierają jeden skan → wymuszony fallback OCR (Tesseract) albo jawny komunikat |
| Merge conficty w plikach współdzielonych | średnie | auto-discovery; zakaz edycji `core/`, `lib/`, `components/ui/` |
| Brak czasu na integrację | średnie | Fala 3 zarezerwowana; E2E od Fali 2 |
| Docker image za duży | niskie | multi-stage, model pobierany przy starcie, nie w obrazie |

---

## 11. Definition of Done całości

Prototyp jest gotowy, gdy:

1. `docker compose up` na czystej maszynie daje działającą aplikację pod `localhost`.
2. Wszystkie 12 wymagań W1–W12 są pokryte i przechodzą testy.
3. Aplikacja działa z `OFFLINE=1` — bez żadnego wyjścia do sieci.
4. Ścieżka demo (§8) przechodzi bez błędów w czasie < 5 minut.
5. `make check` zielony; E2E zielony.
6. Anonimizacja osiąga progi z WS6 na zbiorze etykietowanym.
7. `docs/INSTALL.md` pozwala osobie nietechnicznej uruchomić aplikację.
8. Audyt zapisuje każdą mutację; logi nie zawierają PII.

---

## 12. Poza zakresem

- Film ≤ 3 min i prezentacja ≤ 10 slajdów — zgodnie z ustaleniem, do osobnego etapu.
- Integracja z SIDAS i innymi systemami urzędowymi — O2.
- Wysyłka pism — O1.
- Uwierzytelnianie wieloużytkownikowe — prototyp jest jednoosobowy; audyt po `actor` z konfiguracji.
