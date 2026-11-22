# Demo — scenariusz przejścia przez aplikację

Instrukcja dla osoby prowadzącej prezentację. Cała ścieżka mieści się w **8 minutach**.
Nie ma tu slajdów ani nagrania: pokazujesz działającą aplikację i mówisz, co widać na ekranie.

---

## 1. Przygotowanie (2 minuty przed wejściem)

```bash
cd <katalog projektu>
scripts/demo.sh
```

Skrypt zatrzymuje poprzednie uruchomienie, czyści `backend/data/` (baza i uploady),
ustawia `DEMO_TODAY=2026-03-16` i uruchamia backend oraz frontend, a na końcu
wypisuje adresy i listę „co pokazać”. Tryb modułów bierze z `backend/.env`
(domyślnie wszystkie osiem na `real`); `scripts/demo.sh --fake` wymusza atrapy,
gdy demo ma działać bez bazy i bez modeli.

| Co | Adres |
| --- | --- |
| Interfejs | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8000/api |
| Dokumentacja API | http://127.0.0.1:8000/api/docs |

**Kontrola przed wejściem:**

1. Otwórz http://127.0.0.1:5173 — po lewej jest menu z 8 pozycjami, na górze „Pulpit”.
2. Wejdź w „Kalendarz terminów” — tabela ma **10 wniosków**.
3. Przygotuj w menedżerze plików `fixtures/documents/wniosek-01-wynagrodzenia.pdf`
   (będzie potrzebny w kroku 3).
4. Powiększenie przeglądarki 100%, szerokie okno — tabele mają dużo kolumn.

Tryb `fake` oznacza: **żadnych modeli językowych i żadnej sieci**. Wszystkie dane
pochodzą z `fixtures/`, a odpowiedzi są deterministyczne — demo zawsze wygląda tak samo.

---

## 2. Dane, które będą potrzebne (ściąga)

### Wnioski w kalendarzu — `fixtures/cases/cases.json`

| Numer sprawy | Przedmiot | Termin | Stan | Pilność na 16.03.2026 |
| --- | --- | --- | --- | --- |
| BKS.IV.1431.1.2026 | Wynagrodzenia pracowników Urzędu Miasta w 2025 r. | 06.03.2026 | Zapytania wysłane | **Po terminie** (−10 dni) |
| BKS.IV.1431.2.2026 | Kopie umów najmu lokali komunalnych przy ul. Dworcowej | 16.03.2026 | Kwerenda | Termin dziś |
| BKS.IV.1431.3.2026 | Wydatki na promocję miasta w mediach społecznościowych | 17.03.2026 | Przygotowana odpowiedź | Termin jutro |
| BKS.IV.1431.4.2026 | Protokoły z kontroli Straży Miejskiej w 2025 r. | 19.03.2026 | Zapytania wysłane | Termin wkrótce |
| BKS.IV.1431.5.2026 | Harmonogram remontów dróg gminnych na 2026 r. | 23.03.2026 | Nowy | W terminie |
| BKS.IV.1431.6.2026 | Decyzje o warunkach zabudowy wydane w IV kwartale 2025 r. | 24.03.2026 | Nowy | W terminie |
| BKS.IV.1431.7.2026 | Umowy z podmiotami zewnętrznymi na utrzymanie zieleni | 24.02.2026 | Odpowiedź wysłana | Zamknięta |
| BKS.IV.1431.8.2026 | Zatrudnienie w jednostkach organizacyjnych miasta | 01.03.2026 | Odpowiedź wysłana | Zamknięta |
| BKS.IV.1431.9.2026 | Dostęp do nagrań z monitoringu miejskiego | 25.03.2026 | Nowy | W terminie |
| BKS.IV.1431.10.2026 | Koszty utrzymania Biura Rady Miasta w 2025 r. | 26.03.2026 | Zapytania wysłane | W terminie |

**Bohaterka demo: BKS.IV.1431.1.2026** — po terminie, z zapytaniami już wysłanymi.

### Komórki organizacyjne — `fixtures/departments.json` (26 pozycji)

| Id | Nazwa | Kiedy się przydaje |
| --- | --- | --- |
| `wok` | Wydział Organizacji i Kadr | wynagrodzenia, zatrudnienie, kadry |
| `wgn` | Wydział Gospodarki Nieruchomościami | najem lokali komunalnych, czynsz |
| `wpm` | Wydział Promocji Miasta | promocja, kampanie, media społecznościowe |
| `sm` | Straż Miejska | kontrole, interwencje, monitoring |
| `zdm` | Zarząd Dróg Miejskich i Komunikacji Publicznej | drogi, remonty, mosty |
| `waiu` | Wydział Architektury i Urbanistyki | warunki zabudowy, plany miejscowe |
| `brm` | Biuro Rady Miasta | Rada Miasta, sesje, diety |
| `bks` | Biuro Komunikacji Społecznej | informacja publiczna, wnioski UDIP |

### Dokumenty — `fixtures/documents/`

| Plik | Co to jest |
| --- | --- |
| `wniosek-01-wynagrodzenia.pdf` | wniosek o wynagrodzenia (Jan Kowalski, media) — **wgrany w demo** |
| `wniosek-02-najem-lokali.pdf` | wniosek redakcji o umowy najmu |
| `wniosek-03-wycinka-drzew.docx` | wniosek stowarzyszenia o wycinkę drzew |
| `odpowiedz-wydzialu-01.pdf` | odpowiedź Wydziału Organizacji i Kadr |
| `odpowiedz-wydzialu-02.docx` | odpowiedź Wydziału Gospodarki Nieruchomościami |

### Archiwum — `fixtures/archive/archive.json` (49 spraw)

Najlepsze trafienie dla wniosku o wynagrodzenia: **`a0001`, BKS.IV.1431.87.2025,
„Wynagrodzenia pracowników Urzędu Miasta w 2024 r.”** (ocena ok. 0,63).

### Anonimizacja — `fixtures/anonymization/labeled.jsonl` (20 rekordów)

Tekst z przycisku „Wstaw przykład” zawiera: Jan Kowalski, PESEL 85041212345,
adres `ul. Gdańska 42/7, 85-005 Bydgoszcz`, telefon `+48 601 234 567`,
e-mail `jan.kowalski@example.com`, Anna Nowak.

---

## 3. Przebieg — 8 minut

### 0:00–0:45 — Pulpit

**Co kliknąć:** nic — aplikacja otwiera „Pulpit”.

**Co powinno być widać:**

- cztery kafelki: **Po terminie 1**, **Termin dziś 1**, **W najbliższych dniach 2**,
  **Zamknięte 2**;
- wykres „Rozkład pilności” z paskami w kolorach pilności;
- „Najbliższe terminy” — na górze **BKS.IV.1431.1.2026** z czerwoną plakietką „Po terminie”;
- „Zamknięte w ostatnich 30 dniach” — dwie sprawy z datą odpowiedzi.

**Co powiedzieć:** „Urzędnik zaczyna dzień od jednego ekranu: co jest po terminie,
co ma termin dziś i co zamyka się w najbliższych dniach. Kolor wynika z terminu
ustawowego — 14 dni od wpływu wniosku.”

### 0:45–2:00 — Kalendarz terminów

**Co kliknąć:**

1. „Kalendarz terminów” w menu.
2. Kliknij wiersz **BKS.IV.1431.1.2026**.
3. W panelu po prawej wskaż sekcję „Zmiana stanu”.
4. (opcjonalnie, 10 s) Kliknij „Cofnij do: Nowy” bez notatki — pod polem pojawi się
   „Cofnięcie stanu wymaga notatki.” To samo żądanie z pominięciem interfejsu
   kończy się błędem **409**.
5. Zamknij panel, ustaw filtr „Stan sprawy” = „Nowy”, potem przełącz widok na „Miesiąc”.

**Co powinno być widać:**

- tabela 10 wniosków posortowana terminem rosnąco, kolumny: Numer sprawy, Przedmiot
  wniosku, Wpływ, Termin, Dni, Pilność, Stan, Prowadzący;
- panel „Szczegóły wniosku”: plakietki „Zapytania wysłane” i „Po terminie”,
  podpis „10 dni temu”, pola: liczba porządkowa 1, rok 2026, wpływ 20 lutego 2026,
  termin 6 marca 2026, dni do terminu **−10**, prowadzący **JK**, wnioskodawca **Media**;
- „Historia zmian” z wpisem **„Utworzenie sprawy”** (data wpływu, autor „urzędnik”);
- „Zmiana stanu” z trzema przyciskami: „Przejdź do: Kwerenda”,
  „Pomiń kwerendę: Przygotowana odpowiedź” i „Cofnij do: Nowy” oraz polem
  „Notatka” (cofnięcie bez notatki jest zablokowane);
- po filtrze „Nowy” zostają 3 wnioski (5, 6 i 9);
- widok „Miesiąc” pokazuje marzec 2026 z kolorowymi dniami i liczbą wniosków na dzień.

**Co powiedzieć:** „To jest rejestr spraw z terminami. Dni i pilność nie są wpisane
w bazę — liczy je serwer przy każdym odczycie, więc nigdy nie rozjadą się z kalendarzem.
Stan sprawy zmienia się przyciskami, a cofnięcie wymaga notatki — to ślad w historii.”

### 2:00–3:00 — Dokumenty

**Co kliknąć:**

1. „Dokumenty” w menu.
2. W karcie „Wgraj dokument” wybierz `fixtures/documents/wniosek-01-wynagrodzenia.pdf`.
3. „Rodzaj dokumentu” = **Wniosek**, „Przypisz do sprawy” = **BKS.IV.1431.1.2026**.
4. Kliknij „Wgraj i przetwórz”.
5. Po komunikacie kliknij ikonę oka przy nowym wierszu.

**Co powinno być widać:**

- komunikat „Dokument wgrany i zaindeksowany” z liczbą fragmentów;
- nowy wiersz w „Baza wiedzy”: nazwa pliku, rodzaj „Wniosek”, plakietka
  **Zaindeksowany**, liczba fragmentów, rozmiar;
- podgląd z pełnym tekstem wniosku — z polskimi znakami („WNIOSEK O UDOSTĘPNIENIE
  INFORMACJI PUBLICZNEJ”, „Gdańska”, „Wysokości wynagrodzeń”).

**Co powiedzieć:** „Wgrany PDF jest odczytywany, dzielony na fragmenty z numerem
strony i zapisywany w bazie wiedzy. Numery stron są obowiązkowe, bo generator
odpowiedzi cytuje źródła — bez offsetu nie byłoby czego pokazać urzędnikowi.”

### 3:00–4:00 — Archiwum spraw

**Co kliknąć:**

1. „Archiwum spraw” w menu.
2. W polu „Treść wniosku” wklej: `Wynagrodzenia pracowników Urzędu Miasta na stanowiskach kierowniczych`
3. Kliknij „Szukaj w archiwum”.
4. Przy pierwszym wyniku kliknij „Szczegóły sprawy”.

**Co powinno być widać:**

- lista „Podobne sprawy” (5 pozycji), pierwsza: **a0001 / BKS.IV.1431.87.2025 /
  „Wynagrodzenia pracowników Urzędu Miasta w 2024 r.”** z oceną **0,63** i paskiem;
- przy wyniku: „Dopasowane terminy” (wynagrodzenia, pracowników, urzędu…),
  „Fragment wniosku” i „Fragment odpowiedzi”;
- w szczegółach: pełna treść wniosku i odpowiedzi archiwalnej oraz komórki organizacyjne.

**Co powiedzieć:** „Zanim urzędnik napisze odpowiedź, widzi, jak urząd rozstrzygał
podobne sprawy. Archiwum ma 49 zakończonych spraw; ocena podobieństwa jest liczona
na miejscu, bez wysyłania danych na zewnątrz.”

### 4:00–5:15 — Routing wydziałowy

**Co kliknąć:**

1. „Routing wydziałowy” w menu.
2. „Sprawa z kalendarza” = **BKS.IV.1431.1.2026** — pole „Treść do analizy” wypełni się
   przedmiotem wniosku, a sugestie pojawią się same.
3. Zaznacz **Wydział Organizacji i Kadr**.
4. Spójrz na kartę „Podgląd zapytania”.

**Co powinno być widać:**

- „Sugestie komórek”: **wok — Wydział Organizacji i Kadr 95%**, wadm 48%, wgk 33%,
  przy każdej dopasowane terminy i pasek pewności;
- „Podgląd zapytania”: nagłówek „Bydgoszcz, 16 marca 2026 r.”, **„Znak sprawy:
  BKS.IV.1431.1.2026”**, „Data wpływu wniosku: 20 lutego 2026 r.”,
  **„Termin odpowiedzi: 6 marca 2026 r.”**, lista adresatów, „Dotyczy: Wynagrodzenia
  pracowników Urzędu Miasta w 2025 r.”, treść prośby o materiały;
- przyciski „Kopiuj treść”, „Pobierz .txt”, „Przejdź do odpowiedzi”.

**Co powiedzieć:** „Aplikacja wskazuje komórki właściwe dla sprawy i składa zapytanie
z danych sprawy — numer, data wpływu, termin. Nic nie jest wysyłane: to projekt,
który urzędnik wysyła swoim kanałem.”

### 5:15–7:00 — Generator odpowiedzi

**Co kliknąć:**

1. „Przejdź do odpowiedzi” pod podglądem zapytania (albo „Generator odpowiedzi”
   i wybór sprawy BKS.IV.1431.1.2026).
2. Kliknij „Wygeneruj projekt”.
3. Dopisz w edytorze zdanie, np. `Uzupełniono po konsultacji z Wydziałem Organizacji i Kadr.`
   i odczekaj ~2 sekundy.
4. Kliknij „DOCX” w karcie „Eksport”.

**Co powinno być widać:**

- tytuł „Projekt odpowiedzi na wniosek” i treść z sekcjami: „Podstawa prawna”,
  „Odpowiedź”, „Rozstrzygnięcia w sprawach zbliżonych”, „Pouczenie”;
- panel „Cytowania” z pozycją „Przepis — art. 13 ust. 1 i 2 ustawy o dostępie
  do informacji publicznej”; kliknięcie cytowania podświetla miejsce w treści;
- „Twierdzenia bez źródła” — puste (każde zdanie ma odnośnik);
- po edycji wskaźnik zapisu zmienia się z „Niezapisane zmiany” na **„Zapisano”**;
- po kliknięciu DOCX przeglądarka pobiera plik `odpowiedz-*.docx`;
- w karcie „Eksport” są też PDF, Markdown i przełącznik „Wersja zanonimizowana”.

**Co powiedzieć:** „Projekt powstaje z szablonu, bo w trybie demo nie ma modelu
językowego — ale struktura jest ta sama co z modelem: każde twierdzenie ma odnośnik
do źródła, a zdania bez źródła trafiają do osobnej listy, nie znikają po cichu.
W trybie realnym treść pisze model, a cytowania pochodzą z przepisów, archiwum
i dokumentów sprawy.”

### 7:00–7:40 — Anonimizacja

**Co kliknąć:**

1. „Anonimizacja” w menu.
2. Kliknij „Wstaw przykład”.
3. Kliknij „Wykryj dane osobowe”.
4. Kliknij „Zastosuj anonimizację”.

**Co powinno być widać:**

- „Wykryte fragmenty”: **6 pozycji** z kategoriami — Imię i nazwisko (Jan Kowalski),
  PESEL, Adres, Telefon, E-mail, Imię i nazwisko (Anna Nowak) — z pewnością i źródłem;
- „Podgląd po anonimizacji”: „Wnioskodawca **[USUNIĘTO]**, PESEL **[USUNIĘTO]**,
  zamieszkały przy **[USUNIĘTO]**, prosi o udostępnienie informacji o wydatkach
  na promocję. Kontakt: **[USUNIĘTO]**, **[USUNIĘTO]**. Sprawę prowadzi **[USUNIĘTO]**.”;
- „Metryki jakości” z precyzją, pełnością i F1 oraz rozbiciem na kategorie.

**Co powiedzieć:** „Zanim odpowiedź trafi do publikacji, dane osobowe są usuwane.
Fragmenty można odznaczyć albo dodać ręcznie, jeśli detektor coś pominie —
decyzja zawsze należy do urzędnika.”

### 7:40–8:00 — Ustawienia i zamknięcie

**Co kliknąć:** „Ustawienia” w menu.

**Co powinno być widać:**

- „Środowisko” — wersja, tryb offline, liczba modułów na atrapie (8 z 8);
- „Warstwa modeli” — provider **Atrapa (bez modelu)**, status **Działa**;
- „Tryb modułów” — tabela 8 modułów: nazwa, plakietka **Atrapa** i jedno zdanie
  „co to oznacza dla użytkownika” (np. przy kalendarzu: „Wnioski demonstracyjne
  z plików przykładowych; zmiany statusu nie trafiają do bazy urzędu.”);
- ramka „Co to znaczy w praktyce” — atrapa nie wysyła niczego na zewnątrz
  i nie potrzebuje modelu; tryb zmienia się zmienną `MODULE_MODE_<NAZWA>`.

**Co powiedzieć:** „Każdy moduł włącza się niezależnie: `MODULE_MODE_<NAZWA>=real`.
Demo działa w całości na atrapach, bez modeli i bez sieci — a ten sam przepływ
przechodzi test end-to-end na implementacjach realnych.”

---

## 3a. Jeśli zostanie czas — cztery rzeczy warte pokazania

Nie wchodzą do ośmiu minut; pokazuj je tylko, gdy jury dopytuje o „uczenie się”
albo o automatyzację.

### Dzwonek z przypomnieniami

W górnym pasku, obok przełącznika motywu, jest dzwonek z liczbą **3**.
Po kliknięciu lista: `BKS.IV.1431.1.2026` („Termin odpowiedzi minął 10 dni temu”),
`BKS.IV.1431.2.2026` („mija dziś”), `BKS.IV.1431.3.2026` („mija jutro”).
Klik w pozycję otwiera kartę sprawy w kalendarzu.

**Co powiedzieć:** „Lista liczy się przy odczycie, z tych samych pól, co kalendarz —
nie ma joba w tle, który mógłby się rozjechać z danymi.”

### Przedłużenie terminu w kwerendzie

W kalendarzu otwórz `BKS.IV.1431.1.2026` (stan „Zapytania wysłane”). W karcie sprawy
pojawi się pole **„Przedłużenie terminu (dni)”**. Wpisz `14` i kliknij
**„Przejdź do: Kwerenda”**. Termin zmieni się z 06.03.2026 na **20.03.2026**,
a pod polem pojawi się „Termin przedłużono łącznie o 14 dni”.

**Co powiedzieć:** „Kwerenda to nie tylko plakietka — termin faktycznie się
przesuwa, a liczba dni jest zapisana na sprawie i widoczna w historii.”

### Archiwum rośnie wraz z pracą urzędu

1. W kalendarzu zamknij dowolną sprawę do stanu **„Odpowiedź wysłana”**.
2. Wejdź w **„Archiwum spraw”** i wpisz temat tej sprawy.
3. Na czele wyników pojawi się ona z identyfikatorem `n0001` (nowe sprawy mają
   prefiks `n`, sprawy z materiałów — `a`).

**Co powiedzieć:** „To jest odpowiedź na wymaganie uczenia się na wprowadzanych
danych: zamknięta sprawa zostaje w archiwum razem z odpowiedzią, więc przy
kolejnym podobnym wniosku urzędnik widzi własne wcześniejsze rozstrzygnięcie.”

### Wgranie ustawy do podstawy prawnej

1. **„Dokumenty”** → wgraj plik tekstowy z treścią ustawy, rodzaj **„Ustawa”**.
2. **„Generator odpowiedzi”** → wygeneruj projekt.
3. W sekcji „Podstawa prawna” pod dotychczasowym art. 13 pojawią się artykuły
   wgranej ustawy z odnośnikami, a w panelu cytowań — pozycje z jej tytułem.

Jeśli wgrany akt ma tytuł taki sam jak plik z `fixtures/statutes/`, przykrywa go
w całości — tak działa aktualizacja ustawy.

---

## 4. Jeśli ktoś zapyta o tryb realny

- Wszystkie moduły mają dwie implementacje: `fake` (deterministyczna atrapa z `fixtures/`)
  i `real` (SQLite, PDF/DOCX, wyszukiwanie hybrydowe, reguły anonimizacji).
- Domyślnie działa `real` — `MODULE_MODE_DEFAULT=real` w `backend/.env`. Pojedynczy
  moduł cofniesz do atrapy, np. `MODULE_MODE_ARCHIVE=fake`; całość wymusi
  `scripts/demo.sh --fake`.
- Wyjątek: `MODULE_MODE_INFERENCE_EMBEDDING=fake`, bo `LocalEmbedding` mówi
  protokołem `/embeddings`, a Mistral nie serwuje modelu `BAAI/bge-m3`. Archiwum
  działa bez wektorów — zostaje BM25 i pokrycie leksykalne.
- Dowód, że ścieżka działa w trybie realnym: `backend/tests/test_e2e_flow.py` —
  jeden test przechodzi 11 kroków przez HTTP na wszystkich modułach `real`
  (wgranie PDF → kalendarz → archiwum → routing → zapytanie → projekt → zapis →
  eksport DOCX/PDF → anonimizacja → zmiana stanu → dziennik audytu).
- Uruchomienie testu:

  ```bash
  cd backend && .venv/bin/python -m pytest tests/test_e2e_flow.py -q
  ```

---

## 5. Plan B

| Problem | Co zrobić |
| --- | --- |
| Strona się nie otwiera | `scripts/stop-local.sh`, potem `scripts/demo.sh` jeszcze raz |
| „Nie udało się pobrać wniosków” | backend nie wstał — zajrzyj w `.run/backend.log` |
| Port zajęty | `BACKEND_PORT=8010 FRONTEND_PORT=5180 scripts/demo.sh` |
| Wgranie pliku nie działa | sprawdź, czy wybrano plik z `fixtures/documents/` (PDF albo DOCX) |
| Chcesz zacząć demo od nowa | `scripts/demo.sh` (czyści dane) albo `scripts/demo.sh --no-reset` (zostawia) |

Demo nie potrzebuje internetu ani modeli. Jeśli w sieci nie ma dostępu do niczego —
demo nadal działa.

---

## 6. Zatrzymanie

```bash
scripts/stop-local.sh
```

Logi: `.run/backend.log`, `.run/frontend.log`.
