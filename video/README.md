# Film o projekcie (Revideo)

Trzyminutowy film o *Inteligentnym asystencie urzędnika* zbudowany w
[Revideo](https://re.video) 0.10.4 — otwartoźródłowej (MIT) alternatywie dla
Remotion. Ten sam model pracy: scena to generator w TypeScripcie, animacje to
tweeny, render idzie przez przeglądarkę i ffmpeg.

Gotowy plik: [`../docs/asystent-urzednika.mp4`](../docs/asystent-urzednika.mp4)
(1920×1080, 30 fps, 2:55).

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
npm run render          # → out/asystent.mp4
```

Jeśli Puppeteer nie znajdzie przeglądarki:

```bash
CHROME_PATH=/sciezka/do/chrome npm run render
```

## Struktura

| Plik | Czas | Treść |
| --- | --- | --- |
| `scenes/01-title.tsx` | 0:00–0:08 | nazwa projektu, zespół, wydarzenie |
| `scenes/02-problem.tsx` | 0:08–0:24 | problem: kolejka, 14 dni, setki godzin, dane osobowe |
| `scenes/03-flow.tsx` | 0:24–0:38 | ścieżka: wniosek → archiwum → wydziały → projekt → anonimizacja → wysyłka |
| `scenes/04-demo.tsx` | 0:38–2:08 | dziewięć zrzutów działającego prototypu, po 10 s |
| `scenes/05-tech.tsx` | 2:08–2:25 | stos technologiczny i wdrożenie |
| `scenes/06-future.tsx` | 2:25–2:36 | dla kogo: dziś Bydgoszcz, jutro JST |
| `scenes/07-offline.tsx` | 2:36–2:47 | praca bez sieci: Bielik 11B v2.3 Instruct Q4_K_M |
| `scenes/08-outro.tsx` | 2:47–2:55 | nazwa, hasło, zespół |

`src/components.tsx` trzyma wspólne klocki (tło, nagłówek, ramka przeglądarki,
plakietki, karty statystyk, kropki postępu), `src/theme.ts` — kolory, font i
nazwy. Zrzuty w `src/assets/shots/` pochodzą z uruchomionej aplikacji w trybie
demo (`MODULE_MODE_DEFAULT=fake`), nie z makiety.

## Lektor

Film nie ma nagranej narracji. Pełny tekst z timingami jest w
[`narracja.md`](narracja.md), a `podloz-lektora.sh` kładzie wygenerowane pliki
TTS na ich znacznikach czasu:

```bash
mkdir lektor          # tu 01.wav, 02.wav, 03.wav, 04a.wav … 08.wav
./podloz-lektora.sh   # → ../docs/asystent-urzednika-lektor.mp4
```

Obraz jest kopiowany bez rekompresji, podmienia się tylko ścieżka dźwiękowa.

## Font

Inter (SIL Open Font License 1.1), pliki `woff2` w `src/assets/fonts/`,
podpięte przez `inter-local.css`. Render nie wymaga dostępu do sieci.
