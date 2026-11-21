# Inteligentny asystent urzędnika

## Generator odpowiedzi na UDIP z kalendarzem (organizatorem) wniosków

**HackNation 2026 · Miasto Bydgoszcz**

> Dokument ujednolicony. Scala dwa źródła: *Wyzwanie hackathon* (8 s., opis zadania)
> oraz *Regulamin zadania konkursowego* (4 s., warunki formalne). Numeracja, słownictwo
> i struktura zostały sprowadzone do jednego porządku; rozbieżności źródłowe zebrano w §13.

---

## §0. Metryka zadania

| Pole | Wartość |
|---|---|
| Nazwa zadania | Inteligentny asystent urzędnika — Generator odpowiedzi na UDIP z kalendarzem (organizatorem) wniosków |
| Wydarzenie | HackNation 2026 |
| Organizator wydarzenia | Ministerstwo Cyfryzacji, ul. Królewska 27, 00-060 Warszawa |
| Operator wydarzenia | PROIDEA sp. z o.o., ul. Zakopiańska 9, 30-418 Kraków, KRS 0000448243, NIP 6793088842 |
| Przyrzekający (fundator nagrody) | Miasto Bydgoszcz, ul. Jezuicka 1 — Łukasz Krupa (Zastępca Prezydenta Miasta, pełnomocnictwo WOA-I.0052.779.2024 z 30.07.2024) oraz Piotr Tomaszewski (Skarbnik Miasta) |
| Nagroda | 15 000,00 zł brutto — jedna nagroda główna |
| Uczestnictwo | wyłącznie zarejestrowani Uczestnicy HackNation 2026 |
| Forma oddania | działający prototyp + film ≤ 3 min + prezentacja ≤ 10 slajdów |
| Technologia | dowolna — brak narzuconego stosu i formatu |
| Reżim docelowy | praca w pełni lokalna, bez dostępu do Internetu |

---

## §1. Problem

Każdego dnia do urzędów trafiają dziesiątki wniosków o dostęp do informacji publicznej
(UDIP) — od mieszkańców, aktywistów i dziennikarzy. Prawo do informacji jest ważną częścią
demokracji, ale dla urzędnika oznacza setki godzin na ręcznym przeszukiwaniu archiwów,
weryfikacji stron BIP i pisaniu od nowa powtarzalnych pism.

**Cel:** skrócić czas przygotowania odpowiedzi z kilku dni do kilku minut, bez oddawania
decyzji maszynie.

---

## §2. Oczekiwany rezultat

Innowacyjny, w pełni funkcjonalny prototyp cyfrowy, który przekształca obsługę wniosków UDIP
w Urzędzie Miasta Bydgoszczy w proces szybki, półautomatyczny i bezpieczny, wspierany przez
sztuczną inteligencję lub inną technologię.

- **Główna grupa docelowa:** urzędnicy obsługujący wnioski UDIP.
- **Efekt końcowy:** usprawnienie pracy całego urzędu i podniesienie jakości obsługi mieszkańców.
- **Korzyści dla miasta:** oszczędność czasu pracy urzędników, odciążenie od zadań rutynowych,
  dbałość o ochronę danych osobowych, pozycjonowanie Bydgoszczy jako centrum innowacji.

---

## §3. Zakres funkcjonalny — 12 wymagań

Wymagania uporządkowano w sześć modułów. Numeracja źródłowa była błędna (powtórzony punkt 4,
brak punktu 8) — poniżej numeracja ciągła 1–12.

### Moduł A — Kalendarz wniosków

**W1. Tabela zintegrowana z kalendarzem**
Lista wniosków uporządkowana **od najstarszych do najnowszych**, z uwzględnieniem liczby dni
pozostałych na wysłanie odpowiedzi do wnioskodawcy.

**W2. Wyróżnianie terminów**
Wnioski, na które należy odpowiedzieć w danym dniu i w dniu poprzedzającym, odpowiednio
podświetlone. Dodatkowo wskazane wyróżnienie wniosków wymagających odpowiedzi w pierwszej
kolejności.

**W3. Pola rekordu wniosku**

- liczba porządkowa
- numer wniosku
- okno skróconego opisu tematu wniosku
- data wpływu
- termin odpowiedzi
- data udzielenia odpowiedzi
- inicjały osoby obsługującej wniosek
- status sprawy (patrz W12)
- filtr / wybór roku

### Moduł B — Generator odpowiedzi

**W4. Przygotowanie projektu odpowiedzi**
Po wgraniu przez urzędnika plików z odpowiedziami z wydziałów program przygotowuje projekt
pisma, który urzędnik następnie sprawdza — mechanizm ma wykluczyć błędy i halucynacje AI.

**W5. Wgrywanie plików i dokumentów**
Dane wejściowe wprowadzane ręcznie przez urzędnika obsługującego wnioski, przez wgranie pliku
w formacie PDF lub Word.

### Moduł C — Anonimizacja

**W6. Sugerowanie danych do anonimizacji**
Moduł wskazuje, które fragmenty gotowej odpowiedzi powinny zostać zanonimizowane —
podświetlenie obszaru tekstu na szaro, po akceptacji urzędnika na czarno.

**W7. Automatyczna anonimizacja**
Program proponuje, a następnie automatycznie anonimizuje wszelkie nadmiarowe dane
(np. dane osobowe).

### Moduł D — Wiedza i archiwum

**W8. Uczenie się na bazie wprowadzanych danych**
Możliwość uczenia się na dostarczanych materiałach: ustawy, aktualizacje ustaw, wnioski,
odpowiedzi, zarządzenia.

**W9. Przeszukiwanie archiwum**
Przeszukiwanie bazy archiwalnych odpowiedzi w celu łatwego znalezienia podobnych wniosków
z przeszłości — w szczególności z ostatniego roku.

### Moduł E — Ścieżka urzędowa

**W10. Wskazywanie ścieżki**
Podpowiedź dla urzędnika w zakresie najlepszej możliwej ścieżki pozyskania odpowiedzi
z konkretnych wydziałów urzędu.

### Moduł F — Organizacja pracy

**W11. Automatyzacja**
Automatyzacja rutynowych, powtarzalnych czynności.

**W12. Status sprawy aktualizowany na każdym kroku**

| Kod | Status |
|---|---|
| a | brak działań |
| b | zapytania wysłane do wydziałów |
| c | kwerenda + liczba dni |
| d | przygotowana odpowiedź |
| e | odpowiedź wysłana do wnioskodawcy |

Stany dodatkowe wymienione w opisie pól: „odpowiedź w przygotowaniu", „kwerenda"
(czyli dodatkowy czas na przygotowanie odpowiedzi), „odpowiedź wysłana".

---

## §4. Wymagania techniczne i bezpieczeństwo

**T1. Model AI i środowisko**
Podczas Hackathonu dopuszczalne jest otwarte AI. Docelowy program musi działać na
**zamkniętym modelu, bez dostępu do Internetu**, z możliwością uczenia się na bazie
wprowadzanych danych.

**T2. Bezpieczeństwo i wdrażalność**
Projekt nie może narażać użytkowników ani miasta na wycieki danych. Musi być gotowy do
wdrożenia — łatwy do zainstalowania i uruchomienia w Bydgoszczy.

**T3. Skalowalność**
Rozwiązanie musi działać dobrze nie tylko dla pojedynczych spraw, ale dla setek archiwalnych
dokumentów. Myślenie o tym, jak miasto mogłoby używać go przez lata, jest istotne.

**T4. Użyteczność**
Rozwiązanie musi być łatwe w użyciu dla każdego urzędnika. Prototyp powinien sprawnie przyjąć
wczytany plik (PDF lub Word), przeszukać lokalną bazę, podpowiedzieć właściwy wydział, a po
wpisaniu danych wygenerować projekt odpowiedzi i zanonimizować dane.

**T5. Stabilność i realność wykonania**
Nie trzeba używać trudnych technologii, ale prototyp musi być stabilny i dobrze działać.
Oceniany jest projekt do pokazania, nie plan. Liczy się realność wykonania w czasie konkursu,
dostępność i koszt techniki.

**T6. Dane testowe**
Podczas Hackathonu dozwolone jest otwarte AI, ponieważ wykorzystywane będą testowe wnioski
bez rzeczywistych danych. Koncepcja musi jednak uwzględniać, że docelowo aplikacja w urzędzie
będzie działała w pełni lokalnie, bez dostępu do Internetu, zapewniając pełne bezpieczeństwo
danych osobowych.

---

## §5. Ograniczenia (non-goals)

**O1. Brak automatycznej wysyłki.** Program nie będzie niczego samodzielnie wysyłał — ani do
wydziałów, ani na zewnątrz.

**O2. Brak integracji z systemami urzędowymi.** Nie ma potrzeby integracji z żadnym innym
systemem urzędowym, w tym z systemem SIDAS.

**O3. Narzędzie pomocnicze.** Program służy wyłącznie jako narzędzie wsparcia — ostateczną
decyzję zawsze podejmuje urzędnik.

**O4. Brak narzuconej technologii.** Nie narzuca się konkretnej technologii ani formatu.

---

## §6. Przepływ pracy urzędnika

1. Narzędzie „uczy się" przez wgranie aktualnych ustaw, archiwalnych odpowiedzi na wnioski,
   zarządzeń itp.
2. Urzędnik wgrywa plik (PDF lub Word) z wnioskiem o informację publiczną.
3. Narzędzie analizuje wniosek i pokazuje listę podobnych wniosków, które wpłynęły w ostatnim roku.
4. Narzędzie wyświetla listę propozycji wydziałów, do których urzędnik wyśle prośbę
   o przygotowanie odpowiedzi.
5. Wniosek zostaje umieszczony na liście wniosków; urzędnik akceptuje wprowadzone dane
   (termin, inicjały, daty, numer wniosku itd.).
6. Poza narzędziem: z wydziałów spływa odpowiedź; urzędnik wgrywa ją do narzędzia, po otwarciu
   danej sprawy / wniosku.
7. Na podstawie wgranych odpowiedzi narzędzie przygotowuje szablon odpowiedzi, z zaznaczonymi
   polami do potencjalnej anonimizacji.
8. Urzędnik akceptuje anonimizację lub odznacza tekst do ukrycia.
9. Narzędzie generuje odpowiedź w pliku doc / txt.
10. Urzędnik sprawdza odpowiedź pod względem merytorycznym i nanosi poprawki.
11. Narzędzie na każdym kroku aktualizuje status danej sprawy (patrz W12).

---

## §7. Dane, materiały i wsparcie

**Materiały testowe** — dostępne pod kodem QR w dniu rozpoczęcia Hackathonu, przekazane
przez mentorów:

- wzory pytań (wniosków UDIP) oraz odpowiedzi,
- robocza wizualizacja tabeli / kalendarium wniosków.

**Źródła danych i serwisy miejskie:**

- Biuletyn Informacji Publicznej UM Bydgoszczy
- lista wydziałów UMB — <https://bip.um.bydgoszcz.pl/artykuly/198/wydzialy>
- lista biur — <https://bip.um.bydgoszcz.pl/artykuly/1158/biura>
- ustawa KPA — <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=wdu19600300168>
- ustawa UDIP — <https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=wdu20011121198>

**Wsparcie na miejscu:**

- mentorzy z UMB (Urząd Miasta Bydgoszczy) — komunikacja i procedury urzędowe,
- pracownik Biura Komunikacji Społecznej,
- pracownik Biura Rady Miasta Bydgoszczy,
- eksperci dostępni na stoisku Bydgoszczy lub na dedykowanym kanale Discord.

---

## §8. Kryteria oceny

| Kryterium | Waga |
|---|---|
| Związek z wyzwaniem (zgodność z założeniami) | 30% |
| Bezpieczeństwo i skuteczna anonimizacja danych | 20% |
| Łatwość obsługi i użyteczność dla urzędnika | 20% |
| Kompletność i jakość działającego prototypu | 30% |
| **Razem** | **100%** |

Kryteria mają w źródle charakter **przykładowy**; zgodnie z Regulaminem (§2) pełna treść
zadania wraz z kryteriami jest publikowana w dniu rozpoczęcia Wydarzenia o godz. 11:00.

Dodatkowo: najwyżej ocenione zostaną zespoły, których rozwiązania są zupełnie nowe, bardzo
pomysłowe, bezpieczne i mają szansę na prawdziwe użycie w Bydgoszczy.

---

## §9. Jak jury sprawdzi projekt

1. Wgra przykładowy plik wniosku (PDF lub Word) i sprawdzi, czy program poprawnie odnajduje
   podobne sprawy w archiwum.
2. Sprawdzi, czy po podaniu odpowiedzi z wydziału program poprawnie układa projekt pisma.
3. Przeprowadzi test anonimizacji — wprowadzi plik zawierający dane osobowe i sprawdzi, czy
   program skutecznie je ukrywa.
4. Zobaczy, czy rozwiązanie jest łatwe w obsłudze, czy działa stabilnie i czy faktycznie pomaga
   urzędnikom; sprawdzi realność techniczną — czy da się go użyć w prawdziwym świecie.
5. Sprawdzi sposób ułożenia listy wniosków w kalendarzu i zaprojektowane rozwiązania, m.in.
   w jaki sposób narzędzie wskaże wnioski wymagające odpowiedzi w terminie wysyłki i jak oznacza
   wnioski na danym etapie obsługi.
6. Oceni sposób i łatwość wgrywania danych, aktualizacji ustaw, archiwalnych odpowiedzi.

---

## §10. Co trzeba oddać

**a) Film** — maksymalnie 3 minuty, prezentujący projekt.
**b) Prezentacja** — maksymalnie 10 slajdów.

**Obowiązkowa zawartość prezentacji (8 elementów):**

1. **Początek** — nazwa projektu i skład zespołu.
2. **Co rozwiązujecie** — jaki problem, jak program przyspiesza pracę urzędnika i chroni dane
   osobowe, dlaczego pomysł jest ważny.
3. **Pomysł** — dokładny opis działania: jak wyszukuje archiwalne sprawy, jak anonimizuje dane,
   jak działa kalendarz wniosków, jakiej technologii używa.
4. **Jak to działa** — krótki film lub prezentacja pokazująca prototyp w praktyce (wgrywanie
   PDF/Word, przetwarzanie, generowanie projektu odpowiedzi).
5. **Dla kogo** — kto z tego korzysta: urzędnicy JST.
6. **Przyszłość** — jak rozwiązanie mogłoby działać na stałe w Urzędzie Miasta Bydgoszczy.
7. **Narzędzia** — lista głównych programów i narzędzi, których użyliście.
8. **Tryb zamknięty** — informacja, czy prototyp będzie działał w zamkniętym systemie, bez
   dostępu do Internetu i dużych modeli językowych, ze wskazaniem propozycji konkretnego modelu
   działającego w zamkniętym środowisku.

---

## §11. Nagroda i prawa

### Nagroda

- Jedna nagroda główna: **15 000,00 zł brutto** (piętnaście tysięcy złotych brutto 00/100).
- Płatnikiem jest Przyrzekający; podatek oblicza, pobiera i odprowadza Przyrzekający —
  zwycięzca nie ponosi dodatkowych kosztów podatkowych.
- Wypłata w terminie 7 dni od podpisania umowy przeniesienia autorskich praw majątkowych
  i przekazania kodu źródłowego wraz z opisem.
- W zespole wieloosobowym nagroda dzielona równo między wszystkich członków.
- Nagroda nie podlega wymianie na inne świadczenie ani przeniesieniu na osoby trzecie.
- Brak podpisania umowy w terminie 7 dni → utrata prawa do nagrody; Przyrzekający może
  przyznać ją kolejnej drużynie wskazanej przez jury.

### Prawa autorskie

- Każdy uczestnik oświadcza, że jest twórcą swojego wkładu i przysługują mu pełne autorskie
  prawa majątkowe; użycie rozwiązań zewnętrznych musi być wyraźnie wskazane w prezentacji.
- Uczestnicy zapewniają, że rozwiązanie jest wolne od wad prawnych i nie narusza praw osób trzecich.
- Zwycięzcy zobowiązani do zawarcia umowy przeniesienia praw (Załącznik nr 1 do Regulaminu,
  udostępniany przed rozpoczęciem Wydarzenia).
- Przeniesienie praw do **programu komputerowego** — na polach eksploatacji z art. 74 ust. 4
  ustawy o prawie autorskim: zwielokrotnianie, tłumaczenie / przystosowanie / zmiana układu,
  rozpowszechnianie (w tym użyczanie i najem), zezwalanie na wykonywanie praw zależnych.
- Przeniesienie praw do **utworów niebędących programem** — na polach z art. 50: utrwalanie
  i zwielokrotnianie, wprowadzanie do pamięci komputera i udostępnianie w sieciach, wprowadzanie
  egzemplarzy do obrotu, publiczne odtwarzanie i udostępnianie, wystawianie, wyświetlanie,
  sporządzanie wersji obcojęzycznych (w tym dla osób z niepełnosprawnościami).
- W przypadku utworów zespołowych wszyscy współtwórcy podpisują umowę.
- Po ogłoszeniu wyników zwycięski zespół wypełnia i przekazuje oświadczenie z danymi do przelewu
  (Załącznik nr 2 do Umowy).

---

## §12. Zasady formalne

- Udział wyłącznie dla osób zarejestrowanych jako Uczestnicy HackNation 2026, spełniających
  warunki Regulaminu Wydarzenia.
- Jury powołuje Przyrzekający; minimum 3 członków ze specjalistyczną wiedzą w tematyce zadania.
- Skład jury publikowany najpóźniej w dniu rozpoczęcia Wydarzenia.
- Kryteria oceny publikowane wraz z pełną treścią zadania w dniu rozpoczęcia Wydarzenia o godz. 11:00.
- Jury może wybrać maksymalnie 3 zespoły do prezentacji; zwycięzca wyłaniany spośród nich.
- Decyzje jury są ostateczne, bez odwołania.
- W sprawach nieuregulowanych: Regulamin Wydarzenia (<https://www.hacknation.pl>), Kodeks cywilny.
- W razie rozbieżności między Regulaminem Zadania a Regulaminem Wydarzenia pierwszeństwo ma
  Regulamin Zadania.
- Regulamin Zadania wchodzi w życie z dniem publikacji w Serwisie.
- Miasto Bydgoszcz: najciekawsze i najbardziej obiecujące rozwiązania zostaną rozważone
  do wdrożenia i dalszego rozwoju.

---

## §13. Rozbieżności źródłowe — co poprawiono i co warto potwierdzić

| # | Problem w źródle | Lokalizacja | Rozstrzygnięcie |
|---|---|---|---|
| 1 | Numeracja wymagań: dwa punkty „4", brak punktu „8" | opis, §2 | przenumerowano ciągle 1–12 (W1–W12) |
| 2 | Brak sekcji 7; lista „Potencjalne źródła danych" wisi bez nagłówka, z pustymi i zagnieżdżonymi punktami | opis, s. 7 | wchłonięte do §7 „Dane, materiały i wsparcie" |
| 3 | „w dniu poprzedzającym" vs „w pierwszej kolejności" — dwie różne reguły wyróżniania | W2 | rozdzielono na dwa osobne wyróżnienia |
| 4 | Literówka „wystanie" zamiast „wysłanie" | opis, §2 pkt 3 | poprawiono |
| 5 | Skrót „UMB" nigdzie nie rozwinięty | opis, s. 3 i 6 | przyjęto Urząd Miasta Bydgoszczy |
| 6 | Statusy: 5 kodów (a–e) vs 3 nazwy w opisie pól | W12 | scalono w jeden słownik statusów |
| 7 | „10 wniosków testowych" tylko w sekcji technicznej | T4 / W1 | przeniesione do wymagań kalendarza |
| 8 | Kryteria opisane jako „przykładowe", a Regulamin zapowiada publikację kryteriów o 11:00 | §8 | oznaczone jako orientacyjne |
| 9 | Regulamin powołuje Załącznik nr 1 (umowa) i nr 2 (oświadczenie) — brak w materiałach | §11 | do pobrania z hacknation.pl |
| 10 | Regulamin §1.4 powołuje „Załącznik nr 2 do Porozumienia" (pełnomocnictwo) — inny Załącznik 2 niż w §4.10 | §11 | kolizja oznaczeń, nie wpływa na zadanie |
| 11 | Wymogi oddania (film 3 min, 10 slajdów) są tylko w opisie, nie w Regulaminie | §10 | traktować jako wiążące — pochodzą od Przyrzekającego |
| 12 | Brak wskazania ustawowego terminu odpowiedzi na UDIP (art. 13 ustawy) | W1 | do potwierdzenia: czy narzędzie ma liczyć termin ustawowy, czy tylko termin wprowadzony ręcznie |
