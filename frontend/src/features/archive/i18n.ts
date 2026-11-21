/** Teksty interfejsu modułu archiwum. */

export const TEXT = {
  title: "Archiwum spraw",
  description:
    "Wklej treść nowego wniosku — pokażemy sprawy, które urząd rozpatrzył wcześniej, wraz z gotową odpowiedzią.",

  queryTitle: "Treść wniosku",
  queryDescription:
    "Wklej treść wniosku albo wpisz kilka słów o tym, czego dotyczy. Im więcej szczegółów, tym trafniejsze wyniki.",
  queryLabel: "Zapytanie",
  queryPlaceholder:
    "Wklej treść wniosku, np. „Proszę o wykaz umów najmu lokali komunalnych wraz z wysokością czynszu…”",
  queryHint: "Wklej treść wniosku — nie musisz przepisywać jej własnymi słowami.",
  charCounter: (used: number, max: number) => `${used} / ${max} znaków`,
  search: "Szukaj w archiwum",
  searching: "Szukam…",
  clear: "Wyczyść",
  emptyQuery: "Wpisz treść wniosku, żeby przeszukać archiwum.",
  searchFailed: "Nie udało się przeszukać archiwum. Spróbuj ponownie.",

  optionsTitle: "Ustawienia wyszukiwania",
  limitLabel: "Liczba wyników",
  yearFromLabel: "Sprawy od roku",
  yearAny: "Bez ograniczeń",

  resultsTitle: "Podobne sprawy",
  resultsCount: (count: number) => `${count} ${count === 1 ? "sprawa" : "spraw"}`,
  resultsHint: "Posortowane od najbardziej podobnej.",

  emptyTitle: "Zacznij od treści wniosku",
  emptyDescription:
    "Archiwum przeszuka wszystkie zakończone sprawy — zarówno te z materiałów, jak i te zamknięte w aplikacji. Wyniki pokażą numer sprawy, temat, ocenę podobieństwa i fragmenty.",
  noResultsTitle: "Brak podobnych spraw",
  noResultsDescription:
    "Żadna sprawa w archiwum nie odpowiada temu zapytaniu. Spróbuj innych słów albo skróć zapytanie.",
  failedTitle: "Nie udało się przeszukać archiwum",

  scoreLabel: "Podobieństwo",
  matchedTermsLabel: "Dopasowane terminy",
  noMatchedTerms: "Brak wspólnych terminów",
  requestExcerptLabel: "Fragment wniosku",
  responseExcerptLabel: "Fragment odpowiedzi",
  yearLabel: (year: number | null) => (year ? `Rok ${year}` : "Rok nieznany"),

  details: "Szczegóły sprawy",
  useInResponse: "Użyj w odpowiedzi",
  copied: (caseNumber: string) => `Skopiowano numer sprawy ${caseNumber}`,
  copyFailed: (caseNumber: string) => `Numer sprawy: ${caseNumber}`,
  noDraftingScreen: (caseNumber: string) =>
    `Ekran odpowiedzi nie jest jeszcze gotowy. Numer sprawy: ${caseNumber}`,

  detail: {
    title: "Sprawa archiwalna",
    loading: "Wczytuję treść sprawy…",
    request: "Treść wniosku",
    response: "Treść odpowiedzi",
    departments: "Komórki organizacyjne",
    noDepartments: "Nie wskazano komórek organizacyjnych.",
    close: "Zamknij",
  },
} as const;

export const MAX_QUERY_CHARS = 4000;

export const LIMIT_OPTIONS = [3, 5, 10, 20] as const;

export const YEAR_OPTIONS = [2022, 2023, 2024, 2025, 2026] as const;
