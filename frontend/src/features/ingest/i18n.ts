/** Teksty interfejsu modułu dokumentów (WS2). */

import type { DocumentKind, DocumentStatus } from "@/features/ingest/api";

export const KIND_LABEL: Record<DocumentKind, string> = {
  wniosek: "Wniosek",
  odpowiedz_wydzialu: "Odpowiedź wydziału",
  archiwum: "Archiwum",
  ustawa: "Ustawa",
  zarzadzenie: "Zarządzenie",
  inne: "Inne",
};

export const KIND_OPTIONS: { value: DocumentKind; label: string }[] = [
  { value: "wniosek", label: KIND_LABEL.wniosek },
  { value: "odpowiedz_wydzialu", label: KIND_LABEL.odpowiedz_wydzialu },
  { value: "archiwum", label: KIND_LABEL.archiwum },
  { value: "ustawa", label: KIND_LABEL.ustawa },
  { value: "zarzadzenie", label: KIND_LABEL.zarzadzenie },
  { value: "inne", label: KIND_LABEL.inne },
];

export const STATUS_LABEL: Record<DocumentStatus, string> = {
  pending: "W kolejce",
  parsed: "Rozpoznany",
  indexed: "Zaindeksowany",
  failed: "Błąd odczytu",
};

export const STATUS_CLASS: Record<DocumentStatus, string> = {
  pending:
    "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  parsed:
    "bg-sky-50 text-sky-800 border-sky-200 dark:bg-sky-950 dark:text-sky-200 dark:border-sky-800",
  indexed:
    "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800",
  failed:
    "bg-red-100 text-red-800 border-red-200 dark:bg-red-950 dark:text-red-200 dark:border-red-800",
};

/** Odmiana rzeczownika po liczbie — polskie formy: 1, 2-4, 5+. */
function plural(count: number, one: string, few: string, many: string): string {
  if (count === 1) return one;
  const rest = count % 10;
  const tens = count % 100;
  if (rest >= 2 && rest <= 4 && (tens < 12 || tens > 14)) return few;
  return many;
}

export const TEXT = {
  title: "Dokumenty",
  description:
    "Wgrywanie wniosków, odpowiedzi wydziałów i aktów prawnych. Tekst jest rozpoznawany, dzielony na fragmenty i zapisywany w bazie wiedzy.",
  uploadTitle: "Wgraj dokument",
  uploadHint: "Przeciągnij plik tutaj albo kliknij, żeby wybrać z dysku",
  uploadFormats: "Obsługiwane formaty: PDF, DOCX, TXT, MD. Limit 10 MB.",
  uploadKind: "Rodzaj dokumentu",
  uploadCase: "Przypisz do sprawy",
  uploadCaseNone: "Bez przypisania",
  uploadTitleField: "Tytuł (opcjonalnie)",
  uploadTitlePlaceholder: "np. Wniosek o wynagrodzenia 2025",
  uploadSubmit: "Wgraj i przetwórz",
  uploadClear: "Wyczyść",
  uploadProgress: "Wysyłanie pliku",
  uploadProcessing: "Rozpoznawanie tekstu",
  uploadSuccess: "Dokument wgrany i zaindeksowany",
  uploadFailed: "Nie udało się wgrać dokumentu",
  uploadParseFailed: "Dokument zapisany, ale tekstu nie udało się odczytać",
  listTitle: "Baza wiedzy",
  filterKind: "Rodzaj",
  filterAll: "Wszystkie",
  filterSearch: "Szukaj w nazwach",
  filterSearchPlaceholder: "Nazwa pliku lub tytuł…",
  emptyTitle: "Baza wiedzy jest pusta",
  emptyDescription:
    "Wgraj pierwszy dokument — wniosek, odpowiedź wydziału albo tekst ustawy.",
  emptyFilteredTitle: "Brak dokumentów dla wybranych filtrów",
  emptyFilteredDescription: "Zmień rodzaj dokumentu albo wyczyść pole wyszukiwania.",
  columnName: "Nazwa",
  columnKind: "Rodzaj",
  columnSize: "Rozmiar",
  columnStatus: "Status",
  columnChunks: "Fragmenty",
  columnDate: "Data",
  columnActions: "Akcje",
  actionPreview: "Podgląd",
  actionReindex: "Reindeksuj",
  actionDelete: "Usuń",
  deleteTitle: "Usunąć dokument?",
  deleteDescription:
    "Dokument i jego fragmenty znikną z bazy wiedzy. Tej operacji nie można cofnąć.",
  deleteConfirm: "Usuń dokument",
  deleteCancel: "Anuluj",
  deleteSuccess: "Dokument usunięty",
  deleteFailed: "Nie udało się usunąć dokumentu",
  reindexSuccess: "Indeks odbudowany",
  reindexFailed: "Nie udało się odbudować indeksu",
  previewTitle: "Podgląd dokumentu",
  previewText: "Rozpoznany tekst",
  previewChunks: "Fragmenty",
  previewPage: "Strona",
  previewSection: "Sekcja",
  previewNoText: "Brak rozpoznanego tekstu.",
  previewEmptyPage: "Ta strona nie zawiera tekstu.",
  previewNoChunks: "Brak fragmentów — dokument nie został zaindeksowany.",
  previewError: "Nie udało się odczytać tekstu dokumentu",
  previewClose: "Zamknij",
  previewLoading: "Wczytywanie dokumentu…",
  errorTitle: "Nie udało się pobrać listy dokumentów",
  retry: "Spróbuj ponownie",
  refresh: "Odśwież",
  countLabel: (count: number) => `Dokumentów: ${count}`,
  chunksLabel: (count: number) =>
    `${count} ${plural(count, "fragment", "fragmenty", "fragmentów")}`,
  pagesLabel: (count: number) => `${count} ${plural(count, "strona", "strony", "stron")}`,
} as const;
