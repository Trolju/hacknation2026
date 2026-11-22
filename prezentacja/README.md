# Prezentacja konkursowa (projekt Capricorn)

Dziesięć slajdów w formacie 16:9 (PDF 1440 × 810 pt) zgodnych z wymaganiami
`ZADANIE-KONKURSOWE.md`: maksymalnie 10 slajdów, osiem obowiązkowych elementów
oraz §11, czyli jawne wskazanie rozwiązań zewnętrznych.

Wynik: `prezentacja.pdf`. Samodzielny plik `prezentacja.html` (fonty i zrzuty
osadzone jako base64) umożliwia otwarcie tych samych slajdów w przeglądarce.

## Budowanie

```bash
export LD_LIBRARY_PATH=
python3 prezentacja/build.py
```

Ścieżka do `chrome-headless-shell` (jedyna zależność) jest wpisana na stałe
w `build.py`. `LD_LIBRARY_PATH=` jest konieczne, bo domyślne środowisko psuje
binarne pakiety systemowe. Skrypt: stdlib only, bez zależności Pythona.

`prezentacja.html` i `prezentacja.pdf` to artefakty budowane: są zignorowane
w git, więc po świeżym klonie powstają dopiero po uruchomieniu `build.py`.

## Stan przed wysyłką

- [x] **Nazwa i zespół** — tytuł slajdu 1 i stopka markują `Capricorn`, zespół
  to `sLaRpNaTiOn` (lista `TEAM` w `build.py`).
- [ ] **Zrzuty** — `assets/*.png` to kadry z `video/src/assets/shots/`
  (nagrania realnej aplikacji). Przy zmianie interfejsu przyciąć ponownie:

  ```bash
  export LD_LIBRARY_PATH=
  magick video/src/assets/shots/pulpit.png -crop 2600x1250+560+150 +repage prezentacja/assets/pulpit.png
  magick video/src/assets/shots/kalendarz.png -crop 2600x1300+560+150 +repage prezentacja/assets/kalendarz.png
  magick video/src/assets/shots/archiwum_results.png -crop 2600x836+560+1120 +repage prezentacja/assets/archiwum.png
  magick video/src/assets/shots/wydzialy_query.png -crop 1760x536+560+1220 +repage prezentacja/assets/routing.png
  magick video/src/assets/shots/odpowiedzi_draft.png -crop 2600x1240+560+560 +repage prezentacja/assets/generator.png
  magick video/src/assets/shots/anonimizacja_spans.png -crop 2600x1120+560+340 +repage prezentacja/assets/anonimizacja.png
  magick video/src/assets/shots/ustawienia.png -crop 2600x700+560+1300 +repage prezentacja/assets/modele.png
  ```

- [ ] **Liczby** — po kolejnym przebiegu testów zaktualizować metryki na
  slajdach 2-10 (źródła: `reports/`, `backend/tests/`).

## Mapowanie wymagań na slajdy

| Element zadania | Slajd |
| --- | --- |
| 1. Początek: nazwa + zespół | 1 · Capricorn + zespół sLaRpNaTiOn |
| 2. Co rozwiązujemy: problem, czas, dane | 2 · 14 dni UDIP, archiwum, dane osobowe, arkusz |
| 3. Pomysł: archiwum, anonimizacja, kalendarz, technologia | 3 · ścieżka 6 kroków, 8 modułów, SQLite |
| 4. Jak to działa: prototyp w praktyce | 4-7 · zrzuty: kalendarz, archiwum, routing, generator, anonimizacja |
| 5. Dla kogo: urzędnicy JST | 8 · cztery grupy w urzędzie |
| 6. Przyszłość: praca w UMB | 8 · pilotaż → wydział → cały urząd → inne JST |
| 7. Narzędzia | 9 · pięć grup + sekcja „czego świadomie nie ma" |
| 8. Tryb zamknięty: offline + nazwany model | 10 · dziś Mistral Small przez API Mistrala, w urzędzie OFFLINE=1 z lokalnym Bielikiem 11B v2.3 Instruct (Q4_K_M, 6,7 GB); alternatywa Qwen2.5 7B |

§11 (rozwiązania zewnętrzne): slajd 9 wskazuje wprost, że bieżący prototyp biega
na modelu Mistral Small przez API Mistrala, a slajd 10 pokazuje tę samą ścieżkę
na modelu lokalnym. Docelowo w urzędzie wszystkie komponenty są lokalne i
open source.

W treści slajdów nie ma półpauz i pauz em poza zakresami liczbowymi
(„4,2–5,6 s", „[2]–[13]").
