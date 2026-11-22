/**
 * Warstwa danych modułu dokumentów (WS2).
 *
 * Typy lokalne uzupełniają `src/lib/types.ts` o szczegóły dokumentu i fragmentu
 * (plik współdzielony jest zamrożony). Klucze zapytań: `["documents", filtry]`,
 * `["document", id]`, `["document", id, "chunks"]`.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api, authHeaders, queryString, type ApiErrorBody } from "@/lib/api";
import type { Document } from "@/lib/types";

import { apiErrorMessage } from "@/components/errorMessages";

export type DocumentKind =
  | "wniosek"
  | "odpowiedz_wydzialu"
  | "archiwum"
  | "ustawa"
  | "zarzadzenie"
  | "inne";

export type DocumentStatus = Document["status"];

export type DocumentDetail = Document & {
  text: string;
  page_count: number;
};

export type DocumentChunk = {
  id: string;
  document_id: string;
  index: number;
  text: string;
  page: number | null;
  section: string | null;
};

export type DocumentFilters = {
  kind?: DocumentKind;
  caseId?: string;
};

export type UploadInput = {
  file: File;
  kind: DocumentKind;
  caseId?: string;
  title?: string;
  onProgress?: (percent: number) => void;
};

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

function toErrorBody(payload: unknown, status: number): ApiErrorBody {
  if (payload && typeof payload === "object") {
    const candidate = payload as Partial<ApiErrorBody>;
    if (typeof candidate.message === "string") {
      return {
        code: typeof candidate.code === "string" ? candidate.code : "http_error",
        message: candidate.message,
        details: candidate.details,
      };
    }
  }
  return { code: "http_error", message: `Błąd ${status}` };
}

/**
 * Wgranie pliku przez XHR — tylko tak da się pokazać postęp wysyłania.
 * Błąd backendu ma kształt `{code, message, details}` i trafia do `ApiError`.
 */
function uploadDocument(input: UploadInput): Promise<Document> {
  return new Promise<Document>((resolve, reject) => {
    const form = new FormData();
    form.append("file", input.file);
    form.append("kind", input.kind);
    if (input.caseId) form.append("case_id", input.caseId);
    if (input.title) form.append("title", input.title);

    const request = new XMLHttpRequest();
    request.open("POST", `${BASE}/documents`);
    // XHR omija wspólny klient z `lib/api.ts`, więc nagłówki bierzemy z `authHeaders`.
    for (const [name, value] of authHeaders()) request.setRequestHeader(name, value);
    request.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) {
        input.onProgress?.(Math.round((event.loaded / event.total) * 100));
      }
    };
    request.onload = () => {
      const payload = parseJson(request.responseText);
      if (request.status >= 200 && request.status < 300) {
        resolve(payload as Document);
        return;
      }
      reject(new ApiError(request.status, toErrorBody(payload, request.status)));
    };
    request.onerror = () => {
      reject(
        new ApiError(0, {
          code: "network_error",
          message: "Nie udało się połączyć z serwerem. Sprawdź, czy backend działa.",
        }),
      );
    };
    request.send(form);
  });
}

export function useDocuments(filters: DocumentFilters = {}) {
  return useQuery({
    queryKey: ["documents", filters],
    queryFn: () =>
      api.get<Document[]>(
        `/documents${queryString({ kind: filters.kind, case_id: filters.caseId })}`,
      ),
  });
}

export function useDocument(documentId: string | null) {
  return useQuery({
    queryKey: ["document", documentId],
    queryFn: () => api.get<DocumentDetail>(`/documents/${documentId}`),
    enabled: Boolean(documentId),
  });
}

export function useDocumentChunks(documentId: string | null) {
  return useQuery({
    queryKey: ["document", documentId, "chunks"],
    queryFn: () => api.get<DocumentChunk[]>(`/documents/${documentId}/chunks`),
    enabled: Boolean(documentId),
  });
}

export function useUploadDocument() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => api.delete<void>(`/documents/${documentId}`),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useReindexDocument() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => api.post<Document>(`/documents/${documentId}/reindex`),
    onSuccess: (document) => {
      void client.invalidateQueries({ queryKey: ["documents"] });
      void client.invalidateQueries({ queryKey: ["document", document.id] });
    },
  });
}

/** Rozmiar pliku w jednostkach czytelnych dla urzędnika. */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} kB`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}

/**
 * Dzieli rozpoznany tekst na strony. Backend rozdziela strony znakiem form feed
 * i dodaje końcowy separator, więc ostatni pusty fragment odrzucamy — pustej
 * strony w środku dokumentu nie gubimy, bo przesunęłaby numerację.
 */
export function splitPages(text: string): string[] {
  const parts = text.split("\f");
  if (parts.length > 0 && parts[parts.length - 1].trim() === "") {
    parts.pop();
  }
  return parts.map((page) => page.trim());
}

/** Komunikat błędu do pokazania w toaście — wspólne mapowanie kodów API. */
export function errorMessage(error: unknown): string {
  return apiErrorMessage(error);
}
