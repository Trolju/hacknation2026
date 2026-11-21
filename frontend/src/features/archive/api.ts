/**
 * Hooki React Query modułu archiwum.
 *
 * Kontrakt: `contracts/openapi.yaml` (`/api/archive/*`). Typ `ArchiveCase`
 * nie istnieje w `src/lib/types.ts`, więc mieszka tutaj — nie dopisujemy do
 * plików współdzielonych.
 */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { SimilarCase } from "@/lib/types";

export type ArchiveCase = {
  archive_id: string;
  case_number: string;
  subject: string;
  year: number;
  request_text: string;
  response_text: string;
  departments: string[];
};

export type SimilarInput = {
  text: string;
  k?: number;
  year_from?: number;
  exclude_case_id?: string;
};

/** Wyszukiwanie podobnych spraw — zapytanie jest mutacją, bo nie mieści się w URL. */
export function useSimilarCases() {
  return useMutation({
    mutationFn: (input: SimilarInput) =>
      api.post<SimilarCase[]>("/archive/similar", {
        text: input.text,
        k: input.k ?? 5,
        year_from: input.year_from,
        exclude_case_id: input.exclude_case_id,
      }),
  });
}

/** Pełna treść sprawy archiwalnej — wczytywana dopiero po otwarciu panelu. */
export function useArchiveCase(archiveId: string | null) {
  return useQuery({
    queryKey: ["archive", archiveId],
    queryFn: () => api.get<ArchiveCase>(`/archive/${archiveId}`),
    enabled: Boolean(archiveId),
    retry: false,
  });
}
