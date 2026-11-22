/** Teksty interfejsu modułu generatora odpowiedzi (WS5). */

import type { Citation } from "@/lib/types";

export const SOURCE_LABEL: Record<Citation["source_type"], string> = {
  statute: "Przepis",
  archive: "Archiwum",
  document: "Dokument",
  department_reply: "Odpowiedź komórki",
};

export const SOURCE_CLASS: Record<Citation["source_type"], string> = {
  statute:
    "bg-sky-50 text-sky-800 border-sky-200 dark:bg-sky-950 dark:text-sky-200 dark:border-sky-800",
  archive:
    "bg-violet-50 text-violet-800 border-violet-200 dark:bg-violet-950 dark:text-violet-200 dark:border-violet-800",
  document:
    "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800",
  department_reply:
    "bg-amber-50 text-amber-900 border-amber-200 dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800",
};

export const TEXT = {
  title: "Generator odpowiedzi",
  description:
    "Projekt odpowiedzi na wniosek o udostępnienie informacji publicznej. Każde twierdzenie ma źródło, a braki są widoczne przed wysłaniem.",
  caseLabel: "Sprawa",
  casePlaceholder: "Wybierz sprawę",
  caseEmpty: "Brak spraw do wyboru",
  generate: "Wygeneruj projekt",
  regenerate: "Wygeneruj ponownie",
  generating: "Generowanie projektu…",
  generateSuccess: "Projekt odpowiedzi gotowy",
  generateFailed: "Nie udało się wygenerować projektu",
  regenerateTitle: "Projekt już istnieje",
  regenerateDescription:
    "Nowa wersja zastąpi obecną treść. Poprzednia wersja zostanie zapisana w historii zmian.",
  regenerateConfirm: "Wygeneruj nową wersję",
  regenerateCancel: "Anuluj",
  noDraftTitle: "Brak projektu odpowiedzi",
  noDraftDescription:
    "Wybierz sprawę i wygeneruj projekt. Projekt powstanie także wtedy, gdy model językowy jest niedostępny.",
  noCaseTitle: "Wybierz sprawę",
  noCaseDescription:
    "Projekt odpowiedzi powstaje dla konkretnego wniosku. Wybierz sprawę z listy powyżej.",
  loadingDraft: "Wczytywanie projektu…",
  draftError: "Nie udało się pobrać projektu odpowiedzi",
  editorTitle: "Treść projektu",
  editorHint:
    "Nagłówki, pogrubienie i listy zachowują strukturę pisma. Zmiany zapisują się automatycznie.",
  saveIdle: "Zapisano",
  saveDirty: "Niezapisane zmiany",
  saveSaving: "Zapisywanie…",
  saveSaved: "Zapisano",
  saveError: "Nie udało się zapisać zmian",
  saveRetry: "Zapisz teraz",
  citationsTitle: "Cytowania",
  citationsEmpty: "Projekt nie powołuje żadnego źródła.",
  citationsHint: "Kliknij cytowanie, żeby przejść do miejsca w treści.",
  citationMissing: "Nie znaleziono odnośnika w treści — cytowanie podświetlone w panelu.",
  unsupportedTitle: "Twierdzenia bez źródła",
  unsupportedHint:
    "Te zdania nie mają pokrycia w źródłach. Uzupełnij je albo usuń przed wysłaniem.",
  unsupportedGoTo: "Przejdź do sekcji",
  unsupportedNoSection: "Nie znaleziono sekcji w treści.",
  degradedTitle: "Projekt z szablonu",
  degradedFallback:
    "Model językowy nie dostarczył treści do projektu — pismo powstało z szablonu.",
  exportTitle: "Eksport",
  exportDocx: "DOCX",
  exportPdf: "PDF",
  exportMarkdown: "Markdown",
  exportAnonymized: "Wersja zanonimizowana",
  exportAnonymizedHint: "Usuwa dane osobowe z treści i z listy cytowań.",
  exportSuccess: "Plik gotowy",
  exportNothingToHide: "Brak danych osobowych w projekcie",
  exportNothingToHideHint: "Plik jest identyczny z wersją bez anonimizacji.",
  exportFailed: "Nie udało się wyeksportować projektu",
  exportMissing: "Najpierw wygeneruj projekt.",
  updatedAt: "Ostatnia zmiana",
  createdAt: "Utworzono",
  toolbarUndo: "Cofnij",
  toolbarRedo: "Ponów",
  toolbarHeading2: "Nagłówek",
  toolbarHeading3: "Podnagłówek",
  toolbarBold: "Pogrubienie",
  toolbarBulletList: "Lista punktowana",
  toolbarOrderedList: "Lista numerowana",
  editorPlaceholder: "Treść projektu odpowiedzi…",
  countLabel: (count: number) => `Cytowań: ${count}`,
  unsupportedCount: (count: number) => `Do sprawdzenia: ${count}`,
} as const;
