/**
 * Teksty i style modułu anonimizacji.
 *
 * Kolory są półprzezroczyste, żeby podświetlenie działało w motywie jasnym
 * i ciemnym — tekst pola pozostaje czytelny w obu.
 */

export const CATEGORY_LABELS: Record<string, string> = {
  pesel: "PESEL",
  nip: "NIP",
  regon: "REGON",
  dowod: "Dowód osobisty",
  paszport: "Paszport",
  telefon: "Telefon",
  email: "E-mail",
  iban: "Numer konta",
  adres: "Adres",
  imie_nazwisko: "Imię i nazwisko",
  data_urodzenia: "Data urodzenia",
  miejsce_urodzenia: "Miejsce urodzenia",
  podpis: "Podpis",
  ksiega_wieczysta: "Księga wieczysta",
  dzialka: "Numer działki",
  rejestracja: "Nr rejestracyjny",
  wizerunek: "Wizerunek",
  stan_cywilny: "Stan cywilny",
  zdrowie: "Zdrowie",
  majatek: "Majątek",
  pomoc_spoleczna: "Pomoc społeczna",
  poglady: "Poglądy i religia",
  przynaleznosc: "Przynależność",
  pochodzenie: "Pochodzenie",
  orientacja: "Orientacja",
  karalnosc: "Karalność",
  inne: "Inne",
};

export const CATEGORY_ORDER: string[] = [
  "pesel",
  "nip",
  "regon",
  "dowod",
  "paszport",
  "telefon",
  "email",
  "iban",
  "adres",
  "imie_nazwisko",
  "data_urodzenia",
  "miejsce_urodzenia",
  "podpis",
  "ksiega_wieczysta",
  "dzialka",
  "rejestracja",
  "wizerunek",
  "stan_cywilny",
  "zdrowie",
  "majatek",
  "pomoc_spoleczna",
  "poglady",
  "przynaleznosc",
  "pochodzenie",
  "orientacja",
  "karalnosc",
  "inne",
];

type CategoryStyle = {
  /** Tło podświetlenia w polu tekstowym. */
  mark: string;
  /** Wygląd plakietki na liście spanów. */
  badge: string;
};

const FALLBACK_STYLE: CategoryStyle = {
  mark: "bg-slate-400/40",
  badge: "border-slate-500/40 bg-slate-500/10 text-slate-700 dark:text-slate-300",
};

export const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  pesel: {
    mark: "bg-rose-400/40",
    badge: "border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-300",
  },
  nip: {
    mark: "bg-orange-400/40",
    badge:
      "border-orange-500/40 bg-orange-500/10 text-orange-700 dark:text-orange-300",
  },
  regon: {
    mark: "bg-amber-400/40",
    badge:
      "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300",
  },
  dowod: {
    mark: "bg-lime-400/40",
    badge: "border-lime-500/40 bg-lime-500/10 text-lime-700 dark:text-lime-300",
  },
  paszport: {
    mark: "bg-emerald-400/40",
    badge:
      "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  },
  telefon: {
    mark: "bg-teal-400/40",
    badge: "border-teal-500/40 bg-teal-500/10 text-teal-700 dark:text-teal-300",
  },
  email: {
    mark: "bg-cyan-400/40",
    badge: "border-cyan-500/40 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300",
  },
  iban: {
    mark: "bg-sky-400/40",
    badge: "border-sky-500/40 bg-sky-500/10 text-sky-700 dark:text-sky-300",
  },
  adres: {
    mark: "bg-indigo-400/40",
    badge:
      "border-indigo-500/40 bg-indigo-500/10 text-indigo-700 dark:text-indigo-300",
  },
  imie_nazwisko: {
    mark: "bg-violet-400/40",
    badge:
      "border-violet-500/40 bg-violet-500/10 text-violet-700 dark:text-violet-300",
  },
  data_urodzenia: {
    mark: "bg-fuchsia-400/40",
    badge:
      "border-fuchsia-500/40 bg-fuchsia-500/10 text-fuchsia-700 dark:text-fuchsia-300",
  },
  podpis: {
    mark: "bg-pink-400/40",
    badge: "border-pink-500/40 bg-pink-500/10 text-pink-700 dark:text-pink-300",
  },
  ksiega_wieczysta: {
    mark: "bg-stone-400/40",
    badge: "border-stone-500/40 bg-stone-500/10 text-stone-700 dark:text-stone-300",
  },
  dzialka: {
    mark: "bg-zinc-400/40",
    badge: "border-zinc-500/40 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300",
  },
  rejestracja: {
    mark: "bg-neutral-400/40",
    badge:
      "border-neutral-500/40 bg-neutral-500/10 text-neutral-700 dark:text-neutral-300",
  },
  miejsce_urodzenia: {
    mark: "bg-fuchsia-400/30",
    badge:
      "border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-700 dark:text-fuchsia-300",
  },
  wizerunek: {
    mark: "bg-purple-400/40",
    badge:
      "border-purple-500/40 bg-purple-500/10 text-purple-700 dark:text-purple-300",
  },
  stan_cywilny: {
    mark: "bg-rose-400/30",
    badge: "border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300",
  },
  zdrowie: {
    mark: "bg-red-400/40",
    badge: "border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-300",
  },
  majatek: {
    mark: "bg-amber-400/30",
    badge: "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300",
  },
  pomoc_spoleczna: {
    mark: "bg-orange-400/30",
    badge:
      "border-orange-500/30 bg-orange-500/10 text-orange-700 dark:text-orange-300",
  },
  poglady: {
    mark: "bg-yellow-400/40",
    badge:
      "border-yellow-500/40 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300",
  },
  przynaleznosc: {
    mark: "bg-lime-400/30",
    badge: "border-lime-500/30 bg-lime-500/10 text-lime-700 dark:text-lime-300",
  },
  pochodzenie: {
    mark: "bg-emerald-400/30",
    badge:
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  },
  orientacja: {
    mark: "bg-teal-400/30",
    badge: "border-teal-500/30 bg-teal-500/10 text-teal-700 dark:text-teal-300",
  },
  karalnosc: {
    mark: "bg-slate-400/40",
    badge: "border-slate-500/40 bg-slate-500/10 text-slate-700 dark:text-slate-300",
  },
  inne: FALLBACK_STYLE,
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

export function categoryStyle(category: string): CategoryStyle {
  return CATEGORY_STYLES[category] ?? FALLBACK_STYLE;
}

export const SOURCE_LABELS: Record<string, string> = {
  regex: "reguła",
  ner: "model",
  llm: "ręcznie",
};

export const TEXT = {
  title: "Anonimizacja",
  description:
    "Wykryj dane osobowe w treści pisma, przejrzyj zaznaczenia i zastąp je placeholderem przed dalszym przetwarzaniem.",
  inputTitle: "Tekst do anonimizacji",
  inputDescription:
    "Wklej treść pisma. Zaznacz fragment i dodaj go ręcznie, jeśli detektor go pominął.",
  detect: "Wykryj dane osobowe",
  detecting: "Wykrywanie…",
  clear: "Wyczyść",
  example: "Wstaw przykład",
  placeholderLabel: "Placeholder",
  placeholderHint: "Tekst wstawiany w miejsce usuniętych fragmentów.",
  apply: "Zastosuj anonimizację",
  applying: "Przetwarzanie…",
  resultTitle: "Podgląd po anonimizacji",
  resultDescription: "Tak będzie wyglądał tekst po zastąpieniu zaznaczeń.",
  copy: "Kopiuj wynik",
  copied: "Skopiowano do schowka",
  copyFailed: "Nie udało się skopiować — zaznacz tekst ręcznie.",
  spansTitle: "Wykryte fragmenty",
  spansEmpty: "Brak wykrytych fragmentów. Wklej tekst i uruchom wykrywanie.",
  spansStale: "Tekst zmienił się — uruchom wykrywanie ponownie.",
  remove: "Usuń",
  accept: "Akceptuj",
  unaccept: "Cofnij akceptację",
  acceptAll: "Akceptuj wszystkie",
  rejectAll: "Odrzuć wszystkie",
  pendingHint:
    "Szare fragmenty nie zostaną usunięte, dopóki ich nie zaakceptujesz.",
  acceptedSummary: "zaakceptowanych",
  nothingAccepted: "Zaakceptuj przynajmniej jeden fragment.",
  addSelection: "Dodaj zaznaczenie",
  addSelectionHint:
    "Zaznacz fragment w polu tekstowym, wybierz kategorię i dodaj go do listy.",
  noSelection: "Najpierw zaznacz fragment w polu tekstowym.",
  categoryLabel: "Kategoria",
  metricsTitle: "Metryki jakości",
  metricsDescription:
    "Ocena na ręcznie napisanym zbiorze held-out (40 próbek spoza fixtures).",
  metricsUnavailable: "Nie udało się pobrać metryk.",
  precision: "Precyzja",
  recall: "Pełność",
  f1: "F1",
  support: "Próbek",
  category: "Kategoria",
  detected: "Wykryto",
  removed: "Usunięto",
  manual: "ręcznie",
  detectFailed: "Nie udało się wykryć danych osobowych.",
  applyFailed: "Nie udało się zastosować anonimizacji.",
  emptyText: "Najpierw wklej tekst do anonimizacji.",
} as const;

export const EXAMPLE_TEXT =
  "Wnioskodawca Jan Kowalski, PESEL 85041212345, zamieszkały przy " +
  "ul. Gdańska 42/7, 85-005 Bydgoszcz, prosi o udostępnienie informacji " +
  "o wydatkach na promocję. Kontakt: +48 601 234 567, " +
  "jan.kowalski@example.com. Sprawę prowadzi Anna Nowak.";
