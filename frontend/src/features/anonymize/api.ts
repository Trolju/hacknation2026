/**
 * Hooki React Query modułu anonimizacji.
 *
 * Kontrakt: `contracts/openapi.yaml` (`/api/anonymize/*`). Typy metryk nie
 * istnieją w `src/lib/types.ts`, więc mieszkają tutaj — nie dopisujemy do
 * plików współdzielonych.
 */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Span } from "@/lib/types";

export type CategoryMetrics = {
  precision: number;
  recall: number;
  support: number;
};

export type AnonymizerMetrics = {
  precision: number;
  recall: number;
  f1: number;
  per_category: Record<string, CategoryMetrics>;
};

export type DetectInput = {
  text: string;
  categories?: string[];
};

export type ApplyInput = {
  text: string;
  spans: Span[];
  placeholder?: string;
};

export type ApplyResult = {
  text: string;
  removed_count: number;
};

/** Metryki na zbiorze oceny — precyzja, pełność, F1 i rozbicie na kategorie. */
export function useAnonymizerMetrics() {
  return useQuery({
    queryKey: ["anonymize", "metrics"],
    queryFn: () => api.get<AnonymizerMetrics>("/anonymize/evaluate"),
    staleTime: 5 * 60_000,
  });
}

/** Wykrycie danych osobowych w tekście. */
export function useDetectSpans() {
  return useMutation({
    mutationFn: (input: DetectInput) =>
      api.post<Span[]>("/anonymize/detect", input),
  });
}

/** Zastosowanie zaakceptowanych spanów — podmiana na placeholder. */
export function useApplyAnonymization() {
  return useMutation({
    mutationFn: (input: ApplyInput) =>
      api.post<ApplyResult>("/anonymize/apply", input),
  });
}
