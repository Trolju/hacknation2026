/**
 * Warstwa danych modułu generatora odpowiedzi (WS5).
 *
 * Klucze zapytań: `["draft", caseId]`. Mutacje aktualizują ten sam klucz, więc
 * po zapisie i po ponownym wygenerowaniu ekran od razu widzi nową treść.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api, queryString, type ApiErrorBody } from "@/lib/api";
import type { Draft } from "@/lib/types";

import { apiErrorMessage } from "@/components/errorMessages";

export type DraftFormat = "docx" | "pdf" | "md";

export type ExportInput = {
  draftId: string;
  format: DraftFormat;
  anonymized: boolean;
};

export type ExportResult = {
  blob: Blob;
  filename: string;
};

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

const FALLBACK_NAME: Record<DraftFormat, string> = {
  docx: "odpowiedz.docx",
  pdf: "odpowiedz.pdf",
  md: "odpowiedz.md",
};

export function useDraft(caseId: string | null) {
  return useQuery({
    queryKey: ["draft", caseId],
    queryFn: () => api.get<Draft>(`/drafting/${caseId}`),
    enabled: Boolean(caseId),
    retry: false,
  });
}

export function useCreateDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (caseId: string) => api.post<Draft>("/drafting/draft", { case_id: caseId }),
    onSuccess: (draft) => {
      client.setQueryData(["draft", draft.case_id], draft);
    },
  });
}

export function useSaveDraft() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { draftId: string; body: string; title?: string }) =>
      api.patch<Draft>(`/drafting/${input.draftId}`, {
        body: input.body,
        title: input.title,
      }),
    onSuccess: (draft) => {
      client.setQueryData(["draft", draft.case_id], draft);
    },
  });
}

function parseFilename(header: string | null, format: DraftFormat): string {
  if (!header) return FALLBACK_NAME[format];
  const match = /filename="?([^";]+)"?/i.exec(header);
  return match?.[1] ?? FALLBACK_NAME[format];
}

async function fetchExport(input: ExportInput): Promise<ExportResult> {
  const query = queryString({ fmt: input.format, anonymized: input.anonymized });
  const response = await fetch(`${BASE}/drafting/${input.draftId}/export${query}`);
  if (!response.ok) {
    let body: ApiErrorBody = { code: "http_error", message: `Błąd ${response.status}` };
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      /* odpowiedź bez JSON — zostaje komunikat domyślny */
    }
    throw new ApiError(response.status, body);
  }
  return {
    blob: await response.blob(),
    filename: parseFilename(response.headers.get("Content-Disposition"), input.format),
  };
}

export function useExportDraft() {
  return useMutation({ mutationFn: fetchExport });
}

/** Zapisuje plik na dysku urzędnika — bez otwierania nowej karty. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** Komunikat błędu do pokazania w toaście — wspólne mapowanie kodów API. */
export function errorMessage(error: unknown): string {
  return apiErrorMessage(error);
}

/** Czy błąd oznacza po prostu brak projektu dla sprawy. */
export function isMissingDraft(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}
