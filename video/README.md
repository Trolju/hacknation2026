# Film o projekcie (Revideo)

Film o *Inteligentnym asystencie urzędnika* zbudowany w
[Revideo](https://re.video) 0.10.4 — otwartoźródłowej (MIT) alternatywie dla
Remotion. Ten sam model pracy: scena to generator w TypeScripcie, animacje to
tweeny, render idzie przez przeglądarkę i ffmpeg.

Gotowe pliki (1920×1080, 30 fps, 1:46):

- [`../docs/asystent-urzednika-bez-dzwieku.mp4`](../docs/asystent-urzednika-bez-dzwieku.mp4)
  — tylko obraz, bez strumienia audio. Do przeglądu i do podłożenia lektora.
- [`../docs/asystent-urzednika.mp4`](../docs/asystent-urzednika.mp4) — to samo
  plus cicha ścieżka AAC, którą dokleja Revideo.

Wersja 2 stawia na tempo: 16 scen, prawdziwe nagrania działającej aplikacji z
przejazdem kamery po interfejsie i typografią kinetyczną zamiast statycznych
zrzutów.

## Zanim wyrenderujesz

Nazwiska w napisach są zaślepką. Podmień je w jednym miejscu —
`src/theme.ts`:

```ts
export const TEAM = ['Imię Nazwisko', 'Imię Nazwisko', 'Imię Nazwisko'];
```

Ta tablica trafia do planszy tytułowej i do planszy końcowej.

## Render

```bash
cd video
npm install
npm run render          # → output/out/asystent.mp4
```

Jeśli Puppeteer nie znajdzie przeglądarki:

```bash
CHROME_PATH=/sciezka/do/chrome npm run render
```

Render trzyma `workers: 2` w `render.mjs`. Przy czterech procesach maszyna z
15 GB RAM kończy się OOM na ok. 80% klipu.

## Struktura

| Plik | Czas | Treść |
| --- | --- | --- |
| `scenes/01-intro.tsx` | 0:00–0:06 | nazwa projektu, hasło, trzy liczby, zespół |
| `scenes/02-problem.tsx` | 0:06–0:16 | problem: dziesiątki wniosków, setki godzin, te same pisma → „kilka minut” |
| `scenes/03-modules.tsx` | 0:16–0:19 | osiem modułów jako kafle |
| `scenes/04-feature.tsx` | 0:19–1:15 | osiem modułów na żywo, po jednym nagraniu na moduł |
| `scenes/05-workflow.tsx` | 1:15–1:22 | pięć kroków obsługi wniosku |
| `scenes/06-stack.tsx` | 1:22–1:28 | stos technologiczny w czterech kolumnach |
| `scenes/07-offline.tsx` | 1:28–1:34 | bezpieczeństwo i model lokalny (Bielik 11B v2.3) |
| `scenes/08-audience.tsx` | 1:34–1:39 | dla kogo i co dalej w Bydgoszczy |
| `scenes/09-outro.tsx` | 1:39–1:46 | nazwa, podziękowanie, zespół |

`src/components.tsx` trzyma wspólne klocki (tło, kicker, nagłówek, karta z
nagraniem, podpisy modułów, pasek postępu), `src/theme.ts` — kolory, font i
nazwy, a `src/features.ts` — osiem modułów: nazwę, korzyść, wynik, akcent i
klucze kamery.

Nagrania w `src/assets/clips/` pochodzą z uruchomionej aplikacji w trybie demo
(`scripts/demo.sh --fake`), nie z makiety. Każdy klip to 3200×2000 przy 30 fps,
zrzucany przez CDP w pętli i sklejany do CFR.

## Lektor

Film nie ma nagranej narracji. Pełny tekst z timingami jest w
[`narracja.md`](narracja.md), a `podloz-lektora.sh` kładzie wygenerowane pliki
TTS na ich znacznikach czasu:

```bash
mkdir lektor          # tu 01.wav, 02.wav, 03.wav, 04a.wav … 04h.wav, 05.wav … 09.wav
./podloz-lektora.sh   # → ../docs/asystent-urzednika-lektor.mp4
```

Obraz jest kopiowany bez rekompresji, podmienia się tylko ścieżka dźwiękowa.

## Font

Inter (SIL Open Font License 1.1), pliki `woff2` w `src/assets/fonts/`,
podpięte przez `inter-local.css`. Render nie wymaga dostępu do sieci.
