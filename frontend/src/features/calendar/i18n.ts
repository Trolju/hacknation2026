/** Teksty interfejsu kalendarza — wszystkie po polsku. */

import { format } from "date-fns";
import { pl } from "date-fns/locale";

export const t = {
  page: {
    title: "Kalendarz terminów",
    description:
      "Wnioski o udostępnienie informacji publicznej według terminu odpowiedzi. Termin ustawowy to 14 dni od wpływu.",
    refresh: "Odśwież",
    footer: (count: number) => `Wyświetlono ${count} wniosków.`,
  },
  filters: {
    year: "Rok",
    status: "Stan sprawy",
    sort: "Sortowanie",
    search: "Szukaj",
    searchPlaceholder: "Numer sprawy lub fragment przedmiotu…",
    all: "Wszystkie",
    sortDeadlineAsc: "Termin rosnąco",
    sortDeadlineDesc: "Termin malejąco",
    sortInflowAsc: "Wpływ rosnąco",
    sortInflowDesc: "Wpływ malejąco",
  },
  views: {
    label: "Widok",
    table: "Tabela",
    month: "Miesiąc",
  },
  table: {
    caseNumber: "Numer sprawy",
    subject: "Przedmiot wniosku",
    inflow: "Wpływ",
    deadline: "Termin",
    days: "Dni",
    urgency: "Pilność",
    status: "Stan",
    handler: "Prowadzący",
    empty: "Brak wniosków do wyświetlenia.",
  },
  month: {
    previous: "Poprzedni miesiąc",
    next: "Następny miesiąc",
    today: "Dziś",
    legend: "Kolor dnia wyznacza najpilniejszy termin, liczba — wnioski z terminem w tym dniu.",
    dayLabel: (day: Date, count: number) =>
      `${format(day, "d MMMM yyyy", { locale: pl })} — ${count} wniosków`,
  },
  day: {
    title: (day: Date) => `Terminy: ${format(day, "d MMMM yyyy", { locale: pl })}`,
    description: "Wnioski, których termin odpowiedzi przypada w tym dniu.",
    empty: "Brak wniosków z terminem w tym dniu.",
    open: "Otwórz sprawę",
  },
  detail: {
    title: "Szczegóły wniosku",
    loading: "Ładowanie sprawy…",
    fields: {
      caseNumber: "Numer sprawy",
      ordinal: "Liczba porządkowa",
      subject: "Przedmiot",
      inflow: "Data wpływu",
      deadline: "Termin odpowiedzi",
      responseDate: "Data odpowiedzi",
      days: "Dni do terminu",
      urgency: "Pilność",
      status: "Stan sprawy",
      handler: "Prowadzący",
      applicant: "Wnioskodawca",
      departments: "Komórki",
      notes: "Notatki",
      year: "Rok",
    },
    history: "Historia zmian",
    historyEmpty: "Brak zapisanych zmian.",
    historyLoading: "Ładowanie historii…",
    actions: {
      created: "Utworzenie sprawy",
      field_update: "Zmiana pól",
      status_change: "Zmiana stanu",
    },
    transition: {
      title: "Zmiana stanu",
      hint: "Przejście naprzód nie wymaga notatki. Cofnięcie stanu wymaga notatki.",
      noteLabel: "Notatka",
      notePlaceholder: "Powód zmiany stanu…",
      noteRequired: "Cofnięcie stanu wymaga notatki.",
      forward: (label: string) => `Przejdź do: ${label}`,
      skip: (label: string) => `Pomiń kwerendę: ${label}`,
      backward: (label: string) => `Cofnij do: ${label}`,
      saved: "Zapisano nowy stan sprawy.",
      failed: "Nie udało się zmienić stanu sprawy.",
      closedHint: "Sprawa jest zamknięta — cofnięcie wymaga notatki.",
      daysLabel: "Przedłużenie terminu (dni)",
      daysPlaceholder: "np. 14",
      daysHint:
        "Podaj, o ile dni przesunąć termin odpowiedzi. Puste pole zostawia termin bez zmian.",
      daysInvalid: "Przedłużenie terminu musi być liczbą dni.",
      daysApplied: (days: number) =>
        `Termin przedłużono łącznie o ${days} ${days === 1 ? "dzień" : "dni"}.`,
    },
    applicantTypes: {
      osoba_fizyczna: "Osoba fizyczna",
      organizacja: "Organizacja",
      media: "Media",
      inne: "Inne",
    },
  },
  errors: {
    load: "Nie udało się pobrać wniosków.",
  },
} as const;
