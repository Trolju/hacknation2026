/** Teksty modułu routingu wydziałowego. */

export const TEXT = {
  title: "Routing wydziałowy",
  description:
    "Wskaż komórki organizacyjne właściwe dla wniosku i przygotuj treść zapytania do nich.",

  caseLabel: "Sprawa z kalendarza",
  casePlaceholder: "Wybierz sprawę",
  caseManual: "Wklej treść ręcznie",
  caseHint:
    "Wybór sprawy wypełnia treść przedmiotem wniosku i pozwala wygenerować zapytanie z numerem oraz terminem.",
  caseMissing: "Nie udało się pobrać listy wniosków.",

  textLabel: "Treść do analizy",
  textPlaceholder:
    "Wklej treść wniosku albo wybierz sprawę z listy — sugestie pojawią się same.",
  textHint: "Sugestie aktualizują się w trakcie pisania.",
  clearText: "Wyczyść treść",

  suggestionsTitle: "Sugestie komórek",
  suggestionsDescription:
    "Kolejność według trafności. Zaznacz komórki, do których ma pójść zapytanie.",
  suggestionsEmpty: "Brak sugestii. Wpisz treść wniosku, żeby zobaczyć komórki.",
  suggestionsLoading: "Szukanie komórek…",
  suggestionsFailed: "Nie udało się pobrać sugestii.",
  selectAll: "Zaznacz wszystkie",
  clearSelection: "Odznacz wszystkie",
  selectedCount: (count: number) =>
    count === 1 ? "zaznaczona 1 komórka" : `zaznaczonych komórek: ${count}`,
  matchedTerms: "Dopasowane terminy",
  confidence: "Pewność",

  previewTitle: "Podgląd zapytania",
  previewDescription: "Treść aktualizuje się przy każdej zmianie zaznaczenia.",
  previewNoCase: "Wybierz sprawę z listy, żeby zobaczyć treść zapytania.",
  previewNoSelection: "Zaznacz co najmniej jedną komórkę.",
  previewLoading: "Przygotowywanie treści…",
  previewFailed: "Nie udało się przygotować treści zapytania.",
  addressees: "Adresaci",
  copy: "Kopiuj treść",
  copied: "Skopiowano treść zapytania do schowka",
  copyFailed: "Nie udało się skopiować — zaznacz treść i skopiuj ręcznie.",
  download: "Pobierz .txt",
  goToDraft: "Przejdź do odpowiedzi",
  goToDraftHint: "Otwiera generator odpowiedzi dla tej sprawy.",

  kindLabel: {
    wydzial: "wydział",
    biuro: "biuro",
    referat: "referat",
  } as Record<string, string>,
} as const;
