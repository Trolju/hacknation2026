/**
 * Operacje na zaznaczeniu komórek — czyste funkcje, więc testowalne bez DOM.
 *
 * Zaznaczenie trzymamy jako listę identyfikatorów, a nie zbiór, bo kolejność
 * adresatów w zapytaniu ma znaczenie: urzędnik widzi ich numerację w podglądzie.
 */

import type { DepartmentSuggestion } from "@/lib/types";

/** Ile komórek zaznaczamy na start — dwie najlepsze sugestie. */
export const DEFAULT_SELECTION_SIZE = 2;

/** Dodaje identyfikator na koniec albo usuwa go, zachowując kolejność reszty. */
export function toggleId(ids: string[], id: string): string[] {
  return ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id];
}

/** Domyślne zaznaczenie: najlepsze sugestie, ale nie więcej niż dwie. */
export function defaultSelection(suggestions: DepartmentSuggestion[]): string[] {
  return suggestions.slice(0, DEFAULT_SELECTION_SIZE).map((item) => item.department_id);
}

/**
 * Ogranicza zaznaczenie do komórek obecnych na liście sugestii.
 *
 * Bez tego po zmianie treści w zapytaniu zostawałyby komórki, których już nie
 * ma na liście — podgląd pokazywałby adresatów, których urzędnik nie widzi.
 */
export function pruneSelection(
  ids: string[],
  suggestions: DepartmentSuggestion[],
): string[] {
  const available = new Set(suggestions.map((item) => item.department_id));
  return ids.filter((id) => available.has(id));
}

/** Czy wszystkie sugestie są już zaznaczone. */
export function isAllSelected(
  ids: string[],
  suggestions: DepartmentSuggestion[],
): boolean {
  return (
    suggestions.length > 0 &&
    suggestions.every((item) => ids.includes(item.department_id))
  );
}
