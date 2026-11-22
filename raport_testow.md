# Raport z testów — tryb realny (8/8 modułów) z modelem Mistral

Data: 22 listopada 2026
Środowisko: lokalne, backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:5173`
Zakres: wszystkie osiem modułów na adapterach `real`, generator odpowiedzi na żywym
Mistralu (`mistral-small-latest`). Nie atrapy.

---

## 1. Konfiguracja, na której prowadzono testy

| Ustawienie | Wartość |
| --- | --- |
| `MODULE_MODE_DEFAULT` | `real` |
| `MODULE_MODE_*` | `real` dla cases, ingest, archive, routing, drafting, anonymize, inference, audit |
| `MODULE_MODE_INFERENCE_EMBEDDING` | `fake` — Mistral nie serwuje `BAAI/bge-m3`, archiwum działa na BM25 i pokryciu leksykalnym |
| `LLM_PROVIDER` / `LLM_MODEL` | `mistral` / `mistral-small-latest` |
| `LLM_TIMEOUT_S` / `LLM_MAX_TOKENS` / `LLM_TEMPERATURE` | 60 / 2048 / 0,2 |
| `OFFLINE` | `false` |
| `AUTH_ENABLED` | `true` |
| `DEMO_TODAY` | `2026-03-16` |
| `DATABASE_URL` | `sqlite:///./data/app.db` |

Potwierdzenie z `GET /api/health`:

```json
{"status":"ok","version":"0.1.0","modules":{"cases":"real","ingest":"real",
"archive":"real","routing":"real","drafting":"real","anonymize":"real",
"inference":"real","audit":"real"}}
```

## 2. Metoda

Testy prowadzono na trzech poziomach, żeby nie opierać się wyłącznie na tym, co widać w interfejsie:

1. **Testy jednostkowe i integracyjne repozytorium** — `pytest` (478 testów) i `vitest` (191 testów).
2. **Bezpośrednie wywołania adapterów** — `container.get_llm()`, `get_cases()`, `get_archive()`,
   `get_documents()` w procesie Pythona, z pomiarem czasu i inspekcją surowej odpowiedzi modelu.
3. **Pełna ścieżka przez HTTP** — logowanie, wgranie plików, kalendarz, archiwum, routing,
   zapytanie, projekt, zapis, eksport, anonimizacja, przejścia stanów, audyt.
4. **Interfejs w przeglądarce** — te same ekrany na realnym backendzie.

Pomiary jakości generatora: 5 spraw × 4 generacje = 20 prób, każda z inspekcją surowej
odpowiedzi modelu przed i po normalizacji.

## 3. Wyniki pozytywne

| Obszar | Wynik |
| --- | --- |
| Wgranie PDF / DOCX / TXT | 19–102 ms, status `indexed`, polskie znaki zachowane, fragmenty policzone |
| Odczyt dokumentu | 591–3250 znaków, 1–5 fragmentów, `page_count` poprawny |
| Kalendarz (SQLite) | 10 spraw, `days_remaining` i `urgency` liczone z `DEMO_TODAY` |
| Archiwum | 5 wyników, oceny 0,867 → 0,278 (malejąco), 13–22 ms |
| Routing | 26 komórek, WGN 98% dla najmu lokali, wyjaśnienie pokrycia („3 z 6 istotnych słów") |
| Zapytanie do komórek | numer sprawy i termin obecne w treści |
| Generator (Mistral) | 3,5–6,6 s na projekt, 8–16 cytowań, zero wiszących odnośników |
| Zapis projektu | nowa treść i kolejna wersja |
| Eksport DOCX / PDF / MD | 200, poprawne nagłówki plików (`PK`, `%PDF`), `X-Redactions` |
| Anonimizacja | 6 kategorii, precyzja 1,00, pełność 1,00, F1 1,00 |
| Przejścia stanów | pełny łańcuch `nowy → zapytania_wyslane → kwerenda → przygotowana_odpowiedz → odpowiedz_wyslana` |
| Kwerenda | `kwerenda_days=14` przesuwa termin (23.03 → 06.04), `response_date` ustawiane przy zamknięciu |
| Cofnięcie stanu bez notatki | odrzucone, HTTP 409, komunikat „Cofnięcie stanu wymaga notatki." |
| Audyt | 63 wpisy, akcje: `case.transitioned`, `document.uploaded`, `draft.exported`, `draft.generated`, `draft.saved` |
| Archiwum rośnie | zamknięte sprawy wchodzą jako `n0001` (0,985) i `n0002` (0,990) |

### Obsługa awarii modelu

Wszystkie scenariusze awarii kończą się kontrolowanym wyjątkiem, nie błędem 500:

| Scenariusz | Zachowanie |
| --- | --- |
| Zły klucz API | `InferenceError`: „Serwer modelu zwrócił błąd HTTP 401: Invalid API Key" |
| `health()` przy złym kluczu | `status=down`, komunikat z przyczyną, latencja zmierzona |
| `OFFLINE=true` | `OfflineViolation` z instrukcją wyłączenia trybu |
| Serwer nie odpowiada | `InferenceError`: „Przekroczono limit czasu 2 s — serwer modelu pod adresem … nie odpowiedział." |
| Puste `choices` | `InferenceError`: „Odpowiedź serwera modelu nie zawiera treści…" |
| HTTP 500 od dostawcy | `InferenceError` z kodem i treścią odpowiedzi |
| Śmieciowa odpowiedź („Nie wiem.") | przechodzi do `is_usable`, zostaje odrzucona, projekt z szablonu |

## 4. Błędy

### P1 — Co piąty projekt po cichu schodzi do szablonu (wysoki)

**Pomiar:** 4 z 20 generacji (20%) nie pochodziło z modelu, mimo że model zwrócił
poprawną, kompletną treść 1500–2500 znaków.

**Przyczyna:** model pisze odnośniki jako `[1]`, `[2]`, a nie `[^1]`, `[^2]`.
[`backend/app/modules/drafting/prompt.py:33`](backend/app/modules/drafting/prompt.py:33)
definiuje `_MARKER = re.compile(r"\[\^(\d+)\]")`, więc
[`is_usable`](backend/app/modules/drafting/prompt.py:134) nie znajduje ani jednego
odnośnika i odrzuca całą treść. [`LlmDrafting.draft`](backend/app/adapters/real/drafting.py:137)
podmienia ją wtedy na szablon i dopisuje do `unsupported` notatkę
„Model językowy zwrócił treść, której nie można wykorzystać w projekcie pisma — użyto szablonu."

**Dowód:** wszystkie cztery degradacje miały dokładnie ten sam profil — `[^n]=0`, `[n]=19–23`.

**Poprawka (zweryfikowana):** normalizacja `[n]` → `[^n]` w
[`normalize_model_output`](backend/app/modules/drafting/prompt.py:123), z pominięciem
odnośników już poprawnych i linków markdown. Na tych samych próbkach, które wcześniej
przepadały, `is_usable` zwraca `True`. Regex użyty w weryfikacji:

```python
_PLAIN_REF = re.compile(r"(?<!\^)\[(\d{1,2})\](?!\()")
```

**Skutek dla użytkownika:** urzędnik dostaje dłuższy, szablonowy projekt zamiast treści
napisanej przez model, bez wyraźnego sygnału, że tak się stało — notatka ląduje w panelu
„Twierdzenia bez źródła" (patrz P5).

### P2 — Szablon cytuje każdy artykuł wgranej ustawy (wysoki)

**Pomiar:** po wgraniu `fixtures/statutes/udip.txt` jako dokumentu rodzaju `ustawa`
powstaje 12 źródeł-artykułów. Projekt dla `UDIP.1435.9.2026` ma wtedy 3808 znaków
i 12 zdań „Podstawę prawną stanowi art. N — udip: …". Ten sam wniosek bez wgranej
ustawy: 2027 znaków i jedno takie zdanie.

**Przyczyna:** [`_uploaded_statute_sentences`](backend/app/modules/drafting/template.py:96)
wstawia dosłowny cytat każdego źródła typu `statute`, którego nie ma w `_LEGAL_SENTENCES`.
Docstring wyjaśnia intencję („szablon nie zna jego treści"), ale przy całym akcie
daje ścianę cytatów zamiast podstawy prawnej.

**Skutek:** README reklamuje wgrywanie ustaw jako funkcję („wgrany akt wchodzi do
podstawy prawnej projektu"). W praktyce pismo z taką podstawą prawną nie nadaje się
do wysłania.

### P3 — Definicje przypisów przeciekają do treści pisma (średni)

**Pomiar:** w 6 z 35 obserwowanych generacji (17%) model dokleja na końcu blok
definicji przypisów. Przykład z `UDIP.1435.5.2026`:

```
[^1]: art. 13 ust. 1 i 2 ustawy o dostępie do informacji publicznej
[^2]: art. 10 ust. 1 ustawy o dostępie do informacji publicznej
[^3]: art. 5 ust. 2 ustawy o dostępie do informacji publicznej
[^4]: art. 16 ustawy o dostępie do informacji publicznej
[^5]: § 4 zarządzenia nr 412/2023 Prezydenta Miasta Bydgoszczy
[^6]: sprawa archiwalna UDIP.1435.52.2025
```

**Przyczyna:** `is_usable` sprawdza tylko obecność nagłówka i odnośnika, nie sprawdza
struktury. `strip_invalid_refs` usuwa odnośniki do nieistniejących źródeł, ale nie
blok definicji.

**Skutek:** blok trafia do eksportu DOCX i PDF jako zwykły tekst na końcu pisma.

### P4 — Wgranie dokumentu i eksport w interfejsie zwracają 401 (wysoki)

**Pomiar:** oba działania kończą się toastem:

- „Nie udało się wgrać dokumentu / Wymagane zalogowanie."
- „Nie udało się wyeksportować projektu / Wymagane zalogowanie."

Przez API te same operacje przechodzą (`POST /api/documents` → 201,
`GET /api/drafting/{id}/export` → 200).

**Przyczyna:** dwa miejsca omijają wspólny klient HTTP z
[`frontend/src/lib/api.ts`](frontend/src/lib/api.ts), który dokleja `Authorization: Bearer`:

- [`frontend/src/features/ingest/api.ts:89`](frontend/src/features/ingest/api.ts:89) — `XMLHttpRequest` bez nagłówka,
- [`frontend/src/features/drafting/api.ts:85`](frontend/src/features/drafting/api.ts:85) — goły `fetch` bez nagłówka.

**Skutek:** przy `AUTH_ENABLED=true` (czyli w domyślnej konfiguracji) krok 3 z
`docs/DEMO.md` i cały eksport są niedostępne z interfejsu.

### P5 — Komunikat o degradacji trafia do panelu „Twierdzenia bez źródła" (średni)

Notatka „Model językowy zwrócił treść, której nie można wykorzystać… użyto szablonu."
jest wyświetlana w panelu
[`UnsupportedPanel`](frontend/src/features/drafting/UnsupportedPanel.tsx) pod nagłówkiem
„Twierdzenia bez źródła" i podpisem „Te zdania nie mają pokrycia w źródłach. Uzupełnij je
albo usuń przed wysłaniem."

Komunikat systemowy nie jest twierdzeniem merytorycznym — urzędnik dostaje polecenie
uzupełnienia czegoś, czego uzupełnić nie może. Notatka powinna mieć osobne miejsce
(albo osobne pole w kontrakcie, np. `degraded: bool` + `degraded_reason`).

### P6 — Ustawienia opisują moduły niezgodnie z kodem (średni)

| Plik | Tekst w interfejsie | Stan faktyczny |
| --- | --- | --- |
| [`settings/modules.ts:40`](frontend/src/features/settings/modules.ts:40) | „Komórkę wskazuje model na podstawie treści wniosku." | [`routing.py`](backend/app/adapters/real/routing.py) — dopasowanie słów kluczowych z rdzeniowaniem, frazami i IDF. Model nie bierze udziału. |
| [`settings/modules.ts:50`](frontend/src/features/settings/modules.ts:50) | „Reguły plus model rozpoznający nazwiska i adresy." | [`anonymize.py`](backend/app/adapters/real/anonymize.py) — detektory regułowe; spaCy jest opcjonalny i przy braku modelu następuje cicha degradacja do reguł. W testach każdy span miał etykietę „reguła". |
| [`settings/modules.ts:55`](frontend/src/features/settings/modules.ts:55) | „Zapytania idą do modelu: llama.cpp, Ollama albo OpenAI." | Skonfigurowany dostawca to Mistral (La Plateforme), którego lista nie wymienia. |

Ekran Ustawienia jest miejscem, w którym jury sprawdza, co jest atrapą, a co nie —
opisy powinny odpowiadać kodowi.

### P7 — Testy nie dotykają modelu (wysoki, procesowy)

- `pytest`: 478 testów, wszystkie przechodzą.
- `vitest`: 191 testów, wszystkie przechodzą.
- [`tests/test_inference_real.py`](backend/tests/test_inference_real.py) używa `httpx.MockTransport` — „testy nie dotykają sieci i nie potrzebują uruchomionego modelu".
- [`tests/test_e2e_flow.py`](backend/tests/test_e2e_flow.py) deklaruje wprost: „Test jest wolny od sieci i modeli: warstwa `inference` w trybie `real` nie znajduje serwera modelu, więc generator odpowiedzi schodzi do szablonu".

Żaden test w repozytorium nie wywołuje Mistrala. Dlatego P1 i P3 — czyli 20% degradacji
i 17% przecieków — nie zostały wychwycone. Ścieżka z modelem jest jedyną, która odróżnia
projekt od atrapy, i jest jedyną nieprzetestowaną.

### P8 — Ponowne wgranie tego samego pliku tworzy duplikat (niski)

Ten sam plik wgrany trzy razy daje trzy dokumenty w bazie wiedzy, bez ostrzeżenia
i bez deduplikacji. W trakcie testów powstało 9 duplikatów, które trzeba było usuwać
ręcznie przez `DELETE /api/documents/{id}`.

### P9 — Historia sprawy w trybie realnym nie ma wpisu o utworzeniu (niski)

Atrapa pokazuje w historii „Utworzenie sprawy" z datą wpływu. Adapter realny zaczyna
historię od pierwszego przejścia stanu, więc nietknięta sprawa ma pustą historię.

### P10 — Znaczniki czasu używają realnego zegara (niski)

Przy `DEMO_TODAY=2026-03-16` wpisy historii i audytu mają daty z rzeczywistego zegara
(22 listopada 2026). Terminy są zakotwiczone, znaczniki akcji nie — w demo wygląda to
jak błąd, bo sprawa z marca 2026 dostaje wpis z listopada 2026.

## 5. Latencja modelu

20 generacji, `mistral-small-latest`, `max_tokens=2048`, `temperature=0,2`:

| Metryka | Wartość |
| --- | --- |
| minimum | 3536 ms |
| mediana | 5009 ms |
| maksimum | 6636 ms |
| `POST /api/inference/test` | 558 ms, `ok=true` |
| `GET /api/inference/health` | 216–282 ms |

Pojedynczy projekt mieści się w 3,5–6,6 s. Przy ośmiu sprawach na ekranie i generowaniu
po kolei to 30–50 s — warto rozważyć generowanie równoległe albo strumieniowanie.

## 6. Jak odtworzyć

```bash
# środowisko
scripts/demo.sh                      # czyści data/, ustawia tryb i DEMO_TODAY
# tryb realny: ustaw w backend/.env MODULE_MODE_DEFAULT=real i LLM_* dla Mistrala

# testy repozytorium
cd backend && .venv/bin/python -m pytest -q
cd frontend && npm run test

# pomiar degradacji i przecieków (skrypt poza repozytorium)
cd backend && .venv/bin/python /tmp/real_test_quality.py
```

## 7. Stan po testach

- Dokumenty w bazie: `wniosek-01-wynagrodzenia`, `wniosek-03-wycinka-drzew`, `odpowiedz-wydzialu-01`. Duplikaty i wgrana ustawa `udip` usunięte.
- Projekty wygenerowane dla: `UDIP.1435.1.2026`, `UDIP.1435.2.2026`, `UDIP.1435.3.2026`, `UDIP.1435.4.2026`, `UDIP.1435.9.2026`.
- Zamknięte: `UDIP.1435.5.2026`, `UDIP.1435.6.2026` — weszły do archiwum jako `n0001` i `n0002`.
- Reset do stanu wyjściowego: `scripts/demo.sh`.

## 8. Wnioski

Rdzeń działa. Realne parsery, SQLite, wyszukiwanie w archiwum, routing, anonimizacja,
przejścia stanów i audyt zachowują się zgodnie z kontraktem, a obsługa awarii modelu jest
poprawna — żaden scenariusz nie kończy się błędem 500.

Warstwa modelu jest jednak niedomknięta w trzech miejscach, które widać dopiero przy
prawdziwym Mistralu: odrzucanie poprawnych odpowiedzi z powodu formatu odnośnika (P1),
cytowanie całych ustaw w szablonie (P2) i przeciek definicji przypisów (P3). Do tego dwa
miejsca w interfejsie nie wysyłają tokenu (P4), co przy włączonym logowaniu odcina
wgranie pliku i eksport.

Najpilniejsze do naprawy, w kolejności: **P4** (blokuje demo), **P1** (20% projektów),
**P2** (nieczytelna podstawa prawna po wgraniu ustawy), **P3** (defekt w wysyłanym piśmie),
**P7** (test, który woła model — bez niego P1 i P3 wrócą).
