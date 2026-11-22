# Model domenowy — słownik i reguły

**ZAMROŻONE po Fali 0.** Zmiana wymaga PR-a `contract: <opis>`.

---

## 1. Wniosek (Case)

Rekord kalendarza. Pola odpowiadają wymaganiu W3 z zadania.

| Pole | Typ | Wymaganie | Uwagi |
|---|---|---|---|
| `id` | uuid | — | klucz |
| `case_number` | string | W3 „nr wniosku" | format `BKS.<komórka>.<nr>.<lp>.<rok>` |
| `ordinal` | int | W3 „liczba porządkowa" | nadawana sekwencyjnie w obrębie roku |
| `subject` | string | W3 „okienko na skrócony opis tematu" | ≤ 200 znaków |
| `applicant` | string | — | wnioskodawca w postaci z pisma; puste = nieustalony |
| `inflow_date` | date | W3 „data wpływu" | |
| `deadline` | date | W3 „termin odpowiedzi" | wyliczany lub nadpisany ręcznie |
| `deadline_note` | string | — | termin opisowy z rejestru UMB, np. `19.08.2026/18.09.2026 - doprecyzowanie wniosku`; ≤ 200 znaków, nie wpływa na `days_remaining` |
| `response_date` | date \| null | W3 „data udzielenia odpowiedzi" | |
| `handler_initials` | string | W3 „inicjały osoby obsługującej" | 2–4 znaki |
| `status` | enum | W12 | patrz §2 |
| `year` | int | W3 „wybór roku" | `inflow_date.year` |
| `days_remaining` | int | W1 „ilość dni na wysłanie" | wyliczane, nie przechowywane |
| `urgency` | enum | W2 | wyliczane, patrz §3 |
| `applicant_type` | enum | — | osoba_fizyczna / organizacja / media / inne |
| `source_document_id` | uuid \| null | W5 | wgrany plik wniosku |

**Pola wyliczane** (`days_remaining`, `urgency`, `year`) nie są przechowywane w bazie — liczone w serwisie przy każdym odczycie. Dzięki temu nie rozjeżdżają się z upływem czasu.

---

## 2. Maszyna stanów (W12)

Kody a–e z zadania mapują się na nazwy semantyczne:

| Kod | Wartość | Etykieta PL | Znaczenie |
|---|---|---|---|
| a | `nowy` | Brak działań | wniosek wpłynął, nic nie wysłano |
| b | `zapytania_wyslane` | Zapytania wysłane do wydziałów | prośby rozesłane |
| c | `kwerenda` | Kwerenda | wydział potrzebuje dodatkowego czasu |
| d | `przygotowana_odpowiedz` | Przygotowana odpowiedź | projekt gotowy, czeka na akceptację |
| e | `odpowiedz_wyslana` | Odpowiedź wysłana | sprawa zamknięta |

### Dozwolone przejścia

```
nowy ──► zapytania_wyslane ──► kwerenda ──► przygotowana_odpowiedz ──► odpowiedz_wyslana
  │              │                  │                  │
  │              └──────────────────┴──────────────────┘
  │                          (cofnięcie o krok)
  └──────────────────────────────────────────────────► przygotowana_odpowiedz
```

Reguły:

1. Naprzód: tylko o jeden krok (`nowy → zapytania_wyslane → kwerenda → przygotowana_odpowiedz → odpowiedz_wyslana`).
2. `kwerenda` jest opcjonalna — można pominąć (`zapytania_wyslane → przygotowana_odpowiedz`).
3. Cofnięcie: dozwolone o jeden krok, wymaga `note` w `TransitionRequest`.
4. `odpowiedz_wyslana` jest stanem końcowym — cofnięcie tylko z `note`.
5. Każde przejście zapisuje `HistoryEntry` i `AuditEntry`.
6. Przejście do `odpowiedz_wyslana` ustawia `response_date = today`, jeśli puste.

**Uwaga dla agentów:** niedozwolone przejście zwraca `409` z kodem `invalid_transition`, nie `422`.

---

## 3. Urgency (W2)

Wyliczane z `days_remaining` i `status`:

| Warunek | `urgency` | Kolor UI |
|---|---|---|
| `status == odpowiedz_wyslana` | `closed` | szary |
| `days_remaining < 0` | `overdue` | czerwony |
| `days_remaining == 0` | `today` | bursztynowy |
| `days_remaining == 1` | `tomorrow` | żółty |
| `days_remaining <= 3` | `soon` | jasnożółty |
| pozostałe | `normal` | neutralny |

Zadanie mówi o wyróżnieniu wniosków „na które należy odpowiedzieć w danym dniu i dniu poprzedzającym". Interpretujemy to jako `today` + `tomorrow` (termin dziś i termin jutro) — bo to jest operacyjnie użyteczne. `overdue` dostaje osobny, mocniejszy kolor.

---

## 4. Polityka terminów

```python
DEFAULT_RESPONSE_DAYS = 14   # art. 13 ust. 1 ustawy o dostępie do informacji publicznej
```

- `deadline = inflow_date + DEFAULT_RESPONSE_DAYS`, jeśli nie podano jawnie.
- Wartość konfigurowalna: `settings.default_response_days`.
- Ręczne nadpisanie `deadline` jest dozwolone i trwałe (W3 wymaga pola edytowalnego).
- `kwerenda` nie zmienia `deadline` automatycznie — urzędnik przedłuża ręcznie. To świadoma decyzja: automatyczne przesuwanie terminu ukrywałoby przekroczenia przed urzędnikiem.

> Do potwierdzenia u organizatora, czy narzędzie ma liczyć termin ustawowy, czy tylko wyświetlać termin wprowadzony ręcznie. Domyślnie liczymy 14 dni, ale pole jest edytowalne — więc oba warianty są obsłużone.

---

## 5. Dokument (Document)

| `kind` | Znaczenie | Trafia do |
|---|---|---|
| `wniosek` | wgrany wniosek UDIP | sprawa + archiwum |
| `odpowiedz_wydzialu` | odpowiedź z wydziału | generator odpowiedzi |
| `archiwum` | archiwalna odpowiedź | wyszukiwanie podobnych |
| `ustawa` | tekst ustawy / wyciąg | baza wiedzy |
| `zarzadzenie` | zarządzenie urzędu | baza wiedzy |
| `inne` | — | baza wiedzy |

Statusy: `pending → parsed → indexed`, albo `failed` z polem `error`.

**Offsety są obowiązkowe.** Każdy chunk musi nieść `page` lub `section`, bo generator odpowiedzi cytuje źródła (W4). Chunk bez offsetu jest błędem, nie ostrzeżeniem.

---

## 6. Span anonimizacji (W6, W7)

```python
@dataclass(frozen=True)
class Span:
    start: int          # offset w tekście, inclusive
    end: int            # offset, exclusive
    text: str           # dokładny fragment
    category: SpanCategory
    confidence: float   # 0..1
    source: Literal["regex", "ner", "llm"]
```

Reguły scalania przy nakładaniu:

1. Wyższa `confidence` wygrywa.
2. Przy równej — wygrywa `regex` (najwyższa precyzja na numerach).
3. Span zawierający inny span pochłania go.
4. Spany częściowo się nakładające: wygrywa dłuższy.

**Kategorie krytyczne** (jury testuje w punkcie 3): `pesel`, `nip`, `telefon`, `email`, `imie_nazwisko`, `adres`.

### 6.1. Mapowanie na listę UMB

„Dane podlegające anonimizacji” Urzędu Miasta Bydgoszczy ma 28 pozycji. Dwie z nich rozbijamy na dwie kategorie, bo w praktyce wykrywa je inna reguła:

| Pozycja listy UMB | Kategoria |
|---|---|
| Imię i nazwisko osoby fizycznej | `imie_nazwisko` |
| Numer PESEL | `pesel` |
| Dowód osobisty lub inny dokument tożsamości | `dowod`, `paszport` |
| Numer NIP osoby fizycznej | `nip` |
| Data i miejsce urodzenia | `data_urodzenia`, `miejsce_urodzenia` |
| Adres zamieszkania, zameldowania lub korespondencyjny | `adres` |
| Prywatny numer telefonu | `telefon` |
| Prywatny adres e-mail | `email` |
| Numer rachunku bankowego | `iban` |
| Własnoręczny podpis (parafka) | `podpis` |
| Wizerunek | `wizerunek` |
| Stan cywilny i sytuacja rodzinna | `stan_cywilny` |
| Stan zdrowia, niepełnosprawność, nałogi | `zdrowie` |
| Sytuacja majątkowa, dochody, zadłużenie | `majatek` |
| Korzystanie ze świadczeń pomocy społecznej | `pomoc_spoleczna` |
| Poglądy polityczne, przekonania religijne | `poglady` |
| Przynależność związkowa lub partyjna | `przynaleznosc` |
| Pochodzenie rasowe lub etniczne | `pochodzenie` |
| Orientacja seksualna | `orientacja` |
| Karalność, wyroki, naruszenia prawa | `karalnosc` |
| Numer księgi wieczystej | `ksiega_wieczysta` |
| Numer działki ewidencyjnej | `dzialka` |
| Numer rejestracyjny pojazdu | `rejestracja` |
| Tajemnica przedsiębiorstwa | `tajemnica_przedsiebiorstwa` |
| Tajemnica skarbowa | `tajemnica_skarbowa` |
| Tajemnica bankowa i ubezpieczeniowa | `tajemnica_bankowa` |
| Tajemnica ustawowo chroniona (zawodowa, lekarska, adwokacka) | `tajemnica_zawodowa` |
| Informacje niejawne (klauzule poufności) | `informacje_niejawne` |

Poza listą zostają dwie kategorie: `regon` (potrzebny do identyfikacji podmiotu gospodarczego) i `inne` (przypadki spoza katalogu, np. sygnatury akt).

**Co wykrywa reguła, a co model.** Regex łapie identyfikatory o stałym formacie: `pesel`, `nip`, `regon`, `dowod`, `paszport`, `telefon`, `email`, `iban`, `adres`, `data_urodzenia`, `miejsce_urodzenia`, `ksiega_wieczysta`, `dzialka`, `imie_nazwisko`. Kategorie semantyczne (`wizerunek`, `zdrowie`, `majatek`, `poglady`, `orientacja`, `karalnosc`, `przynaleznosc`, `pochodzenie`, `pomoc_spoleczna`, `stan_cywilny`, `podpis`, `rejestracja`) oraz pięć tajemnic ustawowych oznacza model językowy albo urzędnik ręcznie — rozpoznanie wymaga kontekstu sprawy, nie wzorca tekstu. Metryki w `/api/anonymize/evaluate` mierzą więc detektory regułowe; kategorie semantyczne nie mają próbek w zbiorze held-out i nie wchodzą do F1.

**Zakaz fałszywych trafień:** numery wniosków (`BKS.IV.1431.12.2026`) i sygnatury akt nie mogą być klasyfikowane jako `nip` ani `regon`. To najczęstszy błąd detektorów numerycznych — regex musi mieć negatywny lookbehind na `BKS.` i kropki. Adresy w domenie `um.bydgoszcz.pl` to dane instytucji, nie osoby — nie podlegają anonimizacji.

---

## 7. Projekt odpowiedzi (Draft)

- `body` to Markdown z odnośnikami `[^1]`, `[^2]` mapującymi na `citations[].ref`.
- Każde zdanie faktyczne musi mieć odnośnik albo trafić do `unsupported`.
- `unsupported` nie usuwa zdania — oznacza je. Urzędnik decyduje (O3).
- Eksport DOCX zachowuje strukturę pisma urzędowego: nagłówek, data, znak sprawy, adresat, treść, podpis.

---

## 8. Słownik pojęć

| Pojęcie | Znaczenie |
|---|---|
| UDIP | ustawa o dostępie do informacji publicznej |
| KPA | Kodeks postępowania administracyjnego |
| UMB | Urząd Miasta Bydgoszczy |
| kwerenda | dodatkowy czas na przygotowanie odpowiedzi |
| wniosek | wniosek o udostępnienie informacji publicznej |
| sprawa | wniosek wraz z całym cyklem obsługi |

---

## 9. Konwencje

- Backend: `snake_case`, daty jako ISO 8601, UUID jako string.
- Frontend: `camelCase` w kodzie, `snake_case` w DTO (bez transformacji — mniej błędów).
- Wszystkie teksty UI po polsku, w `features/<x>/i18n.ts` modułu.
- Błędy: `{code, message, details}` — `message` po polsku, `code` po angielsku.
