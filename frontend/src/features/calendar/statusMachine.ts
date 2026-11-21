/**
 * Lustro maszyny stanów z `backend/app/modules/cases/service.py`.
 *
 * Reguły (contracts/domain.md §2): naprzód o jeden krok, `kwerenda` opcjonalna,
 * cofnięcie o krok wymaga notatki, wyjście ze stanu końcowego wymaga notatki.
 */

import type { CaseStatus } from "@/lib/types";

export const STATUS_ORDER: CaseStatus[] = [
  "nowy",
  "zapytania_wyslane",
  "kwerenda",
  "przygotowana_odpowiedz",
  "odpowiedz_wyslana",
];

export type TransitionKind = "forward" | "backward" | "skip";

export type TransitionOption = {
  to: CaseStatus;
  kind: TransitionKind;
  requiresNote: boolean;
};

export function requiresNote(current: CaseStatus, to: CaseStatus): boolean {
  if (current === to) return false;
  if (current === "odpowiedz_wyslana") return true;
  return STATUS_ORDER.indexOf(to) === STATUS_ORDER.indexOf(current) - 1;
}

/** Przejścia dostępne z danego stanu — dokładnie te, które przyjmie backend. */
export function transitionOptions(current: CaseStatus): TransitionOption[] {
  const index = STATUS_ORDER.indexOf(current);
  const options: TransitionOption[] = [];

  const forward = STATUS_ORDER[index + 1];
  if (forward) {
    options.push({ to: forward, kind: "forward", requiresNote: false });
  }
  if (current === "zapytania_wyslane") {
    options.push({
      to: "przygotowana_odpowiedz",
      kind: "skip",
      requiresNote: false,
    });
  }
  const backward = STATUS_ORDER[index - 1];
  if (backward) {
    options.push({ to: backward, kind: "backward", requiresNote: true });
  }
  return options;
}
