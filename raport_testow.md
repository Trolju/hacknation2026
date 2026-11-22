# Raport z testów — tryb realny (8/8 modułów) z modelem Mistral

Data pierwszego przebiegu: 22 listopada 2026
Data powtórnego przebiegu: 22 listopada 2026, po commicie `5356e68`
Środowisko: lokalne, backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:5173`
Zakres: wszystkie osiem modułów na adapterach `real`, generator odpowiedzi na żywym
Mistralu (`mistral-small-latest`). Nie atrapy.

---

## 0. Podsumowanie powtórnego przebiegu

Dziesięć ustaleń z pierwszego raportu jest naprawionych i zweryfikowanych na żywym
modelu. Pomiary, które wcześniej pokazywały problem, są teraz zerowe:

| Miara | Przed | Po |
| --- | --- | --- |
| Degradacja do szablonu | 4/20 (20%) | **0/20 (0%)** |
| Przeciek definicji przypisów | 6/35 (17%) | **0/20 (0%)** |
| Zdań „Podstawę prawną stanowi art. N…” po wgraniu ustawy | 12 | **0** |
| Długość projektu z wgraną ustawą | 3808 znaków | **2096 znaków** |
| Wgranie dokumentu w UI | 401 | **201, toast o sukcesie** |
| Eksport DOCX w UI | 401 | **plik pobrany** |
| Testy backendu | 478 | **512** (+1 pominięty) |
| Testy frontendu | 191 | **195** |
| Test wołający prawdziwe API | brak | **7 przechodzi w 5,3 s** |

Powtórny przebieg odsłonił jednak pięć nowych ustaleń (P11–P15), w tym jedno
wprowadzone przez naprawę P2. Opisane w sekcji 5.

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

Testy prowadzono na czterech poziomach, żeby nie opierać się wyłącznie na tym, co widać
w interfejsie:

1. **Testy jednostkowe i integracyjne repozytorium** — `pytest` i `vitest`, plus test
   na żywo pod `MISTRAL_LIVE=1`.
2. **Bezpośrednie wywołania adapterów** — `container.get_llm()`, `get_cases()`,
   `get_archive()`, `get_documents()` w procesie Pythona, z pomiarem czasu i inspekcją
   surowej odpowiedzi modelu.
3. **Pełna ścieżka przez HTTP** — logowanie, wgranie plików, kalendarz, archiwum,
   routing, zapytanie, projekt, zapis, eksport, anonimizacja, przejścia stanów, audyt.
4. **Interfejs w przeglądarce** — te same ekrany na realnym backendzie.

Pomiary jakości generatora: 5 spraw × 4 generacje = 20 prób, każda z inspekcją surowej
odpowiedzi modelu przed i po normalizacji. Ten sam skrypt w obu przebiegach.

## 3. Wyniki pozytywne

| Obszar | Wynik |
| --- | --- |
| Wgranie PDF / DOCX / TXT | 19–102 ms, status `indexed`, polskie znaki zachowane, fragmenty policzone |
| Odczyt dokumentu | 591–3250 znaków, 1–5 fragmentów, `page_count` poprawny |
| Kalendarz (SQLite) | 10 spraw, `days_remaining` i `urgency` liczone z `DEMO_TODAY` |
| Archiwum | 5 wyników, oceny 0,866 → 0,278 (malejąco), 7–22 ms |
| Routing | 26 komórek, WGN 98% dla najmu lokali, wyjaśnienie pokrycia („3 z 6 istotnych słów") |
| Zapytanie do komórek | numer sprawy i termin obecne w treści |
| Generator (Mistral) | 2,8–6,0 s na projekt, 5–14 cytowań, zero wiszących odnośników |
| Zapis projektu | nowa treść i kolejna wersja |
| Eksport DOCX / PDF / MD | 200, poprawne nagłówki plików (`PK`, `%PDF`), `X-Redactions` |
| Anonimizacja | 6 kategorii, precyzja 1,00, pełność 1,00, F1 1,00 |
| Przejścia stanów | pełny łańcuch `nowy → zapytania_wyslane → kwerenda → przygotowana_odpowiedz → odpowiedz_wyslana` |
| Kwerenda | `kwerenda_days=14` przesuwa termin (06.03 → 20.03), `response_date` ustawiane przy zamknięciu |
| Cofnięcie stanu bez notatki | odrzucone, HTTP 409, komunikat „Cofnięcie stanu wymaga notatki." |
| Cofnięcie stanu z notatką | przechodzi, HTTP 200 |
| Audyt | 85 wpisów, akcje: `case.transitioned`, `document.uploaded`, `document.deleted`, `draft.exported`, `draft.generated`, `draft.saved` |
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
| Śmieciowa odpowiedź („Nie wiem.") | `degraded=True`, `degraded_reason` ustawione, projekt z szablonu |

## 4. Ustalenia z pierwszego przebiegu — status po naprawie

| # | Ustalenie | Status | Dowód z powtórnego przebiegu |
| --- | --- | --- | --- |
| P1 | 20% projektów schodziło do szablonu przez `[n]` zamiast `[^n]` | **naprawione** | 20/20 projektów z modelu, `degraded=False` w każdym |
| P2 | Szablon cytował każdy artykuł wgranej ustawy | **naprawione** | 0 zdań „Podstawę prawną stanowi", 2096 znaków zamiast 3808 |
| P3 | Definicje przypisów przeciekały do treści pisma | **naprawione** | 0/20 prób z blokiem `[^n]:` w treści |
| P4 | Wgranie i eksport w UI zwracały 401 | **naprawione** | toast „Dokument wgrany i zaindeksowany", toast „Plik gotowy" |
| P5 | Notatka o degradacji trafiała do panelu „Twierdzenia bez źródła" | **naprawione** | osobny kafelek „Projekt z szablonu", panel nieobecny |
| P6 | Ustawienia opisywały moduły niezgodnie z kodem | **naprawione** | routing „bez udziału modelu językowego", spaCy „opcjonalny", Mistral na liście dostawców |
| P7 | Żaden test nie wołał modelu | **naprawione** | `test_drafting_mistral_contract.py`, 7 testów na żywo w 5,3 s |
| P8 | Ponowne wgranie tworzyło duplikat | **naprawione** | ten sam plik dwa razy → ten sam `id`; inna nazwa, ta sama treść → ten sam `id` |
| P9 | Historia w trybie realnym bez wpisu o utworzeniu | **naprawione** | 5 wpisów, pierwszy `created` z datą wpływu `2026-02-20T08:00:00` |
| P10 | Znaczniki czasu z realnego zegara | **naprawione** | historia i audyt z datą `2026-03-16`, godzina z realnego zegara |

### Szczegóły weryfikacji

**P1** — ten sam skrypt pomiarowy, 20 generacji:

```
prób: 20  |  z modelu: 20  |  degradacja do szablonu: 0 (0%)
przeciek definicji przypisów do treści: 0 (0%)
latencja: min=2791 mediana=3852 max=5984 ms
```

**P2** — po wgraniu `fixtures/statutes/udip.txt` jako `ustawa` projekt ma 2096 znaków
i ani jednego zdania „Podstawę prawną stanowi art. N — udip: …". Podstawa prawna brzmi:

> Niniejsza odpowiedź została przygotowana na podstawie przepisów ustawy z dnia
> 6 września 2001 r. o dostępie do informacji publicznej (Dz. U. z 2023 r. poz. 1479,
> z późn. zm.) [^2]…[^13], a także § 4 zarządzenia nr 412/2023 Prezydenta Miasta
> Bydgoszczy [^1].

**P5** — wymuszenie degradacji przez `MockTransport` ze śmieciową odpowiedzią:

```
degraded=True
degraded_reason='Model językowy zwrócił treść, której nie można wykorzystać
w projekcie pisma — użyto szablonu. Sprawdź każde twierdzenie przed wysłaniem.'
unsupported=[]
```

W interfejsie: kafelek „Projekt z szablonu" z tą treścią, panel „Twierdzenia bez źródła"
nie pojawia się.

**P8** — dwa wgrania `wniosek-02-najem-lokali.pdf` → `201` i `201`, oba z `id=f703af34`.
Ta sama treść pod inną nazwą → ten sam `id`.

**P10** — historia sprawy:

```
2026-02-20T08:00:00  —                        → None                     urzędnik
2026-03-16T02:50:44  zapytania_wyslane        → kwerenda                 Jan Kowalski
2026-03-16T02:50:44  kwerenda                 → przygotowana_odpowiedz   Jan Kowalski
2026-03-16T02:50:44  przygotowana_odpowiedz   → odpowiedz_wyslana        Jan Kowalski
2026-03-16T02:50:44  odpowiedz_wyslana        → kwerenda                 Jan Kowalski
```

## 5. Nowe ustalenia z powtórnego przebiegu

### P11 — Skrót „Dz. U." rozbija zdania i tworzy fałszywe „twierdzenia bez źródła" (średni)

**Pomiar:** 6 z 10 projektów (60%) ma w `unsupported` zdanie urwane w środku:

```
Niniejsza odpowiedź została przygotowana na podstawie przepisów ustawy z dnia
6 września 2001 r. o dostępie do informacji publicznej (Dz.
```

**Przyczyna:** [`_SENTENCE_END`](backend/app/modules/drafting/prompt.py:35) dzieli zdanie
po kropce, gdy następny znak jest wielką literą. W „Dz. U." po kropce staje „U", więc
podział następuje w środku cytatu aktu prawnego. Pierwszy fragment nie ma odnośnika
i trafia do `unsupported` jako twierdzenie bez pokrycia.

**Dowód jednostkowy:**

```
wejście: Niniejsza odpowiedź … (Dz. U. z 2023 r. poz. 1479) [^1].
  → [ 65] Niniejsza odpowiedź została przygotowana na podstawie ustawy (Dz.
  → [ 29] U. z 2023 r. poz. 1479) [^1].
find_unsupported → FAŁSZYWY ALARM: ['Niniejsza odpowiedź … (Dz.']
```

**Skutek:** urzędnik widzi ostrzeżenie o zdaniu bez źródła, które w rzeczywistości ma
trzynaście odnośników. „Dz. U." to standardowy sposób cytowania w pismach urzędowych,
więc problem będzie wracał. Wymaga listy skrótów wyłączonych z podziału (`Dz. U.`,
`art.`, `ust.`, `poz.`, `nr`, `r.`, `t.j.`).

**Uwaga:** to ustalenie pojawiło się po naprawie P2 — nowa podstawa prawna zawiera
„(Dz. U. z 2023 r. poz. …)", więc model cytuje akt w formie, która uruchamia podział.

### P12 — Nazwa pliku eksportu to fragment UUID, nie numer sprawy (niski)

```
Content-Disposition: attachment; filename="odpowiedz-c0000001-projekt.docx"
```

[`drafting.py:291`](backend/app/adapters/real/drafting.py:291) buduje nazwę jako
`odpowiedz-{draft.case_id.hex[:8]}-{suffix}`. Urzędnik zapisuje plik
`odpowiedz-c0000001-projekt.docx` zamiast `odpowiedz-UDIP.1435.7.2026-projekt.docx`.
Numer sprawy jest dostępny przez `_cases_port`, więc poprawka jest tania.

### P13 — Duplikaty sprzed naprawy zostają w bazie (niski)

Deduplikacja działa dla nowych wgrań, ale dokumenty wgrane przed commitem `5356e68`
nadal leżą w bazie podwójnie. W bazie testowej: `wniosek-01-wynagrodzenia` ×2,
`odpowiedz-wydzialu-01` ×2, `wniosek-03-wycinka-drzew` ×2. Migracja nie sprząta
istniejących rekordów — do rozważenia jednorazowy skrypt porządkowy albo `scripts/demo.sh`.

### P14 — Podstawa prawna zbiera do 13 odnośników pod rząd (niski)

**Pomiar:** 9 z 10 projektów (90%) ma w treści ciąg co najmniej trzech odnośników
bez przerwy; największy zaobserwowany to 13:

```
[^2][^3][^4][^5][^6][^7][^8][^9][^10][^11][^12][^13]
```

Model powołuje się jednym zdaniem na wszystkie artykuły wgranej ustawy. Merytorycznie
poprawne, typograficznie nieczytelne — w wydruku to trzynaście cyfr w indeksie górnym
przy jednym zdaniu. Warto ograniczyć liczbę odnośników w jednym zdaniu albo zgrupować
je jako zakres („art. 1–13").

### P15 — Sporadyczna data w formacie ISO w treści pisma (niski)

**Pomiar:** 1 z 10 projektów (10%) zawierał w treści `2026-03-02` i `2026-03-16` zamiast
„2 marca 2026 r." i „16 marca 2026 r.". W czterech kolejnych próbach na tej samej sprawie
problem się nie powtórzył — jest rzadki i zależny od sformułowania modelu.

Pismo urzędowe nie może zawierać daty ISO. Warto dodać normalizację dat w
`normalize_model_output` albo sprawdzenie w `find_unsupported`.

## 6. Latencja modelu

20 generacji, `mistral-small-latest`, `max_tokens=2048`, `temperature=0,2`:

| Metryka | Przebieg 1 | Przebieg 2 |
| --- | --- | --- |
| minimum | 3536 ms | 2791 ms |
| mediana | 5009 ms | 3852 ms |
| maksimum | 6636 ms | 5984 ms |
| `POST /api/inference/test` | 558 ms | 558 ms |
| `GET /api/inference/health` | 216–282 ms | 206 ms |

Pojedynczy projekt mieści się w 2,8–6,0 s. Przy ośmiu sprawach na ekranie i generowaniu
po kolei to 25–50 s — warto rozważyć generowanie równoległe albo strumieniowanie.

## 7. Jak odtworzyć

```bash
# środowisko
scripts/demo.sh                      # czyści data/, ustawia tryb i DEMO_TODAY
# tryb realny: ustaw w backend/.env MODULE_MODE_DEFAULT=real i LLM_* dla Mistrala

# testy repozytorium
cd backend && .venv/bin/python -m pytest -q
cd frontend && npm run test

# test na żywym API (wymaga klucza)
cd backend && LLM_API_KEY=... MISTRAL_LIVE=1 .venv/bin/python -m pytest \
  tests/test_drafting_mistral_contract.py -q

# pomiar degradacji i przecieków (skrypt poza repozytorium)
cd backend && .venv/bin/python /tmp/real_test_quality.py
```

## 8. Stan po testach

- Dokumenty w bazie: 8 pozycji, w tym trzy duplikaty sprzed naprawy P8 (patrz P13).
- Projekty wygenerowane dla wszystkich spraw poza zamkniętymi.
- Zamknięte: `UDIP.1435.5.2026`, `UDIP.1435.6.2026`, `UDIP.1435.9.2026` — weszły do archiwum jako `n0001`–`n0003`.
- Reset do stanu wyjściowego: `scripts/demo.sh`.

## 9. Wnioski

Wszystkie dziesięć ustaleń z pierwszego raportu jest naprawionych i potwierdzonych na
żywym modelu. Najważniejsze: degradacja spadła z 20% do zera, przecieki przypisów
zniknęły, wgranie i eksport działają z interfejsu, a test na żywo pod `MISTRAL_LIVE=1`
domyka lukę, przez którą P1 i P3 wcześniej przeszły przez 478 testów.

Powtórny przebieg pokazał jednak, że naprawa P2 odsłoniła P11: skrót „Dz. U." rozbija
zdania i w 60% projektów tworzy fałszywe ostrzeżenie o twierdzeniu bez źródła. To
najpoważniejsze z nowych ustaleń, bo dotyka zaufania do panelu kontroli — urzędnik,
który raz zobaczy fałszywy alarm, przestanie czytać ostrzeżenia.

Kolejność dalszych prac: **P11** (fałszywe alarmy), **P14** (klaster odnośników),
**P15** (data ISO w piśmie), **P12** (nazwa pliku), **P13** (sprzątanie duplikatów).
