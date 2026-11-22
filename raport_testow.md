# Raport z testów — tryb realny (8/8 modułów) z modelem Mistral

Data pierwszego przebiegu: 22 listopada 2026
Data drugiego przebiegu: 22 listopada 2026, po commicie `5356e68`
Data trzeciego przebiegu: 22 listopada 2026, po commicie `cbf7ee1`
Środowisko: lokalne, backend `http://127.0.0.1:8000`, frontend `http://127.0.0.1:5173`
Zakres: wszystkie osiem modułów na adapterach `real`, generator odpowiedzi na żywym
Mistralu (`mistral-small-latest`). Nie atrapy.

---

## 0. Podsumowanie trzeciego przebiegu

Pięć ustaleń z drugiego raportu (P11–P15) jest naprawionych i zweryfikowanych na żywym
modelu. Wszystkie pomiary, które wcześniej pokazywały problem, są teraz zerowe:

| Miara | Przebieg 2 | Przebieg 3 |
| --- | --- | --- |
| Fałszywe alarmy „Dz. U." w `unsupported` | 6/10 (60%) | **0/10 (0%)** |
| Klastry ≥3 odnośników pod rząd | 9/10 (90%) | **0/10 (0%)** |
| Daty ISO w treści pisma | 1/10 (10%) | **0/10 (0%)** |
| Nazwa pliku eksportu | `odpowiedz-c0000001-projekt.docx` | **`odpowiedz-UDIP.1435.7.2026-projekt.docx`** |
| Duplikaty dokumentów w bazie | 3 pary | **0 par** |
| Degradacja do szablonu | 0/20 | **0/20** |
| Przeciek definicji przypisów | 0/20 | **0/20** |
| Testy backendu | 512 (+1 pominięty) | **551 (+1 pominięty)** |
| Testy frontendu | 195 | **199** |
| Test wołający prawdziwe API | 7 w 5,3 s | **7 w 3,58 s** |

Trzeci przebieg nie odsłonił żadnej regresji w P1–P10. Znalazł dwie obserwacje
o niskiej wadze, opisane w sekcji 6.

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
4. **Interfejs w przeglądarce** — te same ekrany na realnym backendzie, w tym kliknięcia
   w panelu cytowań.

Pomiary jakości generatora: 5 spraw × 4 generacje = 20 prób, każda z inspekcją surowej
odpowiedzi modelu przed i po normalizacji. Ten sam skrypt we wszystkich trzech przebiegach.

## 3. Wyniki pozytywne

| Obszar | Wynik |
| --- | --- |
| Wgranie PDF / DOCX / TXT | 19–102 ms, status `indexed`, polskie znaki zachowane, fragmenty policzone |
| Odczyt dokumentu | 591–3250 znaków, 1–5 fragmentów, `page_count` poprawny |
| Kalendarz (SQLite) | 10 spraw, `days_remaining` i `urgency` liczone z `DEMO_TODAY` |
| Archiwum | 5 wyników, oceny 0,866 → 0,278 (malejąco), 7–22 ms |
| Routing | 26 komórek, WGN 98% dla najmu lokali, wyjaśnienie pokrycia („3 z 6 istotnych słów") |
| Zapytanie do komórek | numer sprawy i termin obecne w treści |
| Generator (Mistral) | 3,8–6,2 s na projekt, 5–14 cytowań, zero wiszących odnośników |
| Zapis projektu | nowa treść i kolejna wersja |
| Eksport DOCX / PDF / MD | 200, poprawne nagłówki plików (`PK`, `%PDF`), `X-Redactions` |
| Anonimizacja | 6 kategorii, precyzja 1,00, pełność 1,00, F1 1,00 |
| Przejścia stanów | 7/7 scenariuszy, pełny łańcuch `nowy → zapytania_wyslane → kwerenda → przygotowana_odpowiedz → odpowiedz_wyslana` |
| Kwerenda | `kwerenda_days=14` przesuwa termin (06.03 → 20.03), `response_date` ustawiane przy zamknięciu |
| Cofnięcie stanu bez notatki | odrzucone, HTTP 409, komunikat „Cofnięcie stanu wymaga notatki." |
| Cofnięcie stanu z notatką | przechodzi, HTTP 200 |
| Historia sprawy | 5 wpisów, pierwszy `created` z datą wpływu `2026-02-20T08:00:00` |
| Audyt | 100 wpisów, akcje: `case.transitioned`, `document.uploaded`, `document.deleted`, `draft.exported`, `draft.generated`, `draft.saved` |
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

## 4. Ustalenia z pierwszego przebiegu (P1–P10) — nadal naprawione

| # | Ustalenie | Status | Dowód z trzeciego przebiegu |
| --- | --- | --- | --- |
| P1 | 20% projektów schodziło do szablonu przez `[n]` zamiast `[^n]` | **naprawione** | 20/20 projektów z modelu, `degraded=False` w każdym |
| P2 | Szablon cytował każdy artykuł wgranej ustawy | **naprawione** | 0 zdań „Podstawę prawną stanowi", 2096 znaków zamiast 3808 |
| P3 | Definicje przypisów przeciekały do treści pisma | **naprawione** | 0/20 prób z blokiem `[^n]:` w treści |
| P4 | Wgranie i eksport w UI zwracały 401 | **naprawione** | toast „Dokument wgrany i zaindeksowany", toast „Plik gotowy" |
| P5 | Notatka o degradacji trafiała do panelu „Twierdzenia bez źródła" | **naprawione** | osobny kafelek „Projekt z szablonu", panel nieobecny |
| P6 | Ustawienia opisywały moduły niezgodnie z kodem | **naprawione** | routing „bez udziału modelu językowego", spaCy „opcjonalny", Mistral na liście dostawców |
| P7 | Żaden test nie wołał modelu | **naprawione** | `test_drafting_mistral_contract.py`, 7 testów na żywo w 3,58 s |
| P8 | Ponowne wgranie tworzyło duplikat | **naprawione** | ten sam plik dwa razy → ten sam `id`; inna nazwa, ta sama treść → ten sam `id` |
| P9 | Historia w trybie realnym bez wpisu o utworzeniu | **naprawione** | 5 wpisów, pierwszy `created` z datą wpływu `2026-02-20T08:00:00` |
| P10 | Znaczniki czasu z realnego zegara | **naprawione** | historia i audyt z datą `2026-03-16`, godzina z realnego zegara |

## 5. Ustalenia z drugiego przebiegu (P11–P15) — naprawione

| # | Ustalenie | Status | Dowód z trzeciego przebiegu |
| --- | --- | --- | --- |
| P11 | Skrót „Dz. U." rozbijał zdania i tworzył fałszywe „twierdzenia bez źródła" | **naprawione** | 0/10 fałszywych alarmów (było 6/10); `_sentences` 5/5 próbek bez podziału |
| P12 | Nazwa pliku eksportu to fragment UUID | **naprawione** | `odpowiedz-UDIP.1435.7.2026-projekt.docx` |
| P13 | Duplikaty sprzed naprawy zostawały w bazie | **naprawione** | 0 par duplikatów po `backend/scripts/dedup_documents.py` |
| P14 | Podstawa prawna zbierała do 13 odnośników pod rząd | **naprawione** | 0/10 klastrów ≥3 (było 9/10); przebiegi zwężone do `[^2]–[^13]` |
| P15 | Sporadyczna data ISO w treści pisma | **naprawione** | 0/10 projektów z datą ISO (było 1/10) |

### P11 — podział zdań na skrótach

`_sentences` nie dzieli już na „Dz. U.", „art.", „ust.", „poz.", „nr", „r." ani „t.j.".
Pięć próbek z pełną podstawą prawną przechodzi bez rozcięcia:

```
wejście: Niniejsza odpowiedź … (Dz. U. z 2023 r. poz. 1479) [^1].
  → [ 94] Niniejsza odpowiedź … (Dz. U. z 2023 r. poz. 1479) [^1].
find_unsupported → brak alarmu
```

Pomiar na 10 projektach: `unsupported` zawiera teraz wyłącznie prawdziwe twierdzenia
bez źródła, np. „W związku z powyższym informuje się, że wnioskowane umowy … nie zostały
dotychczas opublikowane w BIP". To zdanie istotnie nie ma pokrycia w źródłach — panel
działa zgodnie z przeznaczeniem.

### P12 — nazwa pliku eksportu

```
Content-Disposition: attachment; filename="odpowiedz-UDIP.1435.7.2026-projekt.docx"
Content-Disposition: attachment; filename="odpowiedz-UDIP.1435.2.2026-projekt.pdf"
Content-Disposition: attachment; filename="odpowiedz-UDIP.1435.2.2026-projekt.md"
```

### P13 — sprzątanie duplikatów

Skrypt `backend/scripts/dedup_documents.py` uruchomiony na bazie testowej. Przed: trzy
pary (`wniosek-01-wynagrodzenia`, `odpowiedz-wydzialu-01`, `wniosek-03-wycinka-drzew`).
Po: zero par, sześć dokumentów w bazie.

### P14 — zwężanie przebiegów odnośników

`collapse_ref_runs` zamienia ciąg trzech i więcej odnośników na zakres. W treści projektu
zostaje `[^2]–[^13]` zamiast trzynastu cyfr. Panel cytowań ma komplet czternastu pozycji
(1–14), więc zakres nie gubi odnośników — zwężenie jest wyłącznie typograficzne.

Kliknięcie cytowania ze środka zakresu działa: wybór numeru 5 w panelu zaznacza w edytorze
cały fragment `[^2]–[^13]` i podświetla pozycję 5 jako aktywną. Realizuje to
[`markerRangeFor`](frontend/src/features/drafting/markdown.ts:277) wołane z
[`Editor.tsx:134`](frontend/src/features/drafting/Editor.tsx:134) jako ścieżka zapasowa,
gdy odnośnik nie ma własnego znacznika. Zrzut ekranu:
`/home/trollyou/.t3/userdata/browser-artifacts/browser-screenshot-127-0-0-1-mwr9kh3v-43eed631.png`

### P15 — daty w treści

Zero wystąpień `RRRR-MM-DD` w dziesięciu projektach. Daty w treści mają formę
„2 marca 2026 r." i „16 marca 2026 r.".

## 6. Nowe obserwacje z trzeciego przebiegu

### P16 — eksport Markdown zostawia surowe znaczniki `[^n]` (niski)

DOCX i PDF zamieniają `[^n]` na `[n]` (w DOCX w indeksie górnym), a Markdown zostawia
postać źródłową:

| Format | Fragment podstawy prawnej |
| --- | --- |
| DOCX | `… o dostępie do informacji publicznej [2]–[13], a także … [1].` |
| PDF | `… o dostępie do informacji publicznej [2]–[13] oraz … [1].` |
| MD | `… o dostępie do informacji publicznej [art. 1 ust. 1, …][^2]–[^12] oraz … [^1].` |

[`render_markdown`](backend/app/modules/drafting/export.py:194) nie woła `plain_text`,
więc caret zostaje. Moduł opisuje eksport MD jako „wersję roboczą do wklejenia dalej",
więc nie jest to błąd blokujący — ale przy wklejeniu do pisma trzeba by te znaczniki
usunąć ręcznie. Poprawka to jedno wywołanie `plain_text` w `render_markdown`.

### P17 — zakres odnośników widoczny w edytorze jako surowy tekst (informacyjne)

Edytor pokazuje `[^2]–[^13]` dosłownie, bo prezentuje źródło Markdownu, a nie wersję
złożoną. To istniejąca konwencja edytora z pierwszego przebiegu, nie regresja — panel
cytowań obok jest formą złożoną. Warto rozważyć, czy urzędnik nie powinien widzieć
w treści `[2]–[13]` zamiast `[^2]–[^13]`, ale to zmiana projektowa, nie usterka.

## 7. Latencja modelu

20 generacji, `mistral-small-latest`, `max_tokens=2048`, `temperature=0,2`:

| Metryka | Przebieg 1 | Przebieg 2 | Przebieg 3 |
| --- | --- | --- | --- |
| minimum | 3536 ms | 2791 ms | 3836 ms |
| mediana | 5009 ms | 3852 ms | 5198 ms |
| maksimum | 6636 ms | 5984 ms | 6244 ms |
| `POST /api/inference/test` | 558 ms | 558 ms | 391–445 ms |
| `GET /api/inference/health` | 216–282 ms | 206 ms | 224–266 ms |

Pojedynczy projekt mieści się w 3,8–6,2 s. Przy ośmiu sprawach na ekranie i generowaniu
po kolei to 30–50 s — warto rozważyć generowanie równoległe albo strumieniowanie.

## 8. Jak odtworzyć

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

## 9. Stan po testach

- Dokumenty w bazie: 6 pozycji, zero duplikatów.
- Projekty wygenerowane dla wszystkich spraw poza zamkniętymi.
- Zamknięte: `UDIP.1435.5.2026`, `UDIP.1435.6.2026`, `UDIP.1435.9.2026` — weszły do archiwum jako `n0001`–`n0003`.
- Audyt: 100 wpisów.
- Reset do stanu wyjściowego: `scripts/demo.sh`.

## 10. Wnioski

Wszystkie piętnaście ustaleń z trzech przebiegów jest zamkniętych. Trzeci przebieg nie
znalazł regresji: każdy pomiar, który w drugim przebiegu pokazywał problem, jest teraz
zerowy, a liczby testów rosną (551 backendu, 199 frontendu, 7 na żywym API).

Najważniejsza naprawa to P11. Fałszywy alarm o twierdzeniu bez źródła jest groźniejszy niż
brak alarmu — urzędnik, który raz zobaczy ostrzeżenie przy poprawnie uzasadnionym zdaniu,
przestanie czytać panel kontroli. Zejście z 60% do zera przywraca temu panelowi wiarygodność.

Pozostają dwie obserwacje kosmetyczne: P16 (Markdown zostawia `[^n]`, DOCX i PDF nie)
i P17 (edytor pokazuje surowy zakres). Żadna nie blokuje demonstracji.
