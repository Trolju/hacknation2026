import archiwum from './assets/clips/archiwum.mp4';
import anonimizacja from './assets/clips/anonimizacja.mp4';
import dokumenty from './assets/clips/dokumenty.mp4';
import kalendarz from './assets/clips/kalendarz.mp4';
import odpowiedzi from './assets/clips/odpowiedzi.mp4';
import pulpit from './assets/clips/pulpit.mp4';
import ustawienia from './assets/clips/ustawienia.mp4';
import wydzialy from './assets/clips/wydzialy.mp4';
import {COLORS} from './theme';

export type CamKey = {t: number; z: number; fx: number; fy: number};

export type Feature = {
  id: string;
  index: string;
  name: string;
  benefit: string;
  result: string;
  accent: string;
  clip: string;
  /** Czas trwania nagrania w sekundach. */
  dur: number;
  /** Prędkość odtwarzania — skraca materiał i dodaje tempa. */
  rate: number;
  /** Dodatkowy czas po zakończeniu nagrania (klatka stoi, wjeżdża chip). */
  hold: number;
  camera: CamKey[];
};

export const FEATURES: Feature[] = [
  {
    id: 'pulpit',
    index: '01',
    name: 'Pulpit',
    benefit: 'Wszystkie wnioski, terminy i ryzyka na jednym ekranie',
    result: '4 kategorie pilności',
    accent: COLORS.blue,
    clip: pulpit,
    dur: 5.63,
    rate: 1.05,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 2.2, z: 1.40, fx: 0.58, fy: 0.26},
      {t: 5.63, z: 1.47, fx: 0.58, fy: 0.72},
    ],
  },
  {
    id: 'kalendarz',
    index: '02',
    name: 'Kalendarz wniosków',
    benefit: 'Terminy ustawowe, statusy i „dziś / jutro” podświetlone',
    result: '10 wniosków, 1 widok',
    accent: COLORS.sky,
    clip: kalendarz,
    dur: 4.93,
    rate: 1.0,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 1.9, z: 1.36, fx: 0.56, fy: 0.44},
      {t: 4.93, z: 1.32, fx: 0.8, fy: 0.34},
    ],
  },
  {
    id: 'dokumenty',
    index: '03',
    name: 'Baza wiedzy',
    benefit: 'PDF i Word wgrane, pocięte na fragmenty i zindeksowane',
    result: 'Zindeksowany w 1 krok',
    accent: COLORS.violet,
    clip: dokumenty,
    dur: 6.33,
    rate: 1.1,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 2.0, z: 1.44, fx: 0.58, fy: 0.34},
      {t: 6.33, z: 1.38, fx: 0.58, fy: 0.6},
    ],
  },
  {
    id: 'archiwum',
    index: '04',
    name: 'Przeszukiwanie archiwum',
    benefit: 'Opis sprawy zamiast słów kluczowych — trafność 0,90',
    result: '0,90 · najlepsze trafienie',
    accent: COLORS.green,
    clip: archiwum,
    dur: 8.1,
    rate: 1.15,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 1.8, z: 1.34, fx: 0.58, fy: 0.24},
      {t: 3.6, z: 1.42, fx: 0.58, fy: 0.54},
      {t: 8.1, z: 1.55, fx: 0.58, fy: 0.44},
    ],
  },
  {
    id: 'wydzialy',
    index: '05',
    name: 'Ścieżka do wydziału',
    benefit: 'Podpowiedź komórki organizacyjnej z uzasadnieniem',
    result: 'Pewność 64%',
    accent: COLORS.amber,
    clip: wydzialy,
    dur: 7.7,
    rate: 1.15,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 1.8, z: 1.34, fx: 0.58, fy: 0.24},
      {t: 7.7, z: 1.49, fx: 0.58, fy: 0.6},
    ],
  },
  {
    id: 'odpowiedzi',
    index: '06',
    name: 'Projekt odpowiedzi',
    benefit: 'Pismo z podstawą prawną i przypisami do źródeł',
    result: '6 przypisów do źródeł',
    accent: COLORS.blue,
    clip: odpowiedzi,
    dur: 8.03,
    rate: 1.15,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 1.8, z: 1.34, fx: 0.58, fy: 0.24},
      {t: 3.8, z: 1.42, fx: 0.58, fy: 0.5},
      {t: 8.03, z: 1.36, fx: 0.8, fy: 0.44},
    ],
  },
  {
    id: 'anonimizacja',
    index: '07',
    name: 'Anonimizacja',
    benefit: 'PESEL, NIP, adres, telefon — wykryte i usunięte',
    result: 'F1 100% na 40 sprawach',
    accent: COLORS.red,
    clip: anonimizacja,
    dur: 9.5,
    rate: 1.2,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 1.8, z: 1.36, fx: 0.58, fy: 0.24},
      {t: 3.8, z: 1.45, fx: 0.72, fy: 0.3},
      {t: 9.5, z: 1.40, fx: 0.58, fy: 0.68},
    ],
  },
  {
    id: 'ustawienia',
    index: '08',
    name: 'Model i moduły',
    benefit: 'Każdy moduł przełączany — chmura albo lokalny Bielik',
    result: '8 modułów · tryb realny',
    accent: COLORS.teal,
    clip: ustawienia,
    dur: 4.17,
    rate: 1.0,
    hold: 1.0,
    camera: [
      {t: 0, z: 1.0, fx: 0.5, fy: 0.5},
      {t: 1.6, z: 1.36, fx: 0.58, fy: 0.24},
      {t: 4.17, z: 1.34, fx: 0.58, fy: 0.66},
    ],
  },
];

/** Czas trwania segmentu modułu. */
export const featureDuration = (f: Feature) => f.dur / f.rate + f.hold;
