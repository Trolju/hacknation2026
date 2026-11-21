/** Teksty interfejsu pulpitu — wszystkie po polsku. */

export const t = {
  page: {
    title: "Pulpit",
    description: "Stan wniosków o udostępnienie informacji publicznej na dziś.",
    openCalendar: "Otwórz kalendarz",
  },
  stats: {
    overdue: "Po terminie",
    today: "Termin dziś",
    soon: "W najbliższych dniach",
    closed: "Zamknięte",
  },
  chart: {
    title: "Rozkład pilności",
    description: "Liczba wniosków w każdej kategorii terminów.",
    series: "Wnioski",
    empty: "Brak wniosków do pokazania na wykresie.",
  },
  closed: {
    title: "Zamknięte w ostatnich 30 dniach",
    description: "Sprawy z wysłaną odpowiedzią, od najnowszej.",
    empty: "Brak spraw zamkniętych w ostatnich 30 dniach.",
    responseDate: "Odpowiedź",
  },
  upcoming: {
    title: "Najbliższe terminy",
    description: "Wnioski wymagające uwagi, posortowane od najpilniejszego.",
    empty: "Brak wniosków wymagających uwagi.",
  },
  footer: {
    nextDeadline: "Najbliższy termin",
  },
} as const;
