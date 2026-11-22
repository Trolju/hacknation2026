# Raport z testów — tryb realny (8/8 modułów) z modelem Mistral

Data pierwszego przebiegu: 22 listopada 2026
Data drugiego przebiegu: 22 listopada 2026, po commicie `5356e68`
Data trzeciego przebiegu: 22 listopada 2026, po commicie `cbf7ee1`
Data czwartego przebiegu: 22 listopada 2026, po commicie `0fadae0`
Data piątego przebiegu: 22 listopada 2026, po commicie `0db966c`
Środowisko: lokalne, backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:5173`
Zakres: wszystkie osiem modułów na adapterach `real`, generator odpowiedzi na żywym
Mistralu (`mistral-small-latest`). Nie atrapy.

---

## 0. Podsumowanie piątego przebiegu

Wszystkie szesnaście ustaleń z poprzednich przebiegów pozostaje zamkniętych. Piąty
przebieg nie znalazł ani jednej regresji i ani jednego nowego ustalenia.

| Miara | Przebieg 4 | Przebieg 5 |
| --- | --- | --- |
| Testy backendu | 564 (+1 pominięty) | **584 (+1 pominięty)** |
| Testy frontendu | 199 | **199** |
| Test wołający prawdziwe API | 7 w 3,58 s | **7 w 4,91 s** |
| Degradacja do szablonu | 0/20 | **0/20** |
| Przeciek definicji przypisów | 0/20 | **0/20** |
| Fałszywe alarmy „Dz. U." | 0/10 | **0/10** |
| Przebiegi ≥3 odnośników ściśle kolejnych | 0/10 | **0/10** |
| Daty ISO w treści pisma | 0/10 | **0/10** |
| Odnośniki bez cytatu w panelu | 0/10 | **0/10** |
| Carety `[^n]` w eksporcie | 0 | **0 w MD, DOCX i PDF** |
| Ścieżka HTTP (43 asercje) | — | **43/43 OK** |

## 1. Co zmieniło się od czwartego przebiegu

Między `0fadae0` a `0db966c` projekt przeszedł zmiany, które nie dotyczyły logiki
generatora, ale zmieniły dane i interfejs:

| Zmiana | Skutek dla testów |
| --- | --- |
| Nazwa projektu: **Capricorn**, zespół sLaRpNaTiOn | tytuł strony i nagłówek aplikacji |
| Numeracja spraw: `UDIP.1435.N.2026` → **`BKS.IV.1431.N.2026`** | wszystkie skrypty testowe przestawione na nowy format |
| Pełna lista **28 kategorii anonimizacji UMB** (32 wewnętrznie) | nowe kategorie: `wizerunek`, `zdrowie`, `orientacja`, `karalnosc`, tajemnice ustawowe |
| Termin opisowy (`deadline_note`) | sprawy mogą mieć termin w formie „19.08.2026/18.09.2026 — doprecyzowanie wniosku" |
| Moduł **przypomnień** | nowy endpoint `GET /api/reminders`, dzwonek w nagłówku |
| Dialog nowej sprawy | tworzenie sprawy z poziomu kalendarza |
| Nowy szablon podstawy prawnej | cytuje pojedyncze artykuły zamiast ciągu odnośników |

## 2. Konfiguracja, na której prowadzono testy

| Ustawienie | Wartość |
| --- | --- |
| `MODULE_MODE_DEFAULT` | `real` |
| `MODULE_MODE_*` | `real` dla cases, ingest, ingest_parser, archive, routing, drafting, anonymize, inference, audit |
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

## 3. Metoda

Testy prowadzono na pięciu poziomach, żeby nie opierać się wyłącznie na tym, co widać
w interfejsie:

1. **Testy jednostkowe i integracyjne repozytorium** — `pytest` i `vitest`, plus test
   na żywo pod `MISTRAL_LIVE=1`.
2. **Bezpośrednie wywołania adapterów** — `container.get_llm()`, `get_cases()`,
   `get_archive()`, `get_documents()` w procesie Pythona, z pomiarem czasu i inspekcją
   surowej odpowiedzi modelu.
3. **Pełna ścieżka przez HTTP** — 43 asercje: sprawy, nowa sprawa, przejścia stanów,
   historia, audyt, dokumenty, routing, archiwum, anonimizacja, przypomnienia,
   inference, uwierzytelnianie.
4. **Interfejs w przeglądarce** — wszystkie osiem ekranów, wgranie pliku, kliknięcie
   cytowania, eksport pliku.
5. **Inspekcja plików eksportu** — DOCX rozpakowany (`word/document.xml`), PDF przez
   `pdftotext`, MD jako tekst. Sprawdzane, czy znaczniki odnośników są w formie `[n]`,
   a nie `[^n]`.

Pomiary jakości generatora: 5 spraw × 4 generacje = 20 prób, każda z inspekcją surowej
odpowiedzi modelu przed i po normalizacji. Ten sam skrypt we wszystkich pięciu przebiegach.

## 4. Wyniki pozytywne

| Obszar | Wynik |
| --- | --- |
| Wgranie PDF / DOCX / TXT | 201, status `indexed`, polskie znaki zachowane, fragmenty policzone |
| Ponowne wgranie tego samego pliku | ten sam `id`, zero duplikatów |
| Odczyt dokumentu | 583 i 769 znaków, `page_count=1`, po 1 fragmencie |
| Kalendarz (SQLite) | 10 spraw demo, `days_remaining` i `urgency` liczone z `DEMO_TODAY` |
| Nowa sprawa | 201, status `nowy`, termin policzony (8 dni), duplikat numeru → 409 |
| Archiwum | 5 wyników, oceny 0,898 → 0,233 (malejąco) |
| Routing | 26 komórek, WGN 0,98 dla najmu lokali, uzasadnienie z dopasowanymi słowami |
| Generator (Mistral) | 3,4–6,8 s na projekt, 3–8 cytowań, zero wiszących odnośników |
| Zapis projektu | nowa treść i kolejna wersja |
| Eksport DOCX / PDF / MD | 200, poprawne nagłówki plików (`PK`, `%PDF`), nazwa z numerem sprawy |
| Anonimizacja | 6 encji, 6 kategorii, precyzja 0,966, pełność 0,977, F1 0,972 |
| Przejścia stanów | 7/7 scenariuszy, pełny łańcuch `nowy → zapytania_wyslane → kwerenda → przygotowana_odpowiedz → odpowiedz_wyslana` |
| Kwerenda | `kwerenda_days=14` zapisane i przesuwa termin |
| Cofnięcie stanu bez notatki | odrzucone, HTTP 409 |
| Cofnięcie stanu z notatką | przechodzi, HTTP 200 |
| Historia sprawy | 6 wpisów, pierwszy `created` z datą wpływu, autor i data w każdym |
| Audyt | 69 wpisów, akcje: `case.created`, `case.transitioned`, `document.uploaded`, `draft.exported`, `draft.generated` |
| Przypomnienia | 3 pozycje |
| Inference | `health` ok w 324 ms, `test` 1004 ms, katalog 66 modeli |
| Uwierzytelnianie | sesja JK, zły PIN → 401, brak tokenu → 401 |

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

## 5. Ustalenia z pierwszego przebiegu (P1–P10) — nadal naprawione

| # | Ustalenie | Status | Dowód z piątego przebiegu |
| --- | --- | --- | --- |
| P1 | 20% projektów schodziło do szablonu przez `[n]` zamiast `[^n]` | **naprawione** | 20/20 projektów z modelu, `degraded=False` w każdym |
| P2 | Szablon cytował każdy artykuł wgranej ustawy | **naprawione** | 0 zdań „Podstawę prawną stanowi", 1235–3146 znaków |
| P3 | Definicje przypisów przeciekały do treści pisma | **naprawione** | 0/20 prób z blokiem `[^n]:` w treści |
| P4 | Wgranie i eksport w UI zwracały 401 | **naprawione** | toast „Dokument wgrany i zaindeksowany", plik DOCX pobrany (38 055 B) |
| P5 | Notatka o degradacji trafiała do panelu „Twierdzenia bez źródła" | **naprawione** | osobny kafelek „Projekt z szablonu", panel nieobecny |
| P6 | Ustawienia opisywały moduły niezgodnie z kodem | **naprawione** | routing „bez udziału modelu językowego", spaCy „opcjonalny", Mistral na liście dostawców |
| P7 | Żaden test nie wołał modelu | **naprawione** | `test_drafting_mistral_contract.py`, 7 testów na żywo w 4,91 s |
| P8 | Ponowne wgranie tworzyło duplikat | **naprawione** | ten sam plik dwa razy → ten sam `id` |
| P9 | Historia w trybie realnym bez wpisu o utworzeniu | **naprawione** | 6 wpisów, pierwszy `created` z datą wpływu |
| P10 | Znaczniki czasu z realnego zegara | **naprawione** | historia i audyt z datą `2026-03-16`, godzina z realnego zegara |

## 6. Ustalenia z drugiego i trzeciego przebiegu (P11–P16) — naprawione

| # | Ustalenie | Status | Dowód z piątego przebiegu |
| --- | --- | --- | --- |
| P11 | Skrót „Dz. U." rozbijał zdania i tworzył fałszywe „twierdzenia bez źródła" | **naprawione** | 0/10 fałszywych alarmów (było 6/10) |
| P12 | Nazwa pliku eksportu to fragment UUID | **naprawione** | `odpowiedz-BKS.IV.1431.7.2026-projekt.docx` |
| P13 | Duplikaty sprzed naprawy zostawały w bazie | **naprawione** | 0 par duplikatów |
| P14 | Podstawa prawna zbierała do 13 odnośników pod rząd | **naprawione** | 0/10 przebiegów ≥3 ściśle kolejnych; nowy szablon cytuje pojedyncze artykuły |
| P15 | Sporadyczna data ISO w treści pisma | **naprawione** | 0/10 projektów z datą ISO |
| P16 | Eksport Markdown zostawiał surowe `[^n]` | **naprawione** | 0 caretów w MD, DOCX i PDF |

### P11 — podział zdań na skrótach

`_sentences` nie dzieli już na „Dz. U.", „art.", „ust.", „poz.", „nr", „r." ani „t.j.".
Pomiar na 10 projektach: `unsupported` zawiera wyłącznie prawdziwe twierdzenia bez
źródła, np. „W związku z powyższym informuje się, że wnioskowane umowy … nie zostały
dotychczas opublikowane w BIP". To zdanie istotnie nie ma pokrycia w źródłach — panel
działa zgodnie z przeznaczeniem.

### P12 — nazwa pliku eksportu

```
Content-Disposition: attachment; filename="odpowiedz-BKS.IV.1431.7.2026-projekt.md"
Content-Disposition: attachment; filename="odpowiedz-BKS.IV.1431.7.2026-projekt.docx"
Content-Disposition: attachment; filename="odpowiedz-BKS.IV.1431.7.2026-projekt.pdf"
```

### P13 — sprzątanie duplikatów

Skrypt `backend/scripts/dedup_documents.py`. W piątym przebiegu ponowne wgranie tego
samego pliku zwróciło ten sam `id`, więc duplikat nie powstaje u źródła.

### P14 — zwężanie przebiegów odnośników

`collapse_ref_runs` zamienia ciąg trzech i więcej odnośników na zakres, każdy ciągły
fragment osobno. Numer wypadający z kolejności zostaje wypisany, bo zakres obejmujący
lukę kłamałby o treści:

```
[^2][^3][^4]                          → [^2]–[^4]
[^2][^3]                              → [^2][^3]        (dwa to nie przebieg)
[^2][^5][^9]                          → [^2][^5][^9]
[^2][^3]…[^12][^16]                   → [^2]–[^12][^16]
[^2][^3][^4][^5][^9][^10][^11]        → [^2]–[^5][^9]–[^11]
```

Pomiar na 10 projektach: zero przebiegów trzech i więcej odnośników ściśle kolejnych
i tekstowo przylegających. Nowy szablon podstawy prawnej cytuje pojedyncze artykuły
(`[^2]`, `[^1]`, `[^3]`, `[^5]`), więc przebiegi w ogóle nie powstają.

Kliknięcie cytowania ze środka zakresu obsługuje
[`markerRangeFor`](frontend/src/features/drafting/markdown.ts:277) wołane z
[`Editor.tsx:134`](frontend/src/features/drafting/Editor.tsx:134) jako ścieżka zapasowa.
Pokryte 19 testami w `markdown.test.ts`.

### P15 — daty w treści

Zero wystąpień `RRRR-MM-DD` w dziesięciu projektach. Daty w treści mają formę
„2 marca 2026 r." i „16 marca 2026 r.".

### P16 — eksport bez caretów

[`render_markdown`](backend/app/modules/drafting/export.py:203) woła `markers_to_plain`,
które zdejmuje sam caret, zostawiając nagłówki i pogrubienia Markdownem. Wszystkie trzy
formaty podają ten sam znacznik:

| Format | Znaczniki w treści | Carety |
| --- | --- | --- |
| MD | `[1]`, `[7]`, `[5]` … | 0 |
| DOCX | `[1]`, `[7]`, `[5]` … (indeks górny) | 0 |
| PDF | `[1]`, `[7]`, `[5]` … | 0 |

## 7. Obserwacja otwarta świadomie

### P17 — edytor pokazuje `[^2]` zamiast `[2]` (tak ma być)

Edytor prezentuje źródło Markdownu, a nie wersję złożoną, więc odnośniki widać
dosłownie. To nie usterka i nie jest przewidziane do zmiany: TipTap ze `StarterKit` nie ma
znacznika indeksu górnego, a podmiana wymagałaby własnego węzła i zachowania atrybutu
w `parseHtml` — inaczej zapis projektu zgubiłby odnośniki. Formą złożoną jest panel
cytowań obok edytora i eksport.

## 8. Latencja modelu

20 generacji, `mistral-small-latest`, `max_tokens=2048`, `temperature=0,2`:

| Metryka | Przebieg 1 | Przebieg 2 | Przebieg 3 | Przebieg 4 | Przebieg 5 |
| --- | --- | --- | --- | --- | --- |
| minimum | 3536 ms | 2791 ms | 3836 ms | 4151 ms | 3439 ms |
| mediana | 5009 ms | 3852 ms | 5198 ms | 4779 ms | 5268 ms |
| maksimum | 6636 ms | 5984 ms | 6244 ms | 5643 ms | 6783 ms |
| `POST /api/inference/test` | 558 ms | 558 ms | 391–445 ms | 391–445 ms | 814–1055 ms |
| `GET /api/inference/health` | 216–282 ms | 206 ms | 224–266 ms | 224–266 ms | 301–582 ms |

Pojedynczy projekt mieści się w 3,4–6,8 s. Przy ośmiu sprawach na ekranie i generowaniu
po kolei to 30–55 s — warto rozważyć generowanie równoległe albo strumieniowanie.

## 9. Jak odtworzyć

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

# ustalenia P11–P16 i znaczniki w trzech formatach eksportu
cd backend && .venv/bin/python /tmp/real_test_findings.py

# pełna ścieżka HTTP (43 asercje)
cd backend && .venv/bin/python /tmp/real_test_http.py
```

## 10. Stan po testach

- Sprawy: 10 demo + 3 utworzone przez test HTTP („Test nowej sprawy", numery
  `BKS.IV.1431.9xxx.2026`). Do usunięcia przez `scripts/demo.sh`.
- Dokumenty: 2 (`wniosek-01-wynagrodzenia.pdf`, `wniosek-02-najem-lokali.pdf`), zero duplikatów.
- Audyt: 69 wpisów.
- Projekty wygenerowane dla wszystkich spraw.
- Reset do stanu wyjściowego: `scripts/demo.sh`.

## 11. Wnioski

Piąty przebieg nie znalazł ani jednej regresji i ani jednego nowego ustalenia. Wszystkie
szesnaście ustaleń z czterech poprzednich przebiegów pozostaje zamkniętych, a liczby
testów rosną (584 backendu, 199 frontendu, 7 na żywym API, 43/43 asercji HTTP).

Największa zmiana od czwartego przebiegu nie dotyczy napraw, tylko zakresu: projekt nosi
nazwę Capricorn, sprawy mają numerację BKS, anonimizacja pokrywa pełną listę 28 kategorii
UMB, doszedł moduł przypomnień i dialog nowej sprawy. Wszystkie te elementy przeszły testy
bez zastrzeżeń.

Nowy szablon podstawy prawnej upraszcza obraz odnośników: zamiast ciągu trzynastu cyfr
przy jednym zdaniu są pojedyncze artykuły z własnymi odnośnikami. To skuteczniej rozwiązuje
P14 niż samo zwężanie do zakresów, które pozostaje jako zabezpieczenie.

P17 zostaje świadomie otwarta: edytor pokazuje źródło Markdownu, a nie wersję złożoną.
Formą złożoną jest panel cytowań i eksport, więc nie ma tu straty dla urzędnika.
