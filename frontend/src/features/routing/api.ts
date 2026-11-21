/**
 * Warstwa danych modułu routingu wydziałowego (WS4).
 *
 * Kontrakt: `contracts/openapi.yaml` (`/api/routing/*`). Typ `GeneratedLetter`
 * nie istnieje w `src/lib/types.ts` (plik współdzielony jest zamrożony), więc
 * mieszka tutaj — tak samo jak typy metryk w module anonimizacji.
 *
 * Klucze zapytań: `["routing", "departments"]`, `["routing", "suggest", tekst]`,
 * `["routing", "inquiry", sprawa, komórki]`.
 *
 * Podgląd zapytania jest zapytaniem, nie mutacją: endpoint nic nie wysyła
 * („tylko projekt”), a klucz zależny od wyboru komórek daje podgląd, który sam
 * odświeża się przy każdej zmianie zaznaczenia.
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Department, DepartmentSuggestion } from "@/lib/types";

export type GeneratedLetter = {
  title: string;
  body: string;
  addressees: string[];
};

/** Ile sugestii pokazujemy — kontrakt dopuszcza 1–10. */
export const SUGGESTION_LIMIT = 5;

/** Najkrótszy tekst, dla którego warto pytać backend. */
export const MIN_TEXT_LENGTH = 3;

/** Taksonomia komórek organizacyjnych urzędu. */
export function useDepartments() {
  return useQuery({
    queryKey: ["routing", "departments"],
    queryFn: () => api.get<Department[]>("/routing/departments"),
    staleTime: 5 * 60_000,
  });
}

/** Sugestie komórek dla treści wniosku — odświeżają się z opóźnieniem pisania. */
export function useSuggestDepartments(text: string) {
  const trimmed = text.trim();
  return useQuery({
    queryKey: ["routing", "suggest", trimmed, SUGGESTION_LIMIT],
    queryFn: () =>
      api.post<DepartmentSuggestion[]>("/routing/suggest", {
        text: trimmed,
        k: SUGGESTION_LIMIT,
      }),
    enabled: trimmed.length >= MIN_TEXT_LENGTH,
    staleTime: 60_000,
  });
}

/** Podgląd treści zapytania dla wybranej sprawy i wybranych komórek. */
export function useInquiryPreview(caseId: string | null, departmentIds: string[]) {
  return useQuery({
    queryKey: ["routing", "inquiry", caseId, departmentIds],
    queryFn: () =>
      api.post<GeneratedLetter>("/routing/inquiry", {
        case_id: caseId,
        department_ids: departmentIds,
      }),
    enabled: Boolean(caseId) && departmentIds.length > 0,
    staleTime: 60_000,
    retry: false,
  });
}

/** Nazwa pliku z numerem sprawy — bez znaków, których nie lubią systemy plików. */
export function inquiryFileName(caseNumber: string): string {
  const safe = caseNumber.replace(/[^0-9A-Za-z._-]+/g, "-").replace(/^-+|-+$/g, "");
  return `zapytanie-${safe || "sprawa"}.txt`;
}

/** Pobranie treści jako plik `.txt` — po stronie przeglądarki, bez serwera. */
export function downloadText(fileName: string, text: string): void {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.rel = "noopener";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** Kopiowanie do schowka. `false` oznacza, że przeglądarka odmówiła dostępu. */
export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
